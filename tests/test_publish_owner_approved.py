import copy
import hashlib
import json
import os
from unittest.mock import MagicMock, patch
import pytest

from tools.publish_owner_approved import owner_trace, release
from mkt_flow_p0.editorial_broker_transport import publish_via_broker, BrokerBlocked
from mkt_flow_p0.editorial_trace_gate import REQUIRED

VERSION='b'*64
ENV={'WP_USER':'test-service','WP_APP_PASSWORD':'private-password'}


def packet():
    keys=('versao','titulo','categoria','capa','licenca_imagem','fontes','alegacoes',
          'links_internos','seo','html','revisao_substantiva','visual_390','visual_1440')
    return {'schema':'conexo-owner-release/1','version_sha256':VERSION,'payload':{
        'article_id':'wp:9768','content':'<p>Private unpublished draft</p>',
        'title':'Private title','slug':'private-title','wordpress':{'post_id':9768},
        'owner_id':3,'review_mode':'owner','approval_reference':'OWNER-3-9768-SYNTHETIC',
        'checks':{k:{'estado':'VERIFICADO','evidencia':['Synthetic human review '+k]} for k in keys},
        'seo':{'provider':'native','canonical':'https://conexotech.com.br/private-title/',
               'title':'Reviewed SEO','description':'Reviewed description.'}}}


class Response:
    status_code=200
    def __init__(self,data): self.data=data
    def json(self): return self.data


def http(p):
    s=MagicMock()
    s.get.return_value=Response(p)
    return s


def test_import_trace_is_metadata_only_and_does_not_claim_ai_generation():
    p=packet(); t=owner_trace(p)
    assert {e['stage'] for e in t['events']}==set(REQUIRED)
    generation=next(e for e in t['events'] if e['stage']=='generation')
    assert generation['module_id']=='mkt-rss.existing-wp-draft-import'
    assert 'groq' not in json.dumps(t)
    assert p['payload']['content'] not in json.dumps(t)
    assert t['content_sha256']==hashlib.sha256(p['payload']['content'].encode()).hexdigest()
    assert t['publication_authorized'] is False


def test_unverified_check_does_not_become_trace_pass():
    p=packet(); p['payload']['checks']['fontes']['estado']='PENDENTE'
    with pytest.raises(BrokerBlocked,match='OWNER_CHECK_MISSING'): owner_trace(p)


def test_owner_trace_rejects_service_as_human_owner():
    p=packet(); p['payload']['owner_id']=4
    with pytest.raises(BrokerBlocked,match='OWNER_PACKET_INVALID'): owner_trace(p)


def test_default_only_validates_with_no_write():
    p=packet(); s=http(p)
    with patch.dict(os.environ,ENV), patch('tools.publish_owner_approved.publish_via_broker') as publish:
        out=release(9768,VERSION,session=s,identity=lambda _: 'PASS')
    assert out['write'] is False
    publish.assert_not_called(); s.post.assert_not_called()


def test_wrong_expected_version_never_publishes():
    with patch.dict(os.environ,ENV), patch('tools.publish_owner_approved.publish_via_broker') as publish:
        with pytest.raises(BrokerBlocked,match='EXPECTED_OWNER_VERSION_MISMATCH'):
            release(9768,'c'*64,True,session=http(packet()),identity=lambda _: 'PASS')
    publish.assert_not_called()


def test_execute_uses_existing_broker_strict_seo_and_human_evidence_trace():
    with patch.dict(os.environ,ENV), patch('tools.publish_owner_approved.publish_via_broker',return_value={'verified':True}) as publish:
        out=release(9768,VERSION,True,session=http(packet()),identity=lambda _: 'PASS')
    assert out['verified'] is True
    assert publish.call_args.kwargs['owner_release'] is True
    assert publish.call_args.kwargs['require_signed_seo'] is True
    assert publish.call_args.kwargs['trace_packet']['publication_authorized'] is False


def test_no_network_when_service_identity_is_not_verified():
    s=http(packet())
    with pytest.raises(BrokerBlocked,match='MKT_SERVICE_IDENTITY_NOT_VERIFIED'):
        release(9768,VERSION,True,session=s,identity=lambda _: 'WP_IDENTITY_MISMATCH')
    s.get.assert_not_called()


def test_caller_packet_cannot_override_authoritative_owner_approval():
    p=packet(); tampered=copy.deepcopy(p); tampered['payload']['content']='Different content'
    s=http(p)
    with patch('mkt_flow_p0.editorial_broker_transport.save_turso_trace') as save, \
         patch('mkt_flow_p0.editorial_broker_transport.load_core') as core:
        with pytest.raises(BrokerBlocked,match='OWNER_VERSION_NOT_AUTHENTICATED'):
            publish_via_broker(tampered,core_root='.',wp_url='https://conexotech.com.br',
                wp_user='service',wp_password='test',trace_run_id='test-run-9768',intent='publish',
                publication_reference=p['payload']['approval_reference'],session=s,
                require_signed_seo=True,owner_release=True)
    save.assert_not_called(); s.post.assert_not_called(); core.assert_not_called()
