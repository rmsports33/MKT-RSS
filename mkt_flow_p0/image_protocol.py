"""Image selection and preparation; poor-fit candidates route to an AI generation request."""
import copy
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

CATALOG = Path(__file__).resolve().parents[1] / 'data/licensed-image-catalog.json'
REGISTRY = Path(__file__).resolve().parents[1] / 'data/image-rights-registry.json'


def load_registry():
    """Licenças e domínios aceitos, lidos de um único arquivo de regras."""
    return json.loads(REGISTRY.read_text(encoding='utf-8'))


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
    registry = load_registry()
    license_rule = registry['licenses'].get(resource['license'])
    if (license_rule is None or resource['license_url'] != license_rule['url']
            or resource.get('rights_review') != 'DOCUMENTED_SOURCE_CHECK'):
        raise ValueError('IMAGE_LICENSE_NOT_DOCUMENTED')
    for key in ('source_page','image_url','license_url'):
        p=urlsplit(resource[key])
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.port is not None:
            raise ValueError('IMAGE_URL_INVALID')
    # A página de origem precisa estar na lista branca; o crédito sai daqui, não de texto digitado.
    host=(urlsplit(resource['source_page']).hostname or '').lower().rstrip('.')
    if not any(host==domain or host.endswith('.'+domain) for domain in registry['sources']):
        raise ValueError('IMAGE_SOURCE_NOT_ALLOWED')
    return copy.deepcopy(resource)


def _generation_request(title, reason, candidate=None, artigo=None):
    """Return an explicit request for the available image-generation tool.

    When the full article is supplied, the prompt is derived from the matter
    itself (see image_prompt_from_article) instead of a generic keyword prompt.
    """
    prompt_info = None
    if isinstance(artigo, dict):
        try:
            from mkt_flow_p0.image_prompt_from_article import construir_prompt_imagem
            prompt_info = construir_prompt_imagem({**artigo, 'titulo': artigo.get('titulo') or title})
        except (ValueError, TypeError):
            prompt_info = None

    if prompt_info:
        prompt = prompt_info['prompt']
        constraints = prompt_info['constraints']
        base = prompt_info['base_do_artigo']
    else:
        prompt = ('Create a relevant editorial image for the article "'+title+'". '
                  'Match the article language, device context, and subject. '
                  'Do not use a merely keyword-matched but visually misleading image. '
                  'Avoid logos, fake screenshots, and unsupported UI details.')
        constraints = ['relevant_to_article','no_misleading_interface','no_logos']
        base = {'titulo': title, 'subtitulo': '', 'temas_detectados': []}

    return {
        'status':'AI_GENERATION_REQUIRED',
        'next_step':'GENERATE_RELEVANT_IMAGE',
        'reason':reason,
        'rejected_candidate':candidate,
        'generation_request':{
            'schema':'conexo-image-generation-request/1',
            'article_title':title,
            'prompt':prompt,
            'base_do_artigo':base,
            'constraints':constraints,
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


def plan_image(title, *, offline=True, content_fit=None, used_image_identifiers=None, artigo=None):
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
                return _generation_request(title,'FREE_CANDIDATE_NOT_CONGRUENT',resource['id'],artigo)
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
                                   [item.get('pagina_origem') or item.get('page_url') or item.get('url') for item in candidates],artigo)
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
                               if duplicate_sources or used else 'NO_SUITABLE_FREE_CANDIDATE',artigo)


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
    """Use the existing Pillow cover pipeline for licensed or generated artwork.

    A marca d'água ConexoTech é aplicada ANTES dos recortes, para que desktop e
    mobile a contenham. É Own-brand: não conflita com a regra que proíbe marca
    de terceiros (`PASS_NO_THIRD_PARTY_BRANDING`).
    """
    from mkt_flow_p0.image_handler import processar_capa
    from mkt_flow_p0.image_watermark import aplicar_marca
    from PIL import Image
    import io
    import tempfile
    resource=validate_resource(resource)
    with Image.open(io.BytesIO(image_bytes)) as image:
        if image.width<1440 or image.height<810:raise ValueError('IMAGE_RESOLUTION_TOO_SMALL')
        if image.width*image.height>40_000_000:raise ValueError('IMAGE_PIXEL_LIMIT')
    # Aplica selo próprio em arquivo temporário; preserve os bytes originais.
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/'original.jpg'; dst=Path(tmp)/'marcada.jpg'
        src.write_bytes(image_bytes)
        marca=aplicar_marca(src,dst)
        marked_bytes=dst.read_bytes()
    assets={}
    for name,width,height in (('desktop',1440,810),('mobile',390,219)):
        result=processar_capa(marked_bytes,largura=width,altura=height)
        if 'erro' in result:raise ValueError('IMAGE_PROCESSING_FAILED')
        assets[name]={'bytes':result['bytes'],'width':width,'height':height,
                      'sha256':hashlib.sha256(result['bytes']).hexdigest(),'mime_type':'image/jpeg'}
    return {'resource':resource,'original_sha256':hashlib.sha256(image_bytes).hexdigest(),
            'watermark':{k:v for k,v in marca.items() if k!='destino'},'assets':assets}


def validate_prepared_manifest(manifest, *, base_dir):
    resource=validate_resource(manifest['resource'])
    if manifest.get('visual_review')!='ASSISTED_VISUAL_CHECK_COMPLETED':raise ValueError('IMAGE_VISUAL_REVIEW_PENDING')
    if manifest.get('content_fit_review')!='PASS':raise ValueError('IMAGE_CONTENT_FIT_NOT_APPROVED')
    # A marca de um veículo de origem não comprova licença nem adequação editorial.
    # Exigir inspeção explícita da imagem FINAL, nos recortes desktop e móvel.
    # Ausência de laudo ou qualquer marca suspeita mantém a entrega bloqueada.
    if manifest.get('third_party_branding_review') != 'PASS_NO_THIRD_PARTY_BRANDING':
        raise ValueError('IMAGE_THIRD_PARTY_BRANDING_REVIEW_PENDING')
    if manifest.get('visible_third_party_branding') is not False:
        raise ValueError('IMAGE_THIRD_PARTY_BRANDING_REJECTED')
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
        source=resource.get('source_name')
        if not source:
            host=(urlsplit(resource['source_page']).hostname or '').lower().rstrip('.')
            source=next((name for domain,name in load_registry()['sources'].items()
                         if host==domain or host.endswith('.'+domain)), 'Fonte')
        attribution=('Foto: <a href="'+e(resource['source_page'])+'">'+e(resource['author'])+
                     '</a> / '+e(source)+'. <a href="'+e(resource['license_url'])+'">'+e(resource['license'])+'</a>.')
    return '<figure>'+picture+'<figcaption>'+e(resource['caption'])+' '+attribution+'</figcaption></figure>'
