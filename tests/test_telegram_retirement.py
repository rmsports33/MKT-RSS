"""Offline guard: removed Telegram transports must not return."""
import ast,importlib.util,socket,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
RETIRED=('admin/bot.py','admin/bot-requirements.txt','admin/Dockerfile','fly.toml','.github/workflows/bot-poll.yml')

def violations(root):
    errors=[p for p in RETIRED if (root/p).exists()]
    for path in (root/'admin').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            if isinstance(node,ast.ImportFrom) and (node.module or '').split('.')[0]=='telegram':errors.append(str(path))
            if isinstance(node,ast.Import) and any(x.name.split('.')[0]=='telegram' for x in node.names):errors.append(str(path))
    return errors

class RetirementTests(unittest.TestCase):
    def test_no_transport_or_sdk(self):self.assertEqual(violations(ROOT),[])

    def test_mutation_reactivating_bot_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'admin').mkdir()
            self.assertEqual(violations(root),[])
            (root/'admin/bot.py').write_text('print("retired")')
            self.assertIn('admin/bot.py',violations(root))

    def test_mutation_reintroducing_sdk_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'admin').mkdir()
            (root/'admin/link.py').write_text('from telegram import Update')
            self.assertTrue(violations(root))

    def test_affiliate_helpers_preserved_offline(self):
        sys.path.insert(0,str(ROOT/'admin'))
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            import linkflow,linkauto
            self.assertEqual(linkflow.norm_url('amazon.com.br/produto'),'https://amazon.com.br/produto')
            self.assertIsNone(linkflow.norm_url('not a URL'))
            self.assertEqual(linkauto.detecta_loja('https://www.amazon.com.br/dp/test'),'Amazon')
            self.assertIsNone(linkauto.detecta_loja('https://unknown.example/item'))
            models=['Tribit Stormbox Blast 1','Tribit Stormbox Blast 2']
            self.assertEqual(linkauto.casa_modelo('Tribit StormBox Blast 2 Caixa 90W',models)['modelo'],models[1])
            self.assertEqual(linkauto.parse_linhas(linkauto.msg_confirm('https://example.com/x','Modelo','Amazon'))['url'],'https://example.com/x')

if __name__=='__main__':unittest.main(verbosity=2)
