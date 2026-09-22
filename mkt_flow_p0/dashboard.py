"""
mkt_flow_p0.dashboard — Dashboard ROI consolidado P1.2
Gera dashboard_p1.html local, estilo whois_dashboard.html
Uso: python -m mkt_flow_p0.dashboard
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("dashboard")

DB_PATH = Path(__file__).parent.parent / "mkt_flow_p0.db"
OUT_HTML = Path(__file__).parent.parent / "dashboard_p1.html"
OUT_JSON = Path(__file__).parent.parent / "dashboard_p1.json"


def _query(sql, params=()):
    # Nuvem (Turso) quando configurado — sem Turso, SQLite local
    try:
        from .cloud_db import turso_enabled, turso_execute
        if turso_enabled():
            # Converte ? para execução via HTTP
            r = turso_execute(sql, params)
            if "erro" not in r:
                # turso_execute retorna cols/rows; reconstrói dicts
                cols = r.get("cols", [])
                return [dict(zip(cols, row)) for row in r.get("rows", [])]
    except Exception:
        pass
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def coletar_dados():
    # Pipeline runs
    try:
        runs = _query("SELECT * FROM pipeline_runs ORDER BY created_at DESC")
    except Exception:
        runs = []
    # Link publicações
    try:
        pubs = _query("SELECT * FROM link_publicacoes ORDER BY created_at DESC")
    except Exception:
        pubs = []
    # RSS runs (pipeline_rss) — unificação 12 (dashboard único)
    try:
        rss = _query("SELECT * FROM rss_runs ORDER BY created_at DESC")
    except Exception:
        rss = []
    # Custo LLM + runs clássicos: DB OFICIAL é mkt_flow_p0.db.
    # Migração 22/09/2026 trouxe affiliate_runs do legado mkt_flow.db
    # (arquivado em _arquivo/). Nunca engolir falha em silêncio.
    costs = []
    cost_db = DB_PATH
    if not cost_db.exists():
        logger.warning(f"dashboard: DB oficial ausente em {cost_db} — seção de custos vazia")
    if cost_db.exists():
        try:
            con = sqlite3.connect(cost_db)
            con.row_factory = sqlite3.Row
            cur = con.execute("SELECT * FROM cost_log ORDER BY id DESC LIMIT 100")
            costs = [dict(r) for r in cur.fetchall()]
            con.close()
        except Exception as e:
            logger.warning(f"dashboard: falha lendo cost_log: {e}")
    aff_total = 0
    if cost_db.exists():
        try:
            con = sqlite3.connect(cost_db)
            cur = con.execute("SELECT COUNT(*) FROM affiliate_runs")
            aff_total = int(cur.fetchone()[0] or 0)
            con.close()
        except Exception as e:
            logger.warning(f"dashboard: falha lendo affiliate_runs: {e}")
    # affiliate_runs migrado do legado para o DB oficial (22/09/2026)

    total_runs = len(runs)
    total_pubs = len(pubs)
    valid_pass = sum(1 for r in runs if r.get("status_validacao") == "PASS")
    policy_pass = sum(1 for r in runs if r.get("status_politica") == "PASS")
    by_platform = {}
    for p in pubs:
        by_platform[p.get("plataforma", "desconhecida")] = by_platform.get(p.get("plataforma", "desconhecida"), 0) + 1
    by_program = {}
    for p in pubs:
        by_program[p.get("programa", "desconhecido")] = by_program.get(p.get("programa", "desconhecido"), 0) + 1

    # ROI estimado (soma dos roi_json)
    total_roi_liquido = 0
    total_custo = 0
    for r in runs:
        try:
            roi = json.loads(r.get("roi_json") or "{}")
            total_roi_liquido += float(roi.get("lucro_liquido_brl", 0) or 0)
            total_custo += float(roi.get("custo_ads_brl", 0) or 0)
        except Exception:
            pass
    cost_total = sum(float(c.get("cost", 0) or 0) for c in costs)
    rss_ok = sum(1 for r in rss if r.get("wp_post_id"))
    rss_bloq = sum(1 for r in rss if (r.get("veredito") or "") == "BLOQUEADO" or not r.get("wp_post_id"))

    return {
        "total_runs": total_runs,
        "total_pubs": total_pubs,
        "valid_pass": valid_pass,
        "policy_pass": policy_pass,
        "by_platform": by_platform,
        "by_program": by_program,
        "runs": runs[:20],
        "pubs": pubs[:20],
        "costs": costs[:10],
        "total_roi_liquido": round(total_roi_liquido, 2),
        "total_custo": round(total_custo, 2),
        "cost_total": round(cost_total, 5),
        # Unificação 12: RSS + clássico
        "rss_total": len(rss),
        "rss_publicados": rss_ok,
        "rss_bloqueados": rss_bloq,
        "rss": rss[:20],
        "affiliate_runs_classico": aff_total,
    }


def gerar_html(dados: dict):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    g = lambda k, d=0: dados.get(k, d)
    # Cards
    cards = f"""
        <div class="card" style="border-left:4px solid #16a34a"><div class="card-icon" style="background:#16a34a">✓</div><div><div class="card-count">{g('valid_pass')}</div><div class="card-label">PASS validação</div><div class="card-desc">Links aprovados</div></div></div>
        <div class="card" style="border-left:4px solid #2563eb"><div class="card-icon" style="background:#2563eb">◉</div><div><div class="card-count">{g('total_runs')}</div><div class="card-label">Pipeline runs</div><div class="card-desc">Total processado</div></div></div>
        <div class="card" style="border-left:4px solid #9333ea"><div class="card-icon" style="background:#9333ea">#</div><div><div class="card-count">{g('total_pubs')}</div><div class="card-label">Publicações</div><div class="card-desc">Onde foi publicado</div></div></div>
        <div class="card" style="border-left:4px solid #0ea5e9"><div class="card-icon" style="background:#0ea5e9">R</div><div><div class="card-count">{g('rss_publicados')}/{g('rss_total')}</div><div class="card-label">RSS publicados</div><div class="card-desc">Rascunhos no WP ({g('rss_bloqueados')} filtrados)</div></div></div>
        <div class="card" style="border-left:4px solid #ea580c"><div class="card-icon" style="background:#ea580c">$</div><div><div class="card-count">R$ {g('total_roi_liquido')}</div><div class="card-label">Lucro est.</div><div class="card-desc">ROI estimado (P0)</div></div></div>
        <div class="card" style="border-left:4px solid #6b7280"><div class="card-icon" style="background:#6b7280">¢</div><div><div class="card-count">${g('cost_total')}</div><div class="card-label">Custo LLM</div><div class="card-desc">Groq até agora (+{g('affiliate_runs_classico')} runs clássicos)</div></div></div>
    """
    rows_runs = ""
    for r in g("runs", []):
        status = r.get("status_validacao", "")
        color = "#16a34a" if status == "PASS" else "#dc2626" if status == "FAIL" else "#ca8a04"
        rows_runs += f'<tr><td><span class="badge" style="background:{color}">{status}</span></td><td><strong>{r.get("link_id","")}</strong></td><td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{r.get("link","")}">{r.get("link","")[:60]}</span></td><td>{r.get("titulo","")[:40]}</td><td>{r.get("preco","")}</td><td>{r.get("created_at","")[:16]}</td></tr>'

    rows_pubs = ""
    for p in g("pubs", []):
        rows_pubs += f'<tr><td>{p.get("link_id","")}</td><td>{p.get("plataforma","")}</td><td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{p.get("url_publicacao","")}">{p.get("url_publicacao","")[:60]}</td><td>{p.get("programa","")}</td><td>{p.get("status_validacao","")}</td><td>{p.get("created_at","")[:16]}</td></tr>'

    rows_rss = ""
    for r in g("rss", []):
        ok = bool(r.get("wp_post_id"))
        color = "#16a34a" if ok else "#ca8a04"
        rot = "rascunho" if ok else (r.get("veredito") or "—")
        rows_rss += f'<tr><td><span class="badge" style="background:{color}">{rot}</span></td><td>{r.get("fonte","")}</td><td style="max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{r.get("titulo_seo","")}">{r.get("titulo_seo","")[:60]}</td><td>{r.get("palavras","")}</td><td>{r.get("created_at","")[:16]}</td></tr>'

    by_plat = "".join(f"<li><strong>{k}:</strong> {v}</li>" for k, v in g("by_platform", {}).items()) or "<li>Nenhum dado</li>"
    by_prog = "".join(f"<li><strong>{k}:</strong> {v}</li>" for k, v in g("by_program", {}).items()) or "<li>Nenhum dado</li>"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MKT Flow — Dashboard P1.2</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}} body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8fafc;color:#1e293b;padding:20px}}
.header{{background:white;padding:20px;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1);margin-bottom:20px}}
.header h1{{font-size:22px}} .header p{{color:#64748b;font-size:13px;margin-top:4px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}}
.card{{background:white;padding:14px;border-radius:8px;display:flex;align-items:center;gap:12px;box-shadow:0 1px 2px rgba(0,0,0,0.05)}}
.card-icon{{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold}}
.card-count{{font-size:18px;font-weight:bold}} .card-label{{font-size:12px;font-weight:600}} .card-desc{{font-size:11px;color:#64748b}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}} @media(max-width:800px){{.grid2{{grid-template-columns:1fr}}}}
.panel{{background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);padding:16px}}
.panel h3{{font-size:13px;text-transform:uppercase;color:#475569;margin-bottom:10px}}
.table-wrap{{background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);margin-bottom:20px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th{{background:#f1f5f9;text-align:left;padding:10px 12px;font-weight:600;color:#475569;font-size:11px;text-transform:uppercase}} td{{padding:10px 12px;border-top:1px solid #f1f5f9}}
.badge{{color:white;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600}}
.footer{{text-align:center;color:#94a3b8;font-size:12px;margin-top:16px}}
</style>
</head>
<body>
<div class="header">
    <h1>MKT Flow — Dashboard P1.2</h1>
    <p>{g('total_runs')} runs afiliados · {g('rss_total')} pautas RSS · {g('total_pubs')} publicações · Custo LLM ${g('cost_total')} · Atualizado {now} — <a href="dashboard_p1.json" style="color:#2563eb">JSON</a></p>
</div>
<div class="cards">{cards}</div>
<div class="grid2">
    <div class="panel"><h3>Por plataforma</h3><ul style="font-size:13px;line-height:1.8">{by_plat}</ul></div>
    <div class="panel"><h3>Por programa</h3><ul style="font-size:13px;line-height:1.8">{by_prog}</ul></div>
</div>
<div class="table-wrap">
<table><thead><tr><th>Validação</th><th>Link ID</th><th>Link</th><th>Título</th><th>Preço</th><th>Data</th></tr></thead><tbody>{rows_runs or '<tr><td colspan=6 style="text-align:center;color:#94a3b8">Nenhum run ainda — rode pipeline_p0.py</td></tr>'}</tbody></table>
</div>
<div class="table-wrap">
<table><thead><tr><th>Link ID</th><th>Plataforma</th><th>URL Publicação</th><th>Programa</th><th>Status</th><th>Data</th></tr></thead><tbody>{rows_pubs or '<tr><td colspan=6 style="text-align:center;color:#94a3b8">Nenhuma publicação — P1.1 registra após pipeline</td></tr>'}</tbody></table>
</div>
<div class="table-wrap">
<table><thead><tr><th>RSS</th><th>Fonte</th><th>Título SEO</th><th>Palavras</th><th>Data</th></tr></thead><tbody>{rows_rss or '<tr><td colspan=5 style="text-align:center;color:#94a3b8">Nenhuma pauta RSS ainda — rode pipeline_rss.py</td></tr>'}</tbody></table>
</div>
<p class="footer">Gerado por mkt_flow_p0.dashboard — P1.2 · Draft local é aceitável (como whois_dashboard.html)</p>
</body>
</html>"""
    return html


def main():
    dados = coletar_dados()
    OUT_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_HTML.write_text(gerar_html(dados), encoding="utf-8")
    print(f"Dashboard gerado: {OUT_HTML.resolve()} ({len(dados['runs'])} runs, {len(dados['pubs'])} pubs)")
    print(f"JSON: {OUT_JSON.resolve()}")

if __name__ == "__main__":
    main()
