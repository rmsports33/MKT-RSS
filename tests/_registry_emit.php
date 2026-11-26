<?php
/** Emite envelope {record,signature} para o teste cruzado PHP → Python. */
define('ABSPATH', __DIR__ . '/../');
define('CONEXO_REVIEW_REGISTRY_KEY', str_repeat('r', 40));
define('CONEXO_EDITORIAL_GATE_KEY', str_repeat('c', 40));
define('CXEG_OWNER_REVIEWER_ID', 3);

$GLOBALS['reg_options'] = array();
$GLOBALS['reg_posts'] = array();
$GLOBALS['reg_current_user'] = 3;

class WP_Error { public $code, $msg; public function __construct($c,$m=''){$this->code=$c;$this->msg=$m;} public function get_error_code(){return $this->code;} }
class WP_REST_Response { public $data; public function __construct($d){$this->data=$d;} public function header($k,$v){} }
class WP_Post { public $ID,$post_type,$post_status,$post_title,$post_content,$post_excerpt,$post_name,$post_author,$post_modified; public function __construct($d){foreach($d as $k=>$v)$this->{$k}=$v;} }

function current_user_can($c){return true;}
function get_current_user_id(){return $GLOBALS['reg_current_user'];}
function cxeg_owner_current(){return false;}
function get_option($k,$d=false){return isset($GLOBALS['reg_options'][$k])?$GLOBALS['reg_options'][$k]:$d;}
function update_option($k,$v,$a=false){$GLOBALS['reg_options'][$k]=$v;return true;}
function rest_url($p){return 'https://conexotech.com.br/wp-json/'.$p;}
function wp_extract_urls($s){return array();}
function register_rest_route($n,$r,$a){}
function add_action($h,$c,$p=10){}
function cxeg_protected($id){return true;}
function get_post($id){return isset($GLOBALS['reg_posts'][$id])?$GLOBALS['reg_posts'][$id]:null;}
function wp_get_post_categories($id){return array(10);}
function get_post_thumbnail_id($id){return 12;}
function cxeg_snapshot($id){$p=get_post($id);if(!$p)return null;return array('ID'=>(int)$p->ID,'post_type'=>$p->post_type,'post_status'=>$p->post_status,'post_title'=>$p->post_title,'post_content'=>$p->post_content,'post_excerpt'=>$p->post_excerpt,'post_name'=>$p->post_name,'post_author'=>(int)$p->post_author,'post_category'=>array(10),'meta_input'=>array('_thumbnail_id'=>12));}
function cxeg_hash($v){return hash('sha256',json_encode($v,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_LINE_TERMINATORS));}
function cxeg_quality_valid($id){$q=get_option('cxeg_quality_'.$id,false);if(!is_array($q))return false;$s=cxeg_snapshot($id);return $s&&hash_equals((string)$q['snapshot_sha256'],cxeg_hash($s));}
function cxeg_review_identity_valid($r,$s,$m='independent'){return is_int($r)&&$r>0&&$r!==(int)$s['post_author'];}
function cxeg_sort($v){if(!is_array($v))return $v;if(array_keys($v)!==range(0,count($v)-1))ksort($v);foreach($v as $k=>$i)$v[$k]=cxeg_sort($i);return $v;}

require_once __DIR__ . '/../mkt_flow_p0/gate_v1_registry_route.php';

$id = 9906;
$GLOBALS['reg_posts'][$id] = new WP_Post(array('ID'=>$id,'post_type'=>'post','post_status'=>'draft',
    'post_title'=>'Artigo','post_content'=>'<p>Texto</p>','post_excerpt'=>'Resumo',
    'post_name'=>'artigo','post_author'=>4,'post_modified'=>'2026-11-26 10:00:00'));
$sha = cxeg_hash(cxeg_snapshot($id));
$checks = array('versao'=>array('estado'=>'VERIFICADO','evidencia'=>array('https://example.org/evidencia')),
    'fontes'=>array('estado'=>'VERIFICADO','evidencia'=>array('https://example.org/evidencia')));
$GLOBALS['reg_options']['cxeg_quality_'.$id] = array('schema'=>'conexo-article-quality/1','post_id'=>$id,
    'snapshot_sha256'=>$sha,'veredito'=>'APTO_PARA_APROVACAO','checks'=>$checks,
    'reviewer_id'=>7,'review_mode'=>'independent');
$GLOBALS['reg_options']['cxeg_review_'.$id] = array('decision'=>'approved','reviewer_id'=>7,
    'snapshot_sha256'=>$sha,'reviewed_at'=>time(),'review_mode'=>'independent');

class Req implements ArrayAccess {
    public $id=9906;
    public function get_param($k){return null;}
    public function offsetExists($o):bool{return $o==='id';}
    public function offsetGet($o):mixed{return $this->id;}
    public function offsetSet($o,$v):void{}
    public function offsetUnset($o):void{}
}
$resp = cxeg_registry_read(new Req());
echo json_encode($resp->data, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE), "\n";
