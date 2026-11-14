"""Image selection and preparation; poor-fit candidates route to an AI generation request."""
import copy
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

CATALOG = Path(__file__).resolve().parents[1] / 'data/licensed-image-catalog.json'
LICENSES = {'CC0-1.0': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'CC-BY-4.0': 'https://creativecommons.org/licenses/by/4.0/',
            'CC-BY-SA-4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'Unsplash License': 'https://unsplash.com/license'}


def validate_resource(resource):
    if not isinstance(resource, dict):
        raise ValueError('IMAGE_RESOURCE_INVALID')
    if resource.get('source_type') == 'ai_generated':
        for key in ('id', 'generated_by', 'generated_at', 'prompt', 'alt', 'caption', 'credit'):
            if not isinstance(resource.get(key), str) or not resource[key].strip():
                raise ValueError('IMAGE_PROVENANCE_INCOMPLETE')
        if resource.get('content_fit_review') != 'PASS':
            raise ValueError('IMAGE_CONTENT_FIT_NOT_APPROVED')
        return copy.deepcopy(resource)
    for key in ('id','source_page','image_url','author','license','license_url','checked_at','alt','caption','credit'):
        if not isinstance(resource.get(key),str) or not resource[key].strip():
            raise ValueError('IMAGE_PROVENANCE_INCOMPLETE')
    if (resource['license'] not in LICENSES or resource['license_url'] != LICENSES[resource['license']]
            or resource.get('rights_review') != 'DOCUMENTED_SOURCE_CHECK'):
        raise ValueError('IMAGE_LICENSE_NOT_DOCUMENTED')
    for key in ('source_page','image_url','license_url'):
        p=urlsplit(resource[key])
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.port is not None:
            raise ValueError('IMAGE_URL_INVALID')
    return copy.deepcopy(resource)


def _generation_request(title, reason, candidate=None):
    """Return an explicit request for the available image-generation tool."""
    return {
        'status':'AI_GENERATION_REQUIRED',
        'next_step':'GENERATE_RELEVANT_IMAGE',
        'reason':reason,
        'rejected_candidate':candidate,
        'generation_request':{
            'schema':'conexo-image-generation-request/1',
            'article_title':title,
            'prompt':('Create a relevant editorial image for the article "'+title+'". '
                      'Match the article language, device context, and subject. '
                      'Do not use a merely keyword-matched but visually misleading image. '
                      'Avoid logos, fake screenshots, and unsupported UI details.'),
            'constraints':['relevant_to_article','no_misleading_interface','no_logos'],
        },
        'network_called':False,'ai_called':False,'wordpress_written':False,
    }


def _used_image_keys(used_image_identifiers):
    """IDs and original URLs already reserved by this editorial batch."""
    if used_image_identifiers is None:
        return set()
    if not isinstance(used_image_identifiers, (set, frozenset, list, tuple)):
        raise ValueError('IMAGE_BATCH_USED_INVALID')
    if any(not isinstance(v, str) or not v.strip() for v in used_image_identifiers):
        raise ValueError('IMAGE_BATCH_USED_INVALID')
    return set(used_image_identifiers)


def reserve_image_candidate(plan, used_image_identifiers):
    """Reserve a catalog image for a single article; never imply WP upload."""
    if not isinstance(used_image_identifiers, set):
        raise ValueError('IMAGE_BATCH_USED_INVALID')
    resource = plan.get('resource') if isinstance(plan, dict) else None
    if not isinstance(resource, dict) or plan.get('status') != 'CANDIDATE_LICENSE_DOCUMENTED':
        return False
    resource = validate_resource(resource)
    used_image_identifiers.update(
        v for v in (resource.get('id'), resource.get('image_url'), resource.get('source_page'))
        if isinstance(v, str) and v
    )
    return True


def plan_image(title, *, offline=True, content_fit=None, used_image_identifiers=None):
    """Check free/licensed sources first; an incongruent candidate requires AI generation.

    A keyword match is only a candidate. The caller must pass content_fit='PASS'
    after visual/editorial review before accepting it. Pass 'INCONGRUENT' to
    route directly to the generation tool. The module emits a request because
    GitHub Actions cannot invoke ChatGPT's built-in image generator.
    """
    if content_fit not in (None, 'PASS', 'INCONGRUENT'):
        raise ValueError('IMAGE_CONTENT_FIT_INVALID')
    used=_used_image_keys(used_image_identifiers)
    catalog=json.loads(CATALOG.read_text(encoding='utf-8'))
    duplicate_sources=[]
    for entry in catalog:
        if all(term.casefold() in title.casefold() for term in entry.get('match_all',[])):
            resource=validate_resource(entry)
            if used.intersection({resource['id'], resource['image_url'], resource['source_page']}):
                duplicate_sources.append(resource['id'])
                continue
            if content_fit == 'INCONGRUENT':
                return _generation_request(title,'FREE_CANDIDATE_NOT_CONGRUENT',resource['id'])
            return {'status':'CANDIDATE_LICENSE_DOCUMENTED',
                    'resource':resource,
                    'content_fit_review':'PASS' if content_fit == 'PASS' else 'PENDING',
                    'next_step':'PREPARE_IMAGE' if content_fit == 'PASS' else 'REVIEW_CONTENT_FIT',
                    'network_called':False,'ai_called':False,'wordpress_written':False}
    if offline:
        return {'status':'RESEARCH_REQUIRED_OFFLINE','next_step':'FREE_STOCK_RESEARCH',
                'reason':'BATCH_COVER_ALREADY_RESERVED' if duplicate_sources else 'NO_CATALOG_MATCH',
                'rejected_duplicate_ids':duplicate_sources,
                'network_called':False,'ai_called':False,'wordpress_written':False}
    try:
        from mkt_flow_p0.image_handler import buscar_fallback
        found=buscar_fallback(title,timeout=8)
    except ImportError:
        return {'status':'RESEARCH_DEPENDENCY_UNAVAILABLE','next_step':'INSTALL_FREE_REQUESTS_OR_SUPPLY_LICENSED_MANIFEST',
                'network_called':False,'ai_called':False,'wordpress_written':False}
    candidates=[
        item for item in (found.get('candidatos') or [])
        if not any(item.get(key) in used for key in ('url','pagina_origem','page_url')
                   if isinstance(item.get(key),str))
    ]
    if content_fit == 'INCONGRUENT':
        return _generation_request(title,'FREE_CANDIDATES_NOT_CONGRUENT',
                                   [item.get('pagina_origem') or item.get('page_url') or item.get('url') for item in candidates])
    if candidates and content_fit == 'PASS':
        return {'status':'CANDIDATES_REQUIRE_LICENSE_REVIEW',
                'research':found,'content_fit_review':'PASS',
                'next_step':'VALIDATE_LICENSE_AND_PREPARE','network_called':True,
                'ai_called':False,'wordpress_written':False}
    if candidates:
        return {'status':'CANDIDATES_REQUIRE_CONTENT_FIT_REVIEW',
                'research':found,'content_fit_review':'PENDING',
                'next_step':'REVIEW_CONTENT_FIT','network_called':True,
                'ai_called':False,'wordpress_written':False}
    if found.get('proxima_etapa') == 'PESQUISA_BANCO_PENDENTE':
        # Free-stock access was unavailable; do not claim a failed search justifies AI.
        return {'status':'FREE_STOCK_RESEARCH_PENDING','next_step':'FREE_STOCK_RESEARCH',
                'network_called':True,'ai_called':False,'wordpress_written':False}
    return _generation_request(title,'NO_DISTINCT_FREE_CANDIDATE'
                               if duplicate_sources or used else 'NO_SUITABLE_FREE_CANDIDATE')


def plan_image_batch(titles, *, offline=True, content_fit=None):
    """Plan distinct editorial covers, licensed stock before an AI request.

    Planning never creates images, validates unknown media rights or writes WP.
    """
    if not isinstance(titles, (list, tuple)) or not all(
        isinstance(title, str) and title.strip() for title in titles
    ):
        raise ValueError('IMAGE_BATCH_TITLES_INVALID')
    used=set()
    plans=[]
    for title in titles:
        plan=plan_image(title, offline=offline, content_fit=content_fit,
                        used_image_identifiers=used)
        reserve_image_candidate(plan,used)
        plans.append(plan)
    return {'schema':'conexo-image-batch-plan/1','plans':plans,
            'reserved_image_keys':sorted(used),'wordpress_written':False,
            'ai_called':False}


def prepare_assets(resource, image_bytes):
    """Use the existing Pillow cover pipeline for licensed or generated artwork."""
    from mkt_flow_p0.image_handler import processar_capa
    from PIL import Image
    import io
    resource=validate_resource(resource)
    with Image.open(io.BytesIO(image_bytes)) as image:
        if image.width<1440 or image.height<810:raise ValueError('IMAGE_RESOLUTION_TOO_SMALL')
        if image.width*image.height>40_000_000:raise ValueError('IMAGE_PIXEL_LIMIT')
    assets={}
    for name,width,height in (('desktop',1440,810),('mobile',390,219)):
        result=processar_capa(image_bytes,largura=width,altura=height)
        if 'erro' in result:raise ValueError('IMAGE_PROCESSING_FAILED')
        assets[name]={'bytes':result['bytes'],'width':width,'height':height,
                      'sha256':hashlib.sha256(result['bytes']).hexdigest(),'mime_type':'image/jpeg'}
    return {'resource':resource,'original_sha256':hashlib.sha256(image_bytes).hexdigest(),'assets':assets}


def validate_prepared_manifest(manifest, *, base_dir):
    resource=validate_resource(manifest['resource'])
    if manifest.get('visual_review')!='ASSISTED_VISUAL_CHECK_COMPLETED':raise ValueError('IMAGE_VISUAL_REVIEW_PENDING')
    if manifest.get('content_fit_review')!='PASS':raise ValueError('IMAGE_CONTENT_FIT_NOT_APPROVED')
    base=Path(base_dir).resolve()
    for name in ('desktop','mobile'):
        item=manifest['assets'][name];p=(base/item['path']).resolve()
        if not p.is_relative_to(base) or not p.is_file() or p.stat().st_size>8*1024*1024:raise ValueError('IMAGE_ASSET_INVALID')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('IMAGE_ASSET_HASH_MISMATCH')
        from PIL import Image
        with Image.open(p) as image:
            expected=(1440,810) if name=='desktop' else (390,219)
            if image.size!=expected or (item['width'],item['height'])!=expected:raise ValueError('IMAGE_DIMENSIONS_MISMATCH')
    return resource


def image_figure(resource, desktop, mobile=None):
    e=lambda text:html.escape(str(text),quote=True)
    src=e(desktop);alt=e(resource['alt'])
    picture=('<picture>'+('<source media="(max-width: 600px)" srcset="'+e(mobile)+'">' if mobile else '')+
             '<img src="'+src+'" alt="'+alt+'" width="1440" height="810" style="max-width:100%;height:auto" decoding="async"></picture>')
    if resource.get('source_type') == 'ai_generated':
        attribution=e(resource['credit'])
    else:
        provider = 'Unsplash' if resource.get('license') == 'Unsplash License' else 'Wikimedia Commons'
        attribution=('Foto: <a href="'+e(resource['source_page'])+'">'+e(resource['author'])+
                     '</a> / '+provider+'. <a href="'+e(resource['license_url'])+'">'+e(resource['license'])+'</a>.')
    caption = resource['caption']
    # Legacy manifests already had a full photo credit in caption. Do not
    # duplicate the same author/provider in the rendered HTML.
    already_credited = (resource.get('source_type') != 'ai_generated'
                        and resource.get('author', '').casefold() in caption.casefold()
                        and (('unsplash' in caption.casefold() and resource.get('license') == 'Unsplash License')
                             or ('wikimedia' in caption.casefold())))
    credit_suffix = '' if already_credited else ' ' + attribution
    return '<figure>'+picture+'<figcaption>'+e(caption)+credit_suffix+'</figcaption></figure>'
