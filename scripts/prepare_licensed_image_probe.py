"""One publicly licensed image; no article, credentials, AI or WP in logs."""
import base64
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mkt_flow_p0.image_protocol import plan_image,prepare_assets
from mkt_flow_p0.image_handler import baixar_imagem
plan=plan_image('teclado do iPhone')
resource=plan['resource']
image=baixar_imagem(resource['image_url'],timeout=8)
if 'bytes' not in image:raise SystemExit('BLOCKED: LICENSED_IMAGE_DOWNLOAD_FAILED')
prepared=prepare_assets(resource,image['bytes'])
result={'schema':'conexo-licensed-image-preparation/1','resource':prepared['resource'],
        'original_sha256':prepared['original_sha256'],'assets':{}}
for name,item in prepared['assets'].items():
 result['assets'][name]={k:v for k,v in item.items() if k!='bytes'}
 result['assets'][name]['base64']=base64.b64encode(item['bytes']).decode()
# Public CC0 image bytes, never private article content or credentials.
print(json.dumps(result,sort_keys=True))
