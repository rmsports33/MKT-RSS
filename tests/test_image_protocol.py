import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from mkt_flow_p0.image_protocol import plan_image,validate_resource,prepare_assets,validate_prepared_manifest


class ImageProtocolTests(unittest.TestCase):
    def test_protocol_runs_without_provider_or_image_key(self):
        plan=plan_image('Teclado do iPhone')
        self.assertEqual(plan['status'],'CANDIDATE_LICENSE_DOCUMENTED')
        self.assertEqual(plan['resource']['license'],'CC0-1.0')
        self.assertFalse(plan['network_called'])
        self.assertEqual(plan_image('unrelated title')['status'],'RESEARCH_REQUIRED_OFFLINE')

    def test_unlicensed_or_missing_credit_is_refused(self):
        resource=plan_image('teclado do iPhone')['resource']
        for key,value in (('license','unknown'),('author',''),('license_url','https://example.org/not-license')):
            raw=copy.deepcopy(resource);raw[key]=value
            with self.assertRaises(ValueError):validate_resource(raw)

    def test_editable_delivery_keeps_credit_without_duplicate_featured_image(self):
        from mkt_flow_p0.wordpress_blocks import serialize_blocks
        resource=plan_image('teclado do iPhone')['resource']
        body='<figure><picture><img src="assets/cover-desktop.jpg" alt="photo"></picture><figcaption>credit</figcaption></figure><p>Text</p><h2>Section</h2><ol><li>Step</li></ol><table><tr><td>Cell</td></tr></table>'
        result=serialize_blocks(body,featured_resource=resource)
        self.assertIn('wp:paragraph',result);self.assertIn('wp:table',result)
        self.assertIn('wp:list-item',result);self.assertIn('Karl432',result)
        self.assertNotIn('<img',result)

    def test_real_image_processing_and_tampered_asset_or_missing_visual_refused(self):
        from PIL import Image
        resource=plan_image('teclado do iPhone')['resource']
        raw=io.BytesIO();Image.new('RGB',(1800,1000),'navy').save(raw,format='JPEG')
        result=prepare_assets(resource,raw.getvalue())
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest={'resource':resource,'assets':{},'visual_review':'ASSISTED_VISUAL_CHECK_COMPLETED'}
            for name,item in result['assets'].items():
                path=root/(name+'.jpg');path.write_bytes(item['bytes'])
                manifest['assets'][name]={'path':path.name,'sha256':item['sha256'],'width':item['width'],'height':item['height']}
                with Image.open(path) as image:self.assertEqual(image.size,(item['width'],item['height']))
            validate_prepared_manifest(manifest,base_dir=root)
            from mkt_flow_p0.editorial_import import processar_artigo_importado
            from test_imported_editorial_flow import payload
            value=payload();result_flow=processar_artigo_importado(value,root/'article',image_manifest=manifest,image_base=root)
            preview=Path(result_flow['preview_path']).read_text()
            self.assertIn('<picture>',preview);self.assertIn('assets/cover-mobile.jpg',preview)
            self.assertNotEqual(result_flow['version_sha256'],'')
            self.assertNotEqual(result_flow['image_research'],'NOT_RUN')
            manifest['visual_review']='PENDING'
            with self.assertRaises(ValueError):validate_prepared_manifest(manifest,base_dir=root)
            manifest['visual_review']='ASSISTED_VISUAL_CHECK_COMPLETED';(root/'desktop.jpg').write_bytes(b'tampered')
            with self.assertRaises(ValueError):validate_prepared_manifest(manifest,base_dir=root)


if __name__=='__main__':unittest.main()
