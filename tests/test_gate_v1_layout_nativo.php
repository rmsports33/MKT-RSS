<?php
/**
 * Testes PHP isolados do layout nativo do Gate V1.
 * Usa mocks das funções nativas, sem WordPress, sem produção.
 */
define('CXGV1NAT_TEST_MODE', true);
define('ABSPATH', __DIR__ . '/../../');

// Mocks do WordPress e do Gate V1
$GLOBALS['nat_posts'] = array();
$GLOBALS['nat_options'] = array();
$GLOBALS['nat_owner'] = 3;

class WP_Post {
    public $ID, $post_type, $post_status, $post_title, $post_content,
        $post_excerpt, $post_name, $post_author, $post_modified;
    public function __construct($d = array()) { foreach ($d as $k => $v) $this->{$k} = $v; }
}
class WP_Error {
    private $code, $msg;
    public function __construct($c, $m = '') { $this->code = $c; $this->msg = $m; }
    public function get_error_code() { return $this->code; }
    public function get_error_message() { return $this->msg; }
}

function get_current_user_id() { return $GLOBALS['nat_owner']; }
function current_user_can($c) { return true; }
function cxeg_owner_current() { return get_current_user_id() === $GLOBALS['nat_owner']; }
function get_post($id = null) { return isset($GLOBALS['nat_posts'][(int)$id]) ? $GLOBALS['nat_posts'][(int)$id] : null; }
function get_post_thumbnail_id($id) { return 0; }
function wp_get_attachment_url($id) { return ''; }
function get_post_meta($id, $k = '', $s = false) { return ''; }
function wp_get_post_categories($id) { return array(); }
function get_category($id) { return null; }
function wp_strip_all_tags($s) { return strip_tags($s); }
function home_url() { return 'https://conexotech.com.br'; }
function wp_json_encode($d, $f = 0) { return json_encode($d, $f); }
function get_option($k, $d = false) { return isset($GLOBALS['nat_options'][$k]) ? $GLOBALS['nat_options'][$k] : $d; }
function update_option($k, $v, $a = false) { $GLOBALS['nat_options'][$k] = $v; return true; }
function is_wp_error($v) { return $v instanceof WP_Error; }
function esc_attr($s) { return htmlspecialchars($s, ENT_QUOTES); }
function esc_html($s) { return htmlspecialchars($s, ENT_QUOTES); }
function sanitize_key($s) { return $s; }
function wp_unslash($s) { return $s; }
function esc_url_raw($s) { return $s; }
function rest_url($s) { return 'https://conexotech.com.br/wp-json/' . $s; }
function wp_create_nonce($s) { return 'nonce_teste'; }
function plugins_url($p, $f) { return 'https://conexotech.com.br/wp-content/plugins/' . $p; }
function add_action($a, $b) {}
function wp_enqueue_style() {}
function wp_enqueue_script() {}
function wp_localize_script() {}

function cxeg_snapshot($id) {
    $p = get_post($id);
    if (!$p) return null;
    return array('ID' => (int)$p->ID, 'post_type' => $p->post_type,
        'post_status' => $p->post_status, 'post_title' => $p->post_title,
        'post_content' => $p->post_content, 'post_excerpt' => $p->post_excerpt,
        'post_name' => $p->post_name, 'post_author' => (int)$p->post_author,
        'post_category' => array(), 'meta_input' => array('_thumbnail_id' => 0));
}
function cxeg_hash($v) { return hash('sha256', json_encode($v, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)); }
function cxgna_draft_readiness($id) { return array(); }
function cxgna_eligible_drafts($limit = 5) { return array_values($GLOBALS['nat_posts']); }
function cxeg_reviewed_seo_valid($seo, $snap) { return is_array($seo) && isset($seo['title']) && $seo['title'] !== ''; }
function cxeg_quality_required_checks() { return array('versao', 'titulo', 'categoria', 'capa', 'licenca_imagem', 'fontes', 'alegacoes', 'links_internos', 'seo', 'html', 'revisao_substantiva', 'visual_390', 'visual_1440'); }
function cxeg_owner_approve($id, $hash, $seo, $checks, $confirmed, $mode) {
    $GLOBALS['nat_options']['cxeg_review_' . $id] = array('decision' => 'approved', 'version_sha256' => $hash, 'review_mode' => 'owner');
    return array('approved' => true, 'version_sha256' => $hash);
}
function cxq_process_approved_intent($id, $mode) { return array('id' => $id, 'status' => $mode); }

require_once __DIR__ . '/../mkt_flow_p0/gate_v1_layout_nativo.php';

class NatTest {
    public $pass = 0, $fail = 0;
    function ok($c, $n) { if ($c) { $this->pass++; echo "PASS: $n\n"; } else { $this->fail++; echo "FAIL: $n\n"; } }

    function run() {
        $GLOBALS['nat_posts'][9900] = new WP_Post(array(
            'ID' => 9900, 'post_type' => 'post', 'post_status' => 'draft',
            'post_title' => 'Teste Layout Nativo', 'post_content' => '<p>Conteúdo</p>',
            'post_excerpt' => 'Resumo suficiente para o SEO do artigo de teste.',
            'post_name' => 'teste-layout-nativo', 'post_author' => 4,
            'post_modified' => '2026-11-26 10:00:00'));

        // Lista
        $list = cxgv1nat_list_drafts(5);
        $this->ok(isset($list['items']) && count($list['items']) === 1, 'Lista de artigos nativa');
        $this->ok($list['items'][0]['title'] === 'Teste Layout Nativo', 'Título na lista');
        $this->ok($list['items'][0]['status'] === 'ready', 'Status pronto');

        // Detalhe
        $hash = cxeg_hash(cxeg_snapshot(9900));
        $d = cxgv1nat_get_detail(9900);
        $this->ok($d['id'] === 9900, 'Detalhe do artigo');
        $this->ok($d['snapshot_sha256'] === $hash, 'Hash do snapshot');

        // Aprovação (modo hold não publica)
        $r = cxgv1nat_approve(9900, $hash, 'hold');
        $this->ok(!empty($r['ok']) && $r['decision'] === 'approved', 'Aprovação nativa');
        $this->ok($r['destination'] === 'hold', 'Destino hold (sem publicação)');
        $this->ok(isset($GLOBALS['nat_options']['cxeg_review_9900']), 'Histórico nativo preservado');

        // Hash divergente bloqueia
        $r2 = cxgv1nat_approve(9900, 'hash_errado', 'hold');
        $this->ok(!empty($r2['error']), 'Hash divergente bloqueia');

        // Reprovação
        $r3 = cxgv1nat_reject(9900, $hash, array('fontes_insuficientes', 'texto_incompleto_repetitivo'), 'Precisa de fontes.');
        $this->ok(!empty($r3['ok']) && $r3['decision'] === 'rejected', 'Reprovação com motivos');
        $this->ok(count($r3['rejection_reasons']) === 2, 'Múltiplos motivos');

        // Reprovação sem justificativa bloqueia
        $r4 = cxgv1nat_reject(9900, $hash, array('fontes_insuficientes'), '');
        $this->ok(!empty($r4['error']), 'Reprovação sem justificativa bloqueia');

        // Reprovação sem motivo bloqueia
        $r5 = cxgv1nat_reject(9900, $hash, array(), 'Justificativa');
        $this->ok(!empty($r5['error']), 'Reprovação sem motivo bloqueia');

        echo "\nPASS: {$this->pass} | FAIL: {$this->fail}\n";
        exit($this->fail > 0 ? 1 : 0);
    }
}
(new NatTest())->run();
