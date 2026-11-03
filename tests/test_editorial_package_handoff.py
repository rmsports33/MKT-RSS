"""SEO only joins the reviewed version; no WordPress or AI network."""
import hashlib
import json
import pytest
from mkt_flow_p0.editorial_package_handoff import vincular_seo_antes_da_revisao

CONTENT="<p>Corpo aprovado para revisão, não publicação.</p>"
SLUG="android-drop-recursos"
CANONICAL="https://conexotech.com.br/"+SLUG+"/"

def example():
    payload={"title":"Android Drop","content":CONTENT,"slug":SLUG,"sources":[{"url":"https://example.org/news"}]}
    pkg={"schema_version":"editorial-workflow/2","stage":"draft","payload":payload}
    manifest={"status":"aguardando_revisao","wordpress_written":False,
              "aprovacao_publicacao":False,"seo":{"slug":SLUG,"title":"Android Drop SEO","description":"Descrição verificada"},
              "seo_wp_staging":{"schema_version":"1.0","provider":"native","title":"Android Drop SEO",
                  "description":"Descrição verificada","canonical":CANONICAL,
                  "delivery_status":"not_written","approved_for_publication":False}}
    return pkg,manifest

def test_binds_seo_and_changes_digest_without_approving():
    p,m=example()
    out=vincular_seo_antes_da_revisao(p,m,CONTENT)
    assert "seo" not in p["payload"]
    assert out["payload"]["seo"]["canonical"]==CANONICAL
    digest=hashlib.sha256(json.dumps(out["payload"],sort_keys=True,ensure_ascii=False,
                                 separators=(",", ":")).encode()).hexdigest()
    assert out["version_sha256"]==digest
    assert "reviews" not in out and "human_acceptance" not in out
    assert out["stage"]=="draft"

@pytest.mark.parametrize("case",["approved","reviewed","changed-body","wrong-slug",
                                  "foreign-canonical","approval-meta","duplicate","stale-digest",
                                  "already-written","wrong-title","extra-field"])
def test_fail_closed_on_stale_or_unsafe_source(case):
    p,m=example();body=CONTENT
    if case=="approved":p["stage"]="ready"
    elif case=="reviewed":p["reviews"]=[{"status":"PASS"}]
    elif case=="changed-body":body=CONTENT+"mutated"
    elif case=="wrong-slug":m["seo"]["slug"]="other"
    elif case=="foreign-canonical":m["seo_wp_staging"]["canonical"]="https://other.example/"+SLUG+"/"
    elif case=="approval-meta":m["seo_wp_staging"]["approved_for_publication"]=True
    elif case=="duplicate":p["payload"]["seo"]={"title":"old"}
    elif case=="stale-digest":p["version_sha256"]="f"*64
    elif case=="already-written":m["wordpress_written"]=True
    elif case=="wrong-title":m["seo"]["title"]="Changed after candidate"
    elif case=="extra-field":m["seo_wp_staging"]["rank_math_title"]="unsafe"
    with pytest.raises(ValueError):
        vincular_seo_antes_da_revisao(p,m,body)

def test_previous_valid_version_is_checked_before_rehash():
    p,m=example()
    p["version_sha256"]=hashlib.sha256(json.dumps(p["payload"],sort_keys=True,
                             ensure_ascii=False,separators=(",", ":")).encode()).hexdigest()
    assert vincular_seo_antes_da_revisao(p,m,CONTENT)["version_sha256"] != p["version_sha256"]
