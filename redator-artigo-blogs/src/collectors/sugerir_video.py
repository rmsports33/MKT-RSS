"""src.collectors.sugerir_video — sugere reviews em vídeo (YouTube Data API v3).

Fluxo: busca -> detalhes -> score -> ranking para APROVAÇÃO humana.
Nada entra na ficha sozinho: o dono escolhe 1 candidato e os campos
youtube_* são preenchidos à mão (ver docs/politica-curadoria-video.md).

Uso (chave por sessão, nunca commitar):
    set YOUTUBE_API_KEY=...  (Windows, só na sessão)
    python -m src.collectors.sugerir_video --modelo "Galaxy S24" --modelo "iPhone 15"

Custo: search.list = 100 unidades de cota; videos.list = 1. Cota grátis = 10.000/dia.
Só stdlib (urllib) — zero dependência nova.
"""
import argparse
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from dotenv import load_dotenv
    _AQUI = Path(__file__).resolve()
    load_dotenv(_AQUI.parents[2] / ".env", override=False)  # redator-artigo-blogs/.env
    load_dotenv(_AQUI.parents[3] / ".env", override=False)  # MY PROJECTS FLOW/.env (global)
except Exception:
    pass

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

DURACAO_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")
PT_RE = re.compile(r"[ãõâêîôûáéíóúç]|análise|analise|vale a pena|celular|tela|bateria|câmera|preço|opinião|sincera|comprei|testei|brasil",
                   re.IGNORECASE)


def eh_pt(titulo: str) -> bool:
    """Heurística de português no título (diacríticos ou vocabulário BR)."""
    return bool(PT_RE.search(str(titulo or "")))
CLICKBAIT_RE = re.compile(
    r"(NÃO COMPRE|NUNCA COMPRE|DESTRUI|URGENTE|IMPERDÍVEL|GOLPE|CUIDADO|!!!|\?\?\?)",
    re.IGNORECASE,
)


def parse_iso8601_duracao(s: str) -> int:
    """PT8M32S -> 512 (segundos). Inválido -> 0."""
    m = DURACAO_RE.match(str(s or "").strip())
    if not m:
        return 0
    h, mi, se = (int(g) if g else 0 for g in m.groups())
    return h * 3600 + mi * 60 + se


def flags_clickbait(titulo: str) -> list:
    """Sinaliza títulos com padrão caça-clique (curadoria decide)."""
    t = str(titulo or "")
    flags = []
    if CLICKBAIT_RE.search(t):
        flags.append("clickbait")
    if len(re.findall(r"\b[A-ZÁÉÍÓÚÇ]{4,}\b", t)) >= 3:
        flags.append("caps-excesso")
    return flags


def pontuar(item: dict, canais_aprovados: tuple = (), bonus_pt: float = 0.0) -> float:
    """Score explicável: audiência (log) + aprovação + formato + PT − penalidades."""
    nota = math.log10(int(item.get("views", 0) or 0) + 1)
    if str(item.get("canal_id", "")) in canais_aprovados or str(item.get("canal", "")) in canais_aprovados:
        nota += 2.0
    if bonus_pt and eh_pt(item.get("titulo", "")):
        nota += bonus_pt
    titulo = str(item.get("titulo", "")).lower()
    if "review" in titulo or "análise" in titulo or "analise" in titulo:
        nota += 0.5
    dur = int(item.get("duracao_s", 0) or 0)
    if dur < 90:
        nota -= 1.0
    elif 240 <= dur <= 1200:
        nota += 0.5
    nota -= 1.5 * len(flags_clickbait(item.get("titulo", "")))
    return round(nota, 2)


