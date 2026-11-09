"""Editable core blocks for supervised draft delivery; never writes or publishes."""
import html
import json
from html.parser import HTMLParser
from urllib.parse import urlsplit


class _Fragments(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False);self.depth=0;self.start=None;self.parts=[];self.buffer=[]
    def handle_starttag(self,tag,attrs):
        if self.depth==0:self.start=tag
        self.buffer.append(self.get_starttag_text())
        if tag not in {'img','source','br','hr','meta','link','input'}:self.depth+=1
    def handle_endtag(self,tag):
        self.buffer.append('</'+tag+'>');self.depth-=1
        if self.depth==0:
            self.parts.append((self.start,''.join(self.buffer)));self.buffer=[];self.start=None
    def handle_data(self,data):
        if self.depth:self.buffer.append(data)
    def handle_entityref(self,name):self.buffer.append('&'+name+';')
    def handle_charref(self,name):self.buffer.append('&#'+name+';')


def serialize_blocks(body_html, *, featured_resource=None):
    parser=_Fragments();parser.feed(body_html)
    if parser.depth or parser.buffer:raise ValueError('UNBALANCED_EDITORIAL_HTML')
    out=[]
    for tag,fragment in parser.parts:
        if tag=='figure' and featured_resource is not None:
            # Theme renders featured image once. Preserve a visible caption/credit.
            e=lambda s:html.escape(s,quote=True)
            r=featured_resource
            fragment='<p>'+e(r['caption'])+' Foto: <a href="'+e(r['source_page'])+'">'+e(r['author'])+'</a> / Wikimedia Commons — <a href="'+e(r['license_url'])+'">'+e(r['license'])+'</a>.</p>'
            tag='p'
        if tag=='p':name='paragraph';attrs=''
        elif tag in {'h2','h3'}:
            name='heading';attrs='' if tag=='h2' else ' '+json.dumps({'level':3})
            fragment=fragment.replace('<'+tag+'>','<'+tag+' class="wp-block-heading">',1)
        elif tag=='table':
            name='table';attrs=' '+json.dumps({'hasFixedLayout':False})
            fragment='<figure class="wp-block-table">'+fragment+'</figure>'
        elif tag in {'ol','ul'}:
            name='list';attrs=' '+json.dumps({'ordered':tag=='ol'})
            fragment=fragment.replace('<'+tag+'>','<'+tag+' class="wp-block-list">',1)
            fragment=fragment.replace('<li>','<!-- wp:list-item --><li>').replace('</li>','</li><!-- /wp:list-item -->')
        else:raise ValueError('UNSUPPORTED_EDITORIAL_BLOCK')
        out.append('<!-- wp:'+name+attrs+' -->\n'+fragment+'\n<!-- /wp:'+name+' -->')
    return '\n\n'.join(out)


def prepare_draft_payload(handoff, body_html, media_receipt, *, expected_title, author_id):
    from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt
    from mkt_flow_p0.image_protocol import validate_resource
    validar_handoff_chatgpt(handoff)
    resource=validate_resource(handoff['metadata']['image_resource'])
    media_id=media_receipt.get('id');url=media_receipt.get('source_url','')
    p=urlsplit(url)
    if (type(media_id) is not int or media_id<=0 or p.scheme!='https'
            or p.hostname!='conexotech.com.br' or not media_receipt.get('alt_text')
            or type(author_id) is not int or author_id<=0):raise ValueError('UNVERIFIED_WORDPRESS_MEDIA')
    if handoff['metadata']['title']!=expected_title:raise ValueError('DRAFT_TITLE_MISMATCH')
    return {'title':expected_title,'slug':handoff['metadata']['seo']['slug'],
            'status':'draft','author':author_id,'featured_media':media_id,
            'content':serialize_blocks(body_html,featured_resource=resource),
            'excerpt':handoff['metadata']['seo']['description'],'comment_status':'closed'}
