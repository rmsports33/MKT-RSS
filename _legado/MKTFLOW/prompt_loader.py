from pathlib import Path
import os

BASE_DIR = Path(__file__).parent / "prompts"

DEFAULT_CORE = """Você é o Mick, especialista em marketing digital. Seja direto e objetivo.
Sempre inclua o disclosure (#ad #linkdeafiliado) em conteúdos promocionais.
Nunca invente dados ou faça promessas garantidas.
"""

DEFAULT_OUTPUT = """# FORMATO DE SAÍDA
Retorne APENAS um JSON válido com os campos: decision, content, disclosure, reason_code, metadata.
"""

DEFAULT_MODULE = """# INSTRUÇÕES ESPECÍFICAS
Responda com clareza e objetividade, mantendo o tom profissional.
"""

def _ensure_file(path: Path, content: str):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

def ensure_prompts_exist():
    """Cria os arquivos de prompt padrão se não existirem."""
    for lang in ["pt", "es", "en"]:
        lang_path = BASE_DIR / lang
        _ensure_file(lang_path / "core.md", DEFAULT_CORE)
        _ensure_file(lang_path / "output.md", DEFAULT_OUTPUT)
        for module in ["social", "geo", "roi", "landing_page", "ab_test", "article", "default"]:
            _ensure_file(lang_path / "modules" / f"{module}.md", DEFAULT_MODULE)

def load_prompt(task: str, lang: str = "pt", force_full_mode: bool = False) -> str:
    """Carrega o prompt adequado para a tarefa."""
    ensure_prompts_exist()
    lang_path = BASE_DIR / lang
    if not lang_path.exists():
        lang_path = BASE_DIR / "pt"
    
    core = (lang_path / "core.md").read_text(encoding="utf-8")
    output = (lang_path / "output.md").read_text(encoding="utf-8")
    
    module_path = lang_path / "modules" / f"{task}.md"
    if module_path.exists():
        module = module_path.read_text(encoding="utf-8")
    else:
        module = (lang_path / "modules" / "default.md").read_text(encoding="utf-8")
    
    return f"{core}\n\n{output}\n\n{module}"