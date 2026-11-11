"""MKT-RSS publishes one current WordPress-owner-approved version.

No text generation, no change of author, no self-approval and no credentials
outside the existing executor. Default validates only; --execute is explicit.
"""
import argparse
import hashlib
import json
import os
import re
import uuid
from html.parser import HTMLParser

from tools.wp_identity_preflight import check_identity
from mkt_flow_p0.editorial_transport import SITE
from mkt_flow_p0.editorial_broker_transport import _get_json, publish_via_broker, BrokerBlocked
from mkt_flow_p0.editorial_trace_gate import REQUIRED
import requests


class PublicSEO(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles, self.descriptions, self.canonicals = [], [], []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title':
            self.titles.append(''); self.in_title = True
        if tag == 'meta' and a.get('name','').lower() == 'description':
            self.descriptions.append(a.get('content',''))
        if tag == 'link' and 'canonical' in a.get('rel','').lower().split():
            self.canonicals.append(a.get('href',''))

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False

    def handle_data(self, data):
        if self.in_title: self.titles[-1] += data


def verify_public_seo(payload, version, *, http=requests):
    seo = payload.get('seo', {})
    slug = payload.get('slug')
    if not isinstance(slug,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):
        return False
    canonical = SITE + '/' + slug + '/'
    if seo.get('canonical') != canonical: return False
    try:
        # New unauthenticated request: no Application Password or article text.
        reply = http.get(canonical + '?conexo_verify=' + version[:16], timeout=20,
                         allow_redirects=False, headers={'User-Agent':'MKT-RSS-Public-SEO-Verify/1'})
        if reply.status_code != 200 or len(reply.content) > 2 * 1024 * 1024: return False
        page = PublicSEO(); page.feed(reply.text)
        return (len(page.titles)==1 and page.titles[0].strip()==seo.get('title')
                and page.descriptions==[seo.get('description')]
                and page.canonicals==[canonical])
    except (requests.RequestException, ValueError):
        return False


def owner_trace(packet):
    payload = packet.get('payload', {})
    checks = payload.get('checks')
    if (packet.get('schema') != 'conexo-owner-release/1' or payload.get('owner_id') != 3
            or payload.get('review_mode') != 'owner' or not isinstance(checks, dict)
            or not isinstance(payload.get('content'), str)
            or not re.fullmatch(r'[a-f0-9]{64}', packet.get('version_sha256', ''))):
        raise BrokerBlocked('OWNER_PACKET_INVALID')
    mapped = {'source_review':['fontes'], 'research':['fontes','alegacoes'],
              'factual_review':['alegacoes'], 'style_review':['revisao_substantiva'],
              'seo_review':['seo'], 'image_review':['capa','licenca_imagem'],
              'internal_links':['links_internos'], 'render_review':['visual_390','visual_1440'],
              'editorial_approval':['versao','revisao_substantiva']}
    digest = hashlib.sha256(payload['content'].encode('utf-8')).hexdigest()
    events = []
    for stage in REQUIRED:
        if stage == 'generation':
            # This article already exists. PASS observes import of exact bytes;
            # it does not assert an LLM generation/model execution happened.
            module = 'mkt-rss.existing-wp-draft-import'
            evidence = 'existing-wp-content-sha256:' + digest
        else:
            for check in mapped[stage]:
                item = checks.get(check)
                if (not isinstance(item, dict) or item.get('estado') != 'VERIFICADO'
                        or not isinstance(item.get('evidencia'), list) or not item['evidencia']
                        or not all(isinstance(v,str) and len(v.strip()) >= 8 for v in item['evidencia'])):
                    raise BrokerBlocked('OWNER_CHECK_MISSING')
            module = 'wordpress.owner-version-review'
            evidence = 'owner-approval:' + payload['approval_reference'] + ':' + stage
        events.append({'stage':stage, 'module_id':module, 'status':'PASS', 'evidence_ref':evidence})
    return {'schema':'conexo-editorial-executor-events/1', 'run_id':str(uuid.uuid4()),
            'article_id':payload['article_id'], 'post_id':payload['wordpress']['post_id'],
            'content_sha256':digest, 'publication_authorized':False, 'events':events}


def release(post_id, version, execute=False, *, session=requests, identity=check_identity):
    if identity(os.environ) != 'PASS':
        raise BrokerBlocked('MKT_SERVICE_IDENTITY_NOT_VERIFIED')
    if type(post_id) is not int or post_id < 1 or not re.fullmatch(r'[a-f0-9]{64}', version):
        raise BrokerBlocked('EXPECTED_VERSION_INVALID')
    auth = (os.environ['WP_USER'], os.environ['WP_APP_PASSWORD'])
    packet = _get_json(session, f'{SITE}/wp-json/conexo/v1/editorial/owner-release/{post_id}', auth, 15)
    payload = packet.get('payload', {})
    if (packet.get('version_sha256') != version or not isinstance(payload,dict)
            or payload.get('wordpress', {}).get('post_id') != post_id):
        raise BrokerBlocked('EXPECTED_OWNER_VERSION_MISMATCH')
    trace = owner_trace(packet)
    if not execute:
        return {'validated':True,'post_id':post_id,'version_sha256':version,'write':False}
    result = publish_via_broker(packet, core_root='.', wp_url=SITE, wp_user=auth[0], wp_password=auth[1],
        trace_run_id=trace['run_id'], trace_packet=trace, intent='publish',
        publication_reference=payload['approval_reference'], session=session,
        require_signed_seo=True, owner_release=True)
    if 'erro' not in result:
        result['seo_public_verified'] = verify_public_seo(payload,version)
        if not result['seo_public_verified']:
            result.update(erro='PUBLICATION_CONFIRMED_PUBLIC_SEO_INSPECTION_PENDING', retry_automatic=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--post-id', required=True, type=int)
    parser.add_argument('--version', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    try:
        result = release(args.post_id, args.version, args.execute)
    except BrokerBlocked as exc:
        result = {'erro':str(exc),'retry_automatic':False}
    except (ValueError, KeyError, TypeError):
        # Stable code only; never exception repr, unpublished text or secrets.
        result = {'erro':'OWNER_RELEASE_BLOCKED_INSPECT_NO_RETRY','retry_automatic':False}
    text = json.dumps(result, ensure_ascii=False, sort_keys=True)
    print(text)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as out:
            out.write('MKT-RSS owner-approved release\n\n```json\n'+text+'\n```\n')
    return 1 if 'erro' in result else 0


if __name__ == '__main__':
    raise SystemExit(main())
