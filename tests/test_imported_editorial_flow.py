import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from mkt_flow_p0.editorial_import import processar_artigo_importado
from mkt_flow_p0.editorial_identity import criar_handoff_chatgpt
from mkt_flow_p0.editorial_readiness import avaliar_prontidao_editorial

ROOT=Path(__file__).resolve().parents[1]


def payload():
    return {'source_url':'https://example.org/source','source_name':'Primary source',
        'article':{'titulo_seo':'Documented editorial guide','meta_description':'A documented and attributed guide with practical explanations and clear limits, pending human editorial review before publication.',
            'slug':'documented-editorial-guide','texto_markdown':'## First section\n\n'+('Clear sourced explanation for readers, with no invented experience or claims. '*22)+'\n\n## Comparison\n\n| Option | Purpose |\n|---|---|\n| Example | Explanation |'},
        'research':{'sources':[{'name':'Additional source','url':'https://example.com/additional',
            'facts':['A source documents the explained feature and its limitations.']}]}}


class ImportedEditorialFlowTests(unittest.TestCase):
    def test_real_modules_generate_preview_body_seo_and_pending_diagnostics_without_network(self):
        with tempfile.TemporaryDirectory() as folder, patch('socket.create_connection',side_effect=AssertionError('Unexpected network')):
            result=processar_artigo_importado(payload(),Path(folder)/'version')
            self.assertEqual(set(result['modules_executed']),{'editorial_import','editorial_identity','editorial_core_offline','format','seo','seo_contract_native','editorial_readiness','gate_editorial_pos_ia','adaptador_contrato_editorial','editorial_trace','image_protocol','editorial_substance'})
            self.assertIn('<table>',Path(result['wordpress_body_path']).read_text())
            self.assertIn('noindex,nofollow',Path(result['preview_path']).read_text())
            self.assertFalse(result['wordpress_written']);self.assertFalse(result['provider_called'])
            self.assertFalse(result['publication_authorized'])
            self.assertEqual(result['human_acceptance'],'PENDING')
            self.assertEqual(result['evidence_contract']['veredito'],'BLOQUEADO')
            self.assertIn('imagem_destacada_com_direitos_pendente',result['readiness']['pendencias'])
            trace=json.loads(Path(result['trace_path']).read_text())
            self.assertEqual(trace['events'][0]['status'],'IMPORTED_NO_PROVIDER')
            self.assertEqual(Path(result['preview_path']).stat().st_mode & 0o777,0o600)

    def test_primary_cli_works_with_python_S_and_no_provider_or_wp_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'input.json').write_text(json.dumps(payload()))
            env=dict(os.environ,GROQ_API_KEY='',WP_APP_PASSWORD='',WP_URL='',WP_USER='')
            run=subprocess.run([sys.executable,'-S',str(ROOT/'pipeline_rss.py'),'--import-article',str(p/'input.json'),
                '--handoff-only','--handoff-dir',str(p/'out'),'--genero','guia','--offline'],cwd=folder,env=env,text=True,capture_output=True,check=True)
            summary=json.loads(run.stdout)
            self.assertFalse(summary['provider_called']);self.assertFalse(summary['wordpress_written'])
            self.assertNotIn(payload()['article']['texto_markdown'][:50],run.stdout)
            self.assertFalse((p/'mkt_flow_p0.db').exists())
            self.assertTrue((p/'out/pipeline-report.json').is_file())

    def test_imported_display_title_is_not_duplicated_in_preview_or_wp_body(self):
        value=payload();title=value['article']['titulo_seo']
        value['article']['texto_markdown']='# '+title+'\n\n'+value['article']['texto_markdown']
        with tempfile.TemporaryDirectory() as folder:
            result=processar_artigo_importado(value,Path(folder)/'version')
            self.assertEqual(Path(result['preview_path']).read_text().count('<h1>'),1)
            self.assertNotIn(title,Path(result['wordpress_body_path']).read_text())
            self.assertTrue(Path(result['markdown_path']).read_text().startswith('# '+title))

    def test_source_or_markdown_invalid_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'out'
            for mutate in (lambda p:p.update(source_name=''),lambda p:p['article'].update(texto_markdown='<script>x</script>'+'word '*200)):
                value=payload();mutate(value)
                with self.assertRaises(ValueError):processar_artigo_importado(value,out)
                self.assertFalse(out.exists())

    def test_existing_output_never_overwrites_previous_version(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'out';first=processar_artigo_importado(payload(),p)
            before=Path(first['markdown_path']).read_bytes()
            with self.assertRaises(FileExistsError):processar_artigo_importado(payload(),p)
            self.assertEqual(Path(first['markdown_path']).read_bytes(),before)

    def test_publishing_and_rss_flags_cannot_activate_import_write(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'input.json').write_text(json.dumps(payload()))
            for extra in (['--intent','publish'],['--queue-only'],['--fonte','tecnoblog'],['--featured-media-id','0']):
                result=subprocess.run([sys.executable,'-S',str(ROOT/'pipeline_rss.py'),'--import-article',str(p/'input.json'),
                    '--handoff-only','--handoff-dir',str(p/'out'),*extra],text=True,capture_output=True,cwd=folder)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse((p/'out').exists())

    def test_source_ids_and_procedure_markers_are_not_quantities_but_real_numbers_are(self):
        from mkt_flow_p0.gate_editorial_pos_ia import validar_saida
        source='Abra os ajustes e salve a preferência.'
        markdown='1. Abra os ajustes.\n2. Salve a preferência.\n[Apple](https://support.apple.com/pt-br/104995)'
        self.assertEqual(validar_saida(source,markdown)['veredito'],'SEM_ALERTAS')
        for extra in (' Custa R$ 199.', ' Funciona em 100 aparelhos.', ' [200](https://example.org/104995)'):
            with self.subTest(extra=extra):
                self.assertIn('numeros_sem_correspondencia_na_fonte',validar_saida(source,markdown+extra)['motivos'])

    def test_word_count_reference_does_not_determine_editorial_eligibility(self):
        p=payload();p['article']['texto_markdown']='## First\n\nShort documented guide.\n\n## Second\n\nUseful explanation.'
        handoff=criar_handoff_chatgpt(p['article'],url_fonte=p['source_url'],fonte_nome=p['source_name'],contexto_complementar=p['research'])
        links=['https://conexotech.com.br/a/','https://conexotech.com.br/b/','https://conexotech.com.br/c/']
        html='<h2>A</h2><h2>B</h2>'+''.join('<a href="'+u+'">link</a>' for u in links)
        result=avaliar_prontidao_editorial(handoff,html=html,genero='guia',featured_media_id=1,direitos_imagem_confirmados=True,verified_related_urls=links)
        self.assertNotIn('texto_abaixo_da_referencia_do_genero',result['pendencias'])
        self.assertIn('texto_abaixo_da_referencia_do_genero',result['avisos'])
        self.assertEqual(result['status'],'ENRIQUECIMENTO_PENDENTE')
        self.assertIn('persona_editorial_nao_aplicada',result['pendencias'])
        self.assertFalse(result['pronto_para_publicar'])


if __name__=='__main__':unittest.main()
