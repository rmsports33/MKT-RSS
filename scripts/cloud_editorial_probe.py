"""Bounded real cloud probes. No AI, queue mutation, article bodies or WordPress."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

HOST = 'mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io'


def packet_for(run):
    from mkt_flow_p0.editorial_trace import make_trace
    if not re.fullmatch(r'[0-9]{1,24}-[0-9]{1,6}', run):
        raise ValueError('INVALID_PROBE_RUN_ID')
    packet = make_trace('https://example.org/conexo-cloud-persistence-probe',
                        'metadata-only-persistence-probe/1:' + run)
    packet['run_id'] = 'cloud-probe-' + run
    return packet


def persistence(mode, run):
    # Stricter caller guard prevents alternate hosts, paths, credentials or ports.
    if (os.getenv('TURSO_DATABASE_URL') != 'libsql://' + HOST
            or os.getenv('CONEXO_TRACE_TURSO_ALLOWED_HOST') != HOST
            or not os.getenv('TURSO_AUTH_TOKEN', '').strip()):
        raise ValueError('BLOCKED_HOMOLOG_CONFIGURATION')
    from mkt_flow_p0.editorial_trace_turso import save_turso_trace, get_turso_trace
    packet = packet_for(run)
    if mode == 'write':
        result = save_turso_trace(packet)
        if not result.get('ok'):
            raise ValueError(result.get('reason', 'TRACE_WRITE_FAILED'))
    result = get_turso_trace(packet['run_id'])
    if not result.get('ok'):
        raise ValueError(result.get('reason', 'TRACE_READ_FAILED'))
    if result['trace'] != packet:
        raise ValueError('TRACE_READBACK_MISMATCH')
    return {'probe': 'homolog-metadata-persistence', 'mode': mode,
            'run_id': packet['run_id'], 'exact_readback': True,
            'production_queue_tested': False, 'publication_authorized': False}


def rss_shadow():
    import requests
    import feedparser
    from mkt_flow_p0.opportunity_shadow import compare
    from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO
    url = FEEDS_PADRAO['tecnoblog']
    # Fixed existing source only; never follows links to articles or redirects.
    with requests.get(url, timeout=8, allow_redirects=False, stream=True,
                      headers={'User-Agent': 'ConexoTech-readonly-shadow/1'}) as response:
        if response.status_code != 200:
            raise ValueError('FEED_HTTP_' + str(response.status_code))
        body = bytearray()
        for chunk in response.iter_content(16384):
            body.extend(chunk)
            if len(body) > 1024 * 1024:
                raise ValueError('FEED_RESPONSE_EXCEEDS_1_MIB')
    parsed = feedparser.parse(bytes(body))
    if not parsed.entries:
        raise ValueError('FEED_EMPTY_OR_INVALID')
    now = datetime.now(timezone.utc)
    candidates = [{'title': entry.get('title', ''), 'url': entry.get('link', ''),
                   'kind': 'noticia', 'observed_at': now.isoformat(),
                   'published_at': entry.get('published', '')}
                  for entry in parsed.entries[:3]]
    report = compare(candidates, now=now)
    # Persist ephemeral local JSON for replay in this run; no public content artifact.
    with open('shadow-real.json', 'x', encoding='utf-8') as stream:
        json.dump({'source_url': url, 'observed_at': now.isoformat(),
                   'input': candidates, 'report': report}, stream, ensure_ascii=False)
    return {'probe': 'real-rss-shadow', 'source_url': url,
            'observed_at': now.isoformat(), 'input_count': len(candidates),
            'response_sha256': hashlib.sha256(body).hexdigest(),
            'counts': report['counts'], 'reason_counts': report['reason_counts'],
            'demand_verified': False, 'event_dates_verified': False,
            'queue_changed': False, 'publication_authorized': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['write', 'read', 'rss-shadow'])
    parser.add_argument('--run')
    args = parser.parse_args()
    try:
        result = rss_shadow() if args.mode == 'rss-shadow' else persistence(args.mode, args.run or '')
    except Exception as exc:
        # Exception messages from network/SQL may contain credentials: never print them.
        safe = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r'[A-Z0-9_]+', str(exc)) else type(exc).__name__
        print(json.dumps({'status': 'BLOCKED', 'reason': safe}))
        return 1
    rendered = json.dumps(result, sort_keys=True)
    print(rendered)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(rendered + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
