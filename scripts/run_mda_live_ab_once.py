"""One bounded live 4-case Conexo MDA A/B run; WordPress read-only, Groq Free, encrypted artifacts.

Runs only in the owner-gated workflow. Never publishes, writes WP, modifies GitHub,
or emits unpublished text, prompts, credentials, or source URLs in public logs.
"""
import base64
import hashlib
import io
import json
import os
import re
import secrets
import sys
import time
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from mkt_flow_p0.rewriter import SYSTEM_PROMPT
from scripts.prepare_mda_ab import build_pair

OUT = Path('work/mda-ab-live/public')
PRIVATE = Path('work/mda-ab-live/private')
MODEL = 'openai/gpt-oss-120b'
SPECS = (
    ('guia-9798', 9798, {
        'genre': 'guia',
        'reader': 'Pessoas que precisam corrigir o comportamento do teclado no iPhone sem perder funções úteis.',
        'need': 'Distinguir autocorreção, texto preditivo e previsões em linha antes de mudar o ajuste.',
        'angle': 'Organizar o guia por sintoma e impacto reversível, evitando reproduzir a ordem do manual.',
        'contribution': 'Dar critérios práticos para decidir qual controle mudar e qual recurso manter.',
        'limits': 'Sem testes próprios de aparelhos; disponibilidade e nomes dos controles variam por versão e idioma.'}),
    ('noticia-9635', 9635, {
        'genre': 'noticia',
        'reader': 'Usuários brasileiros que desejam entender opções futuras de internet via satélite.',
        'need': 'Distinguir homologação regulatória de disponibilidade comercial e cobertura real.',
        'angle': 'Separar o certificado do terminal, capacidade anunciada e incerteza sobre planos e operações.',
        'contribution': 'Apontar quais informações faltam para transformar o anúncio em escolha concreta de consumidor.',
        'limits': 'Sem teste próprio do terminal, sem tabela oficial confirmada de preços e sem comprovação de cobertura comercial.'}),
    ('analise-9687', 9687, {
        'genre': 'analise',
        'reader': 'Leitores interessados em inteligência artificial, jogos, hardware e consequências de novas técnicas.',
        'need': 'Diferenciar reações à IA criativa em jogos de seu emprego em ferramentas e engenharia.',
        'angle': 'Confrontar dados de opinião, limites das amostras e afirmações de fornecedores sem extrapolar.',
        'contribution': 'Explicar tensões e critérios de avaliação, sem confundir percepção de jogadores com profissionais.',
        'limits': 'Pesquisas de amostra voluntária, comunicados de fornecedores e ausência de testes próprios limitam conclusões.'}),
    ('comparativo-9681', 9681, {
        'genre': 'comparativo',
        'reader': 'Compradores brasileiros de smartphones Samsung que buscam equilíbrio entre preço e durabilidade.',
        'need': 'Escolher entre Galaxy A36 e A16 5G com base em diferenças relevantes e usos reais.',
        'angle': 'Comparar por critérios de suporte, resistência e desempenho declarado, sem supor teste de laboratório.',
        'contribution': 'Construir decisão condicional para perfis de uso, preservando limites de especificações oficiais.',
        'limits': 'Sem preços atuais auditados nem medição independente de desempenho, bateria ou longevidade em uso real.'}),
)


class SafeAbort(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class MarkdownExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.ignore_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.ignore_depth += 1
        if self.ignore_depth:
            return
        if tag in {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'div', 'tr', 'blockquote'}:
            self.parts.append('\n\n')
        if tag.startswith('h') and tag[1:].isdigit():
            self.parts.append('#' * min(int(tag[1:]), 4) + ' ')
        if tag in {'td', 'th'}:
            self.parts.append(' | ')
        if tag == 'a':
            href = dict(attrs).get('href')
            self.links.append(href if href and href.startswith('https://') else None)

    def handle_data(self, data):
        if not self.ignore_depth:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.ignore_depth = max(0, self.ignore_depth - 1)
            return
        if self.ignore_depth:
            return
        if tag == 'a' and self.links:
            link = self.links.pop()
            if link:
                self.parts.append(' [' + link + ']')
        if tag in {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'div', 'tr', 'blockquote'}:
            self.parts.append('\n\n')

    def result(self):
        source = ''.join(self.parts)
        source = re.sub(r'[ \t]+', ' ', source)
        source = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', source)
        return source.strip()


def fetch_private_draft(post_id):
    import requests
    base = os.environ.get('WP_URL', '').rstrip('/')
    if base != 'https://conexotech.com.br':
        raise SafeAbort('WORDPRESS_TARGET_NOT_ALLOWED')
    user = os.environ.get('WP_USER', '').strip()
    pw = os.environ.get('WP_APP_PASSWORD', '').strip()
    if not user or not pw:
        raise SafeAbort('WORDPRESS_CREDENTIALS_MISSING')
    url = f'{base}/wp-json/wp/v2/posts/{post_id}?context=edit'
    try:
        response = requests.get(url, auth=(user, pw), timeout=25, allow_redirects=False,
                                headers={'Accept': 'application/json'})
    except requests.RequestException:
        raise SafeAbort('WORDPRESS_READ_ERROR') from None
    if response.status_code != 200:
        raise SafeAbort(f'WORDPRESS_HTTP_{response.status_code}')
    try:
        data = response.json()
        if data['id'] != post_id or data['status'] != 'draft':
            raise SafeAbort('WORDPRESS_UNEXPECTED_POST_STATUS')
        raw = data['content'].get('raw') or data['content'].get('rendered')
        title = data['title'].get('raw') or data['title'].get('rendered')
        if not isinstance(raw, str) or not isinstance(title, str):
            raise SafeAbort('WORDPRESS_MISSING_CONTENT')
    except (KeyError, AttributeError, TypeError, ValueError):
        raise SafeAbort('WORDPRESS_INVALID_RESPONSE') from None
    extractor = MarkdownExtractor()
    extractor.feed(raw)
    text = extractor.result()
    if not 350 <= len(text.split()) <= 10000 or len(text) > 60000:
        raise SafeAbort('WORDPRESS_DRAFT_NOT_COMPLETE')
    from html import unescape
    return unescape(re.sub('<[^<>]*>', '', title)).strip(), text, str(data.get('modified_gmt', ''))


def build_private_case(case_id, post_id, brief):
    title, content, modified = fetch_private_draft(post_id)
    case = {'schema': 'conexo-mda-ab-source/1', 'case_id': case_id, 'title': title,
            'source_name': 'Rascunho editorial original ConexoTech e suas referências',
            'source_text': content, 'editorial_brief': brief, 'research_context': None,
            'intended_generation': {'model': MODEL, 'temperature': 0.5, 'max_tokens': 3800}}
    control, mda, manifest = build_pair(case)
    return case, control, mda, manifest, modified


def encrypt_private(root, destination, public_key_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(root))
    pub = serialization.load_pem_public_key(Path(public_key_path).read_bytes())
    if getattr(pub, 'key_size', 0) < 3072:
        raise SafeAbort('PUBLIC_KEY_TOO_SMALL')
    key = AESGCM.generate_key(bit_length=256)
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, buffer.getvalue(), b'conexo-mda-ab/1')
    wrapped = pub.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                                          algorithm=hashes.SHA256(), label=None))
    output = {'schema': 'conexo-mda-ab/1', 'nonce': base64.b64encode(nonce).decode(),
              'wrapped_key': base64.b64encode(wrapped).decode(),
              'ciphertext': base64.b64encode(ciphertext).decode(),
              'ciphertext_sha256': hashlib.sha256(ciphertext).hexdigest()}
    destination.write_text(json.dumps(output), encoding='utf-8')
    return output['ciphertext_sha256']


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    report = {'schema': 'conexo-mda-ab-public-receipt/1', 'status': 'PREFLIGHT_PENDING',
              'model': MODEL, 'cases': [], 'total_provider_calls': 0, 'completed_pairs': 0,
              'factual_approval': False, 'independent_review': False,
              'publication_authorized': False, 'wordpress_writes': 0,
              'groq_free_quota_unverified': True}
    code = 3
    try:
        if (os.getenv('MDA_AB_FREE_CONFIRMATION') != 'CONFIRMED_FREE_TIER'
                or os.getenv('MDA_AB_MAX_CALLS') != '8'):
            raise SafeAbort('FREE_TIER_NOT_CONFIRMED')
        key = os.environ.get('GROQ_API_KEY', '').strip()
        if not key:
            raise SafeAbort('GROQ_KEY_MISSING')
        from groq import Groq
        client = Groq(api_key=key, max_retries=0, timeout=90)
        models = client.models.list()
        if MODEL not in {x.id for x in models.data}:
            raise SafeAbort('SELECTED_MODEL_UNAVAILABLE')
        # All four drafts must be readable before any paid/free model tokens are used.
        cases = [build_private_case(*spec) for spec in SPECS]
        for (case, control, mda, manifest, modified) in cases:
            folder = PRIVATE / case['case_id']
            folder.mkdir(mode=0o700)
            (folder / 'source.private.json').write_text(json.dumps(case, ensure_ascii=False), encoding='utf-8')
            (folder / 'control.prompt.txt').write_text(control, encoding='utf-8')
            (folder / 'mda.prompt.txt').write_text(mda, encoding='utf-8')
            (folder / 'preflight.private.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
            report['cases'].append({'case_id': case['case_id'], 'source_sha256': manifest['source_sha256'],
                                    'brief_sha256': manifest['brief_sha256'],
                                    'wp_modified_gmt': modified, 'arms': []})
        report['status'] = 'GENERATING'
        # Ordered within each pair and alternating first arm between cases: avoids a
        # systematic time-of-day treatment confound while retaining exact prompts.
        for idx, (case, control, mda, manifest, _) in enumerate(cases):
            pairs = [('control', control), ('mda', mda)] if idx % 2 == 0 else [('mda', mda), ('control', control)]
            for arm, prompt in pairs:
                if report['total_provider_calls'] >= 8:
                    raise SafeAbort('MAX_CALLS_REACHED')
                if report['total_provider_calls']:
                    time.sleep(70)  # conservative free-tier TPM pacing, no paid fallback
                report['total_provider_calls'] += 1
                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[{'role':'system','content': SYSTEM_PROMPT}, {'role':'user','content':prompt}],
                        temperature=0.5, max_tokens=3800, timeout=90,
                        reasoning_effort='low', include_reasoning=False,
                        response_format={'type':'json_object'},
                    )
                except Exception as exc:
                    status = getattr(exc, 'status_code', None)
                    reason = ('GROQ_RATE_LIMIT' if status == 429 else
                              'GROQ_AUTH' if status in (401,403) else
                              'GROQ_MODEL_REQUEST' if status in (400,404) else
                              'GROQ_PROVIDER_ERROR')
                    report['cases'][idx]['arms'].append({'arm':arm,'state':reason})
                    raise SafeAbort(reason) from None
                finish = response.choices[0].finish_reason
                content = response.choices[0].message.content or ''
                folder = PRIVATE / case['case_id']
                (folder / f'{arm}.raw.private.json.txt').write_text(content, encoding='utf-8')
                try:
                    data = json.loads(content)
                    article = data.get('texto_markdown')
                    if not isinstance(article, str):
                        article = ''
                    words = len(article.split())
                except (ValueError, TypeError, AttributeError):
                    article, words = '', 0
                minimum = 450 if case['editorial_brief']['genre']=='noticia' else 600
                complete = finish != 'length' and words >= minimum
                if article:
                    (folder / f'{arm}.article.private.md').write_text(article, encoding='utf-8')
                usage = getattr(response, 'usage', None)
                receipt = {'arm':arm, 'state':'COMPLETE' if complete else 'NOT_COMPLETE',
                           'finish_reason': finish if finish in ('stop','length') else 'OTHER',
                           'word_count':words, 'text_sha256':hashlib.sha256(article.encode()).hexdigest(),
                           'prompt_tokens':int(getattr(usage,'prompt_tokens',0) or 0),
                           'completion_tokens':int(getattr(usage,'completion_tokens',0) or 0)}
                report['cases'][idx]['arms'].append(receipt)
            if all(a['state']=='COMPLETE' for a in report['cases'][idx]['arms']):
                report['completed_pairs'] += 1
        report['status'] = 'COMPLETE_GENERATION_REVIEW_PENDING' if report['completed_pairs']==4 else 'PARTIAL_INCOMPLETE_ARTICLES'
        code = 0 if report['completed_pairs']==4 else 3
    except SafeAbort as exc:
        report['status'] = exc.code
    except Exception:
        report['status'] = 'INTERNAL_FAILURE_REDACTED'
    finally:
        try:
            report['sealed_ciphertext_sha256'] = encrypt_private(
                PRIVATE, OUT / 'evidence-encrypted.json', 'data/homolog/mda_ab_public_20261110.pem')
        except Exception:
            report['status'] = 'ENCRYPTION_FAILURE'
            code = 4
        (OUT / 'manifest-public.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps({'status':report['status'],'completed_pairs':report['completed_pairs'],
                          'total_provider_calls':report['total_provider_calls'],
                          'encrypted': 'sealed_ciphertext_sha256' in report,
                          'wordpress_writes':0, 'publication_authorized':False}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())