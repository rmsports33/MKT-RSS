"""Always-evaluated image protocol; no AI dependency or automatic WP writes."""
import copy
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

CATALOG = Path(__file__).resolve().parents[1] / 'data/licensed-image-catalog.json'
LICENSES = {'CC0-1.0': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'CC-BY-4.0': 'https://creativecommons.org/licenses/by/4.0/',
            'CC-BY-SA-4.0': 'https://creativecommons.org/licenses/by-sa/4.0/'}


def validate_resource(resource):
    if not isinstance(resource, dict):raise ValueError('IMAGE_RESOURCE_INVALID')
    for key in ('id','source_page','image_url','author','license','license_url','checked_at','alt','caption','credit'):
        if not isinstance(resource.get(key),str) or not resource[key].strip():raise ValueError('IMAGE_PROVENANCE_INCOMPLETE')
    if (resource['license'] not in LICENSES or resource['license_url'] != LICENSES[resource['license']]
            or resource.get('rights_review') != 'DOCUMENTED_SOURCE_CHECK'):
        raise ValueError('IMAGE_LICENSE_NOT_DOCUMENTED')
    for key in ('source_page','image_url','license_url'):
        p=urlsplit(resource[key])
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.port is not None:
            raise ValueError('IMAGE_URL_INVALID')
    return copy.deepcopy(resource)


def plan_image(title, *, offline=True):
    """Protocol runs even offline/handoff-only; missing assets remain explicit."""
    catalog=json.loads(CATALOG.read_text(encoding='utf-8'))
    for entry in catalog:
        if all(term.casefold() in title.casefold() for term in entry.get('match_all',[])):
            resource=validate_resource(entry)
            return {'status':'CANDIDATE_LICENSE_DOCUMENTED','resource':resource,
                    'next_step':'PREPARE_AND_REVIEW_1440_390','network_called':False,
                    'ai_called':False,'wordpress_written':False}
    if offline:
        return {'status':'RESEARCH_REQUIRED_OFFLINE','next_step':'FREE_STOCK_RESEARCH',
                'network_called':False,'ai_called':False,'wordpress_written':False}
    try:
        from mkt_flow_p0.image_handler import buscar_fallback
        found=buscar_fallback(title,timeout=8)
    except ImportError:
        return {'status':'RESEARCH_DEPENDENCY_UNAVAILABLE','next_step':'INSTALL_FREE_REQUESTS_OR_SUPPLY_LICENSED_MANIFEST',
                'network_called':False,'ai_called':False,'wordpress_written':False}
    return {'status':'CANDIDATES_REQUIRE_LICENSE_REVIEW' if found.get('candidatos') else 'FREE_RESEARCH_UNAVAILABLE',
            'research':found,'network_called':True,'ai_called':False,'wordpress_written':False}


def prepare_assets(resource, image_bytes):
    """Use the existing Pillow cover pipeline. No fictitious UI/screenshots."""
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
    return '<figure>'+picture+'<figcaption>'+e(resource['caption'])+' Foto: <a href="'+e(resource['source_page'])+'">'+e(resource['author'])+'</a> / Wikimedia Commons. <a href="'+e(resource['license_url'])+'">'+e(resource['license'])+'</a>.</figcaption></figure>'
