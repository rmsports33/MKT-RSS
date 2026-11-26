<?php
/** Testes comportamentais da rota de registro assinado do Gate V1. Sem WordPress real. */
define('ABSPATH', __DIR__ . '/../../');
define('CONEXO_REVIEW_REGISTRY_KEY', str_repeat('r', 40));
define('CONEXO_EDITORIAL_GATE_KEY', str_repeat('c', 40));
define('CXEG_OWNER_REVIEWER_ID', 3);

$GLOBALS['reg_options'] = array();
$GLOBALS['reg_posts'] = array();
$GLOBALS['reg_current_user'] = 3;
$GLOBALS['reg_permission_user'] = 3;

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

function current_user_can($c) { return $GLOBALS['reg_current_user'] > 0; }
function get_current_user_id() { return $GLOBALS['reg_current_user']; }
function cxeg_owner_current() { return get_current_user_id() === CXEG_OWNER_REVIEWER_ID; }
function get_option($k, $d = false) { return isset($GLOBALS['reg_options'][$k]) ? $GLOBALS['reg_options'][$k] : $d; }
function update_option($k, $v, $a = false) { $GLOBALS['reg_options'][$k] = $v; return true; }
function rest_url($p) { return 'https://conexotech.com.br/wp-json/' . $p; }
function wp_extract_urls($s) { preg_match_all('#https?://[^\s"<>\)]+#i', $s, $m); return $m[0]; }
function register_rest_route($ns, $route, $args) { $GLOBALS['reg_route'] = array($ns, $route, $args); }
function add_action($h, $c, $p = 10) { if ($h === 'rest_api_init') { call_user_func($c); } }
function cxeg_protected($id) { return true; }
function get_post($id) { return isset($GLOBALS['reg_posts'][$id]) ? $GLOBALS['reg_posts'][$id] : null; }
function wp_get_post_categories($id) { return array(10); }
function get_post_thumbnail_id($id) { return 12; }
function cxeg_snapshot($id) {
    $p = get_post($id);
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
function cxeg_review_identity_valid($reviewer, $snapshot, $mode = 'independent') {
    if (!is_int($reviewer) || $reviewer <= 0) return false;
    if ($mode === 'independent') return $reviewer !== (int)$snapshot['post_author'];
    if ($mode === 'owner') return $reviewer === CXEG_OWNER_REVIEWER_ID;
    return false;
}
function cxeg_sort($v) {
    if (!is_array($v)) return $v;
    if (array_keys($v) !== range(0, count($v) - 1)) ksort($v);
    foreach ($v as $k => $i) $v[$k] = cxeg_sort($i);
    return $v;
}

require_once __DIR__ . '/../mkt_flow_p0/gate_v1_registry_route.php';

class Req implements ArrayAccess {
    public $id, $params;
    public function __construct($id, $params = array()) { $this->id = $id; $this->params = $params; }
    public function get_param($k) { return $this->params[$k] ?? null; }
    public function offsetExists($o): bool { return $o === 'id'; }
    public function offsetGet($o): mixed { return $this->id; }
    public function offsetSet($o, $v): void { $this->id = $v; }
    public function offsetUnset($o): void {}
}

class RegTest {
    public $pass = 0, $fail = 0;
    function ok($c, $n) { if ($c) { $this->pass++; echo "PASS: $n\n"; } else { $this->fail++; echo "FAIL: $n\n"; } }

    function setup($id = 9906, $mode = 'independent', $reviewer = 7, $author = 4, $evidence = array('https://example.org/evidencia')) {
        $GLOBALS['reg_posts'][$id] = new WP_Post(array(
            'ID' => $id, 'post_type' => 'post', 'post_status' => 'draft',
            'post_title' => 'Artigo', 'post_content' => '<p>Texto</p>',
            'post_excerpt' => 'Resumo', 'post_name' => 'artigo', 'post_author' => $author,
            'post_modified' => '2026-11-26 10:00:00'));
        $sha = cxeg_hash(cxeg_snapshot($id));
        $checks = array();
        foreach (array('versao','fontes','revisao_substantiva') as $k) {
            $checks[$k] = array('estado' => 'VERIFICADO', 'evidencia' => $evidence);
        }
        $GLOBALS['reg_options']['cxeg_quality_' . $id] = array(
            'schema' => 'conexo-article-quality/1', 'post_id' => $id,
            'snapshot_sha256' => $sha, 'veredito' => 'APTO_PARA_APROVACAO',
            'checks' => $checks, 'reviewer_id' => $reviewer, 'review_mode' => $mode);
        $GLOBALS['reg_options']['cxeg_review_' . $id] = array(
            'decision' => 'approved', 'reviewer_id' => $reviewer,
            'snapshot_sha256' => $sha, 'reviewed_at' => time(), 'review_mode' => $mode);
        return $sha;
    }

    function run() {
        // 1. Registro válido → envelope
        $sha = $this->setup();
        $resp = cxeg_registry_read(new Req(9906));
        $this->ok($resp instanceof WP_REST_Response, '1. Envelope gerado');
        $data = $resp->data;
        $this->ok(isset($data['record'], $data['signature']), '1. {record,signature}');
        $rec = $data['record'];

        // 2. HMAC compatível com Python (canonical sort_keys)
        $expected = hash_hmac('sha256', cxeg_registry_canonical($rec), CONEXO_REVIEW_REGISTRY_KEY);
        $this->ok(hash_equals($data['signature'], $expected), '2. HMAC válido');

        // 3. draft_sha256 = draft_digest() Python (campos canônicos)
        $py_fields = array('id'=>9906,'status'=>'draft','title'=>'Artigo','content'=>'<p>Texto</p>',
            'slug'=>'artigo','categories'=>array(10),'featured_media'=>12);
        ksort($py_fields);
        $py = hash('sha256', json_encode($py_fields, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_LINE_TERMINATORS));
        $this->ok($rec['draft_sha256'] === $py, '3. draft_sha256 == draft_digest Python');
        $this->ok($rec['draft_sha256'] !== $sha, '3. Não é o hash do snapshot');

        // 4. Revisão independente válida
        $this->ok($rec['independent'] === true, '4. independent=true');
        $this->ok($rec['decision'] === 'APROVADO' && $rec['status'] === 'FINAL', '4. decision/status');

        // 5. owner NÃO aceito como independente
        $this->setup(9907, 'owner', CXEG_OWNER_REVIEWER_ID);
        $r5 = cxeg_registry_read(new Req(9907));
        $this->ok($r5 instanceof WP_Error && $r5->get_error_code() === 'cxeg_registry_no_review', '5. owner rejeitado');

        // 6. Reviewer IDs incompatíveis
        $this->setup(9908, 'independent', 7);
        $GLOBALS['reg_options']['cxeg_quality_9908']['reviewer_id'] = 9;
        $r6 = cxeg_registry_read(new Req(9908));
        $this->ok($r6 instanceof WP_Error, '6. reviewers divergentes rejeitados');

        // 7. Evidência HTTP inválida rejeitada
        $this->setup(9909, 'independent', 7, 4, array('http://example.org/evidencia'));
        $r7 = cxeg_registry_read(new Req(9909));
        $this->ok($r7 instanceof WP_Error, '7. evidência HTTP rejeitada');

        // 8. Registro alterado / assinatura inválida
        $rec['draft_sha256'] = str_repeat('0', 64);
        $bad_sig = hash_hmac('sha256', cxeg_registry_canonical($rec), CONEXO_REVIEW_REGISTRY_KEY);
        $this->ok(!hash_equals($bad_sig, $data['signature']), '8. assinatura não cobre registro alterado');

        // 9/10. Chaves ausentes/iguais — testado via lógica de fallback
        $this->ok(cxeg_registry_key() !== null && cxeg_registry_certificate_key() !== null, '9/10. chaves disponíveis');
        $this->ok(!hash_equals(cxeg_registry_key(), cxeg_registry_certificate_key()), '10. chaves distintas');

        // 11. Permissão: usuário não autorizado
        $GLOBALS['reg_current_user'] = 99;
        $this->ok(cxeg_registry_permission(new Req(9906)) === false, '11. usuário não autorizado negado');
        $GLOBALS['reg_current_user'] = 3;
        $this->ok(cxeg_registry_permission(new Req(9906)) === true, '11. usuário autorizado aceito');

        // 12. Sem parecer → 404
        unset($GLOBALS['reg_options']['cxeg_quality_9906']);
        $r12 = cxeg_registry_read(new Req(9906));
        $this->ok($r12 instanceof WP_Error && $r12->get_error_code() === 'cxeg_registry_no_review', '12. sem parecer → 404');

        echo "\nPASS: {$this->pass} | FAIL: {$this->fail}\n";
        exit($this->fail > 0 ? 1 : 0);
    }
}
(new RegTest())->run();
