import re
class TaskRouter:
    @staticmethod
    def route(msg):
        msg = msg.lower()
        if re.search(r"roi|retorno|cpc|conversão", msg): return "roi"
        if re.search(r"link|tracking|valide|validar", msg): return "link_validation"
        if re.search(r"seo|geo|estratégia|posicionamento", msg): return "geo"
        if re.search(r"landing|página|html", msg): return "landing_page"
        if re.search(r"instagram|legenda|post|tiktok|facebook|social", msg): return "social"
        if re.search(r"ab test|teste a/b|variação", msg): return "ab_test"
        if re.search(r"artigo|review|blog|conteúdo longo", msg): return "article"
        return "default"