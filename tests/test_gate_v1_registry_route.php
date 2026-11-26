<?php
/** Testes isolados da rota de registro assinado do Gate V1. Sem WordPress. */
define('ABSPATH', __DIR__ . '/../../');
define('CONEXO_REVIEW_REGISTRY_KEY', str_repeat('r', 40));

$GLOBALS['reg_options'] = array();
$GLOBALS['reg_key'] = str_repeat('r', 40);
$GLOBALS['reg_current_user'] = 3;

class WP_Error {
    public $code, $msg, $data;
    public function __construct($c, $m = '', $d = array()) { $this->code = $c; $this->msg = $m; $this->data = $d; }
    public function get_error_code() { return $this->code; }
    public function get_error_message() { return $this->msg; }
}
class WP_REST_Response {
    public $data, $headers = array();
    public function __construct($d) { $this->data = $d; }
    public function header($k, $v) { $this->headers[$k] = $v; }
}
class WP_Post {
    public $ID, $post_type, $post_status, $post_title, $post_content, $post_excerpt,
        $post_name, $post_author, $post_modified;
    public function __construct($d = array()) { foreach ($d as $k => $v) $this->{$k} = $v; }
}

function current_user_can($c) { return true; }
function get_current_user_id() { return $GLOBALS['reg_current_user']; }
function get_option($k, $d = false) { return isset($GLOBALS['reg_options'][$k]) ? $GLOBALS['reg_options'][$k] : $d; }
function update_option($k, $v, $a = false) { $GLOBALS['reg_options'][$k] = $v; return true; }
function rest_url($p) { return 'https://conexotech.com.br/wp-json/' . $p; }
function wp_extract_urls($s) { preg_match_all('#https?://[^\s"<>\)]+#i', $s, $m); return $m[0]; }
function register_rest_route($ns, $route, $args) { $GLOBALS['reg_route'] = array($ns, $route, $args); }
function add_action($h, $c, $p = 10) {
    $GLOBALS['reg_actions'][$h][] = array($c, $p);
    // Executa imediatamente em ambiente de teste (sem WordPress).
    if ($h === 'rest_api_init') { call_user_func($c); }
}
function cxeg_protected($id) { return true; }
function cxeg_snapshot($id) {
    $p = isset($GLOBALS['reg_posts'][$id]) ? $GLOBALS['reg_posts'][$id] : null;
    if (!$p) return null;
    return array('ID' => (int)$p->ID, 'post_type' => $p->post_type,
        'post_status' => $p->post_status, 'post_title' => $p->post_title,
        'post_content' => $p->post_content, 'post_excerpt' => $p->post_excerpt,
        'post_name' => $p->post_name, 'post_author' => (int)$p->post_author,
        'post_category' => array(10), 'meta_input' => array('_thumbnail_id' => 12));
}
function cxeg_hash($v) { return hash('sha256', json_encode($v, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_LINE_TERMINATORS)); }
function cxeg_quality_valid($id) {
    $q = get_option('cxeg_quality_' . $id, false);
    if (!is_array($q)) return false;
    $s = cxeg_snapshot($id);
    return $s && hash_equals((string)$q['snapshot_sha256'], cxeg_hash($s));
}
function cxeg_sort($v) {
    if (!is_array($v)) return $v;
    if (array_keys($v) !== range(0, count($v) - 1)) ksort($v);
    foreach ($v as $k => $i) $v[$k] = cxeg_sort($i);
    return $v;
}

$_SERVER['REQUEST_METHOD'] = 'GET';
require_once __DIR__ . '/../mkt_flow_p0/gate_v1_registry_route.php';

class RegTest {
    public $pass = 0, $fail = 0;
    function ok($c, $n) { if ($c) { $this->pass++; echo "PASS: $n\n"; } else { $this->fail++; echo "FAIL: $n\n"; } }

    function setup($id = 9906) {
        $GLOBALS['reg_posts'][$id] = new WP_Post(array(
            'ID' => $id, 'post_type' => 'post', 'post_status' => 'draft',
            'post_title' => 'Artigo', 'post_content' => '<p>Texto https://example.org/fonte</p>',
            'post_excerpt' => 'Resumo', 'post_name' => 'artigo', 'post_author' => 4,
            'post_modified' => '2026-11-26 10:00:00'));
        $sha = cxeg_hash(cxeg_snapshot($id));
        $GLOBALS['reg_options']['cxeg_quality_' . $id] = array(
            'schema' => 'conexo-article-quality/1', 'post_id' => $id,
            'snapshot_sha256' => $sha, 'veredito' => 'APTO_PARA_APROVACAO',
            'checks' => array('fontes' => array('estado' => 'VERIFICADO',
                'evidencia' => array('https://example.org/evidencia'))),
            'reviewer_id' => 7);
        $GLOBALS['reg_options']['cxeg_review_' . $id] = array(
            'decision' => 'approved', 'reviewer_id' => 7,
            'snapshot_sha256' => $sha, 'reviewed_at' => time());
        return $sha;
    }

    function run() {
        $sha = $this->setup();

        // Rota registrada
        $this->ok(isset($GLOBALS['reg_route']) && $GLOBALS['reg_route'][0] === 'conexo/v1', 'Rota REST registrada');
        $this->ok(strpos($GLOBALS['reg_route'][1], 'registry') !== false, 'Rota registry');
        $cb = $GLOBALS['reg_route'][2];
        $this->ok($cb['methods'] === 'GET', 'Somente GET');
        $this->ok(is_callable($cb['permission_callback']), 'permission_callback presente');

        // Chave separada
        $this->ok(cxeg_registry_key() === $GLOBALS['reg_key'], 'Chave separada disponível');

        // Registro assinado
        $req = new class implements ArrayAccess {
            public $id = 9906;
            public function offsetExists($o): bool { return $o === 'id'; }
            public function offsetGet($o): mixed { return $this->id; }
            public function offsetSet($o, $v): void { $this->id = $v; }
            public function offsetUnset($o): void {}
        };
        $resp = cxeg_registry_read($req);
        $this->ok($resp instanceof WP_REST_Response, 'Resposta REST');
        $data = $resp->data;
        $this->ok(isset($data['record']) && isset($data['signature']), 'Envelope {record,signature}');
        $rec = $data['record'];
        $this->ok($rec['decision'] === 'APROVADO', 'decision Aprovado');
        $this->ok($rec['status'] === 'FINAL', 'status FINAL');
        $this->ok($rec['independent'] === true, 'independent true');
        $this->ok($rec['revoked'] === false, 'revoked false');
        $this->ok($rec['draft_sha256'] === $sha, 'hash vinculado à versão');
        $this->ok($rec['reviewer_id'] === '7', 'reviewer_id');
        $this->ok(in_array('https://example.org/evidencia', $rec['evidence_refs'], true), 'evidence_refs');
        $this->ok(strpos($rec['review_record_url'], '/registry/9906') !== false, 'review_record_url');

        // HMAC com chave separada
        $expected = hash_hmac('sha256', cxeg_registry_canonical($rec), $GLOBALS['reg_key']);
        $this->ok(hash_equals($data['signature'], $expected), 'HMAC válido com chave separada');

        // Sem parecer vigente
        unset($GLOBALS['reg_options']['cxeg_quality_9906']);
        $err = cxeg_registry_read($req);
        $this->ok($err instanceof WP_Error && $err->get_error_code() === 'cxeg_registry_no_review', 'Sem parecer → 404');

        echo "\nPASS: {$this->pass} | FAIL: {$this->fail}\n";
        exit($this->fail > 0 ? 1 : 0);
    }
}
(new RegTest())->run();