def _get_json(url: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + "?" + qs, headers={"User-Agent": "ConexoTech-VideoSuggester/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def buscar_candidatos(modelo: str, key: str, max_results: int = 10,
                      ordem: str = "relevance", busca: str = "") -> list:
    """Retorna candidatos incorporáveis ordenados por score (sem escrever nada)."""
    if ordem not in ("relevance", "viewCount", "date"):
        ordem = "relevance"
    busca = _get_json(SEARCH_URL, {
        "key": key, "part": "snippet", "type": "video", "videoEmbeddable": "true",
        "q": busca.strip() or f"{modelo} review", "regionCode": "BR", "relevanceLanguage": "pt",
        "order": ordem, "maxResults": max(1, min(25, max_results)),
    })
    ids = [it["id"]["videoId"] for it in busca.get("items", []) if it.get("id", {}).get("videoId")]
    if not ids:
        return []
    det = _get_json(VIDEOS_URL, {
        "key": key, "part": "snippet,contentDetails,statistics,status",
        "id": ",".join(ids),
    })
    candidatos = []
    for it in det.get("items", []):
        if it.get("status", {}).get("embeddable") is False:
            continue
        sn, st = it.get("snippet", {}), it.get("statistics", {})
        candidatos.append({
            "youtube_id": it["id"],
            "titulo": sn.get("title", ""),
            "canal": sn.get("channelTitle", ""),
            "canal_id": sn.get("channelId", ""),
            "publicado_em": (sn.get("publishedAt", "") or "")[:10],
            "duracao_s": parse_iso8601_duracao(it.get("contentDetails", {}).get("duration", "")),
            "views": int(st.get("viewCount", 0) or 0),
        })
    return candidatos


def relatorio(modelo: str, key: str, canais: tuple = (), max_results: int = 10,
              ordem: str = "relevance", so_pt: bool = False, busca: str = "") -> dict:
    cands = buscar_candidatos(modelo, key, max_results, ordem, busca)
    if so_pt:
        cands = [c for c in cands if eh_pt(c["titulo"])]
    for c in cands:
        c["score"] = pontuar(c, canais, bonus_pt=2.0 if so_pt else 0.0)
        c["flags"] = flags_clickbait(c["titulo"])
    cands.sort(key=lambda c: c["score"], reverse=True)
    ficha = {}
    if cands:
        top = cands[0]
        ficha = {"youtube_id": top["youtube_id"], "youtube_titulo": top["titulo"],
                 "youtube_canal": top["canal"]}
    return {"modelo": modelo, "candidatos": cands, "sugestao_ficha_top1": ficha}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Sugere reviews em vídeo para aprovação humana.")
    ap.add_argument("--modelo", action="append", required=True, help="Modelo (repita por comparativo).")
    ap.add_argument("--max", type=int, default=10, help="Candidatos por modelo (padrão 10).")
    ap.add_argument("--ordem", default="relevance", choices=["relevance", "viewCount", "date"],
                    help="Ordenação da busca (padrão relevance).")
    ap.add_argument("--pt", action="store_true", help="Só títulos em português, PT primeiro no score.")
    ap.add_argument("--busca", default="", help="Consulta livre (padrão: '<modelo> review').")
    ap.add_argument("--key", default="", help="Chave YouTube Data API v3 (ou env YOUTUBE_API_KEY).")
    ap.add_argument("--canais", default="", help="IDs ou nomes de canais aprovados, separados por vírgula.")
    ap.add_argument("--saida", default="", help="Caminho JSON para salvar o relatório (opcional).")
    args = ap.parse_args(argv)
    key = (args.key or os.getenv("YOUTUBE_API_KEY", "")).strip()
    if not key:
        print("Sem chave: defina YOUTUBE_API_KEY na sessão ou passe --key.\n"
              "Crie grátis em console.cloud.google.com (YouTube Data API v3). "
              "Nunca commite a chave.", file=sys.stderr)
        return 2
    canais = tuple(c.strip() for c in args.canais.split(",") if c.strip())
    tudo = [relatorio(m, key, canais, args.max, args.ordem, args.pt, args.busca) for m in args.modelo]
    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as fh:
            json.dump(tudo, fh, ensure_ascii=False, indent=2)
        print(f"Relatório salvo em {args.saida}")
    for r in tudo:
        print(f"\n== {r['modelo']} ({len(r['candidatos'])} candidatos) ==")
        for i, c in enumerate(r["candidatos"], 1):
            print(f"{i}. [{c['score']}] {c['titulo']} | {c['canal']} | "
                  f"{c['views']} views | {c['duracao_s']}s | {c['youtube_id']}"
                  + (f" | FLAGS: {','.join(c['flags'])}" if c["flags"] else ""))
        if r["sugestao_ficha_top1"]:
            print("Sugestão top1 p/ ficha: " + json.dumps(r["sugestao_ficha_top1"], ensure_ascii=False))
    print("\nCusto estimado: ~100 unidades de cota por modelo (cota grátis: 10.000/dia).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
