import tiktoken, json
class ContextCompiler:
    def __init__(self, token_budget=2000):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.token_budget = token_budget
    def compile(self, task, data):
        keys = {"social": ["nome", "preco", "url"], "article": ["nome", "preco", "url", "descricao"]}.get(task, ["nome", "url"])
        filtered = {k: data.get(k) for k in keys if k in data}
        if len(self.encoder.encode(json.dumps(filtered))) > self.token_budget:
            filtered = {k: v[:200] if isinstance(v, str) else v for k, v in filtered.items()}
        return filtered