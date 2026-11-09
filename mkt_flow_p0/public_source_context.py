"""Bounded public-source context check, NOT factual or product-test approval."""
import hashlib
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser

AGENT = 'ConexoTech-Research/1'
LIMIT = 1024 * 1024


class ArticleContext(HTMLParser):
    def __init__(self):
        super().__init__(); self.depth=0; self.skip=0; self.text=[]; self.canonicals=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in ('script','style'):self.skip+=1
        if tag=='article':self.depth+=1
        if tag=='link' and attrs.get('rel','').lower()=='canonical':
            self.canonicals.append(attrs.get('href',''))
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.skip:self.skip-=1
        if tag=='article' and self.depth:self.depth-=1
    def handle_data(self,data):
        if self.depth and not self.skip:self.text.append(data)


def fetch(url):
    import requests
    with requests.get(url,timeout=8,allow_redirects=False,stream=True,
                      headers={'User-Agent':AGENT}) as response:
        if response.status_code!=200:
            raise ValueError('SOURCE_HTTP_'+str(response.status_code))
        data=bytearray()
        for chunk in response.iter_content(16384):
            data.extend(chunk)
            if len(data)>LIMIT:raise ValueError('SOURCE_RESPONSE_TOO_LARGE')
    return bytes(data)


def verify_context(url, terms, *, transport=fetch):
    parsed=urlsplit(url)
    if (parsed.scheme!='https' or parsed.hostname!='tecnoblog.net' or parsed.port is not None
            or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment):
        raise ValueError('SOURCE_OUTSIDE_ALLOWLIST')
    if not isinstance(terms,list) or not terms or any(not isinstance(t,str) or not t for t in terms):
        raise ValueError('INVALID_CONTEXT_TERMS')
    robots=transport('https://tecnoblog.net/robots.txt')
    robots_text=robots.decode('utf-8','replace')
    if not re.search(r'(?im)^user-agent\s*:',robots_text):
        raise ValueError('SOURCE_ROBOTS_INVALID')
    parser=RobotFileParser();parser.parse(robots_text.splitlines())
    if not robots.strip() or not parser.can_fetch(AGENT,url):
        raise ValueError('SOURCE_ROBOTS_BLOCKED')
    body=transport(url)
    page=ArticleContext();page.feed(body.decode('utf-8','replace'))
    if len(page.canonicals)!=1 or urljoin(url,page.canonicals[0]).rstrip('/')!=url.rstrip('/'):
        raise ValueError('SOURCE_CANONICAL_MISMATCH')
    text=' '.join(page.text).casefold()
    if not text or not all(term.casefold() in text for term in terms):
        raise ValueError('SOURCE_ARTICLE_CONTEXT_NOT_CONFIRMED')
    return {'source_url':url,'robots_allowed':True,'canonical_matches':True,
            'context_terms_found':terms,'article_sha256':hashlib.sha256(body).hexdigest(),
            'factuality_verified':False,'own_product_test':False}
