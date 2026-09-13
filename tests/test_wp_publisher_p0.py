"""
Testes P0 — wp_publisher (gate PASS + draft)
pytest tests/test_wp_publisher_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.wp_publisher import publicar_no_wordpress


def _ok(post_id=1, status="draft"):
    m = MagicMock()
    m.status_code = 201
    m.json.return_value = {"id": post_id, "link": f"https://site.com/?p={post_id}", "status": status}
    return m


def test_bloqueia_publish_sem_pass():
    r = publicar_no_wordpress("T", "<p>x</p>", "UNKNOWN", "https://site.com", "u", "p", status_desejado="publish")
    assert "erro" in r and "bloqueada" in r["erro"].lower()


def test_publica_draft_ok():
    with patch("mkt_flow_p0.wp_publisher.requests.post", return_value=_ok()) as mp:
        r = publicar_no_wordpress("T", "<p>x</p>", "UNKNOWN", "https://site.com", "u", "p")
        assert r["status"] == "draft"
        assert mp.called


def test_publica_publish_com_pass():
    with patch("mkt_flow_p0.wp_publisher.requests.post", return_value=_ok(2, "publish")):
        r = publicar_no_wordpress("T", "<p>x</p>", "PASS", "https://site.com", "u", "p", status_desejado="publish")
        assert r["status"] == "publish"


def test_sem_credencial_erro():
    assert "erro" in publicar_no_wordpress("T", "<p>x</p>", "PASS", "", "", "")


def test_slug_e_taxonomias_no_payload():
    from mkt_flow_p0 import wp_publisher as W
    with patch.object(W.requests, "post", return_value=_ok()) as mp:
        publicar_no_wordpress("T", "<p>x</p>", "PASS", "https://site.com", "u", "p",
                              slug="meu-slug", categoria_ids=[3], tag_ids=[7, 8])
        payload = mp.call_args.kwargs["json"]
        assert payload["slug"] == "meu-slug"
        assert payload["categories"] == [3] and payload["tags"] == [7, 8]


def test_rank_math_ok_segundo_passo():
    from mkt_flow_p0 import wp_publisher as W
    post, meta = _ok(), MagicMock()
    meta.status_code = 200
    with patch.object(W.requests, "post", side_effect=[post, meta]) as mp:
        r = publicar_no_wordpress("T", "<p>x</p>", "PASS", "https://site.com", "u", "p",
                                  rank_math={"title": "T", "description": "D", "focus": "fone"})
        assert r["post_id"] == 1 and r.get("meta_ok") is True
        assert mp.call_count == 2
        assert "rank_math_title" in mp.call_args.kwargs["json"]["meta"]


def test_rank_math_falha_mantem_post():
    from mkt_flow_p0 import wp_publisher as W
    ruim = MagicMock()
    ruim.status_code = 400
    ruim.text = "meta inválida"
    with patch.object(W.requests, "post", side_effect=[_ok(), ruim]):
        r = publicar_no_wordpress("T", "<p>x</p>", "PASS", "https://site.com", "u", "p",
                                  rank_math={"title": "T"})
        assert r["post_id"] == 1 and "meta_aviso" in r


def test_garantir_categoria_existente_e_nova():
    from mkt_flow_p0.wp_publisher import garantir_categoria, garantir_tag
    get_existe = MagicMock()
    get_existe.status_code = 200
    get_existe.json.return_value = [{"id": 5, "name": "Notícias"}]
    with patch("mkt_flow_p0.wp_publisher.requests.get", return_value=get_existe):
        assert garantir_categoria("https://site.com", "u", "p", "notícias") == 5
    get_vazio = MagicMock()
    get_vazio.status_code = 200
    get_vazio.json.return_value = []
    criado = MagicMock()
    criado.status_code = 201
    criado.json.return_value = {"id": 9}
    with patch("mkt_flow_p0.wp_publisher.requests.get", return_value=get_vazio), \
         patch("mkt_flow_p0.wp_publisher.requests.post", return_value=criado):
        assert garantir_tag("https://site.com", "u", "p", "Fone JBL") == 9
