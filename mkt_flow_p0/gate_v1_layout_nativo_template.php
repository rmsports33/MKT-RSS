<?php
/**
 * Conexo Editorial Gate V1 RC10.4 — Template do layout nativo de duas colunas.
 *
 * ADITIVO: renderiza dentro da página existente do Gate. NÃO cria endpoints REST
 * novos — reaproveita `conexo/v1/editorial/snapshot/{id}`, `quality/{id}` e a
 * ação nativa `cxeg_owner_page` para salvar a decisão.
 *
 * O formulário de decisão usa os mesmos campos do formulário nativo existente
 * (`snapshot_sha256`, `checked[]`, `evidence[]`, `seo[]`, `owner_accept`,
 * `publication_mode`) — apenas apresentados com outro layout.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Enfileira CSS/JS somente na página nativa do Gate.
 */
function cxgv1nat_enqueue($hook) {
    if (!isset($_GET['page']) || sanitize_key(wp_unslash($_GET['page'])) !== 'conexo-owner-review') {
        return;
    }
    $base = plugins_url('mkt_flow_p0/', __FILE__);
    wp_enqueue_style('cxgv1nat', $base . 'gate_v1_layout_nativo.css', array(), '0.1.0-rc10.4');
    wp_enqueue_script('cxgv1nat', $base . 'gate_v1_layout_nativo.js', array('jquery'), '0.1.0-rc10.4', true);
    wp_localize_script('cxgv1nat', 'cxgv1nat_cfg', array(
        'apiBase' => esc_url_raw(rest_url('conexo/v1/editorial')),
        'nonce' => wp_create_nonce('wp_rest'),
        'currentUserId' => get_current_user_id(),
    ));
}
add_action('admin_enqueue_scripts', 'cxgv1nat_enqueue');

/**
 * Renderiza o painel de duas colunas ACIMA do formulário nativo existente.
 * Chamado por cxeg_owner_page() — aditivo, não substitui a tela.
 */
function cxgv1nat_render_above_native_form($id) {
    if (!function_exists('cxgv1nat_is_owner') || !cxgv1nat_is_owner()) {
        return;
    }
    $id = (int) $id;
    if (!$id) {
        return;
    }
    $snapshot = cxeg_snapshot($id);
    if (!$snapshot || !in_array($snapshot['post_status'], array('draft', 'pending'), true)) {
        return;
    }
    $hash = cxeg_hash($snapshot);

    echo '<div class="cxgv1nat-shell" id="cxgv1nat-root" data-post-id="' . esc_attr((string) $id) . '" data-snapshot="' . esc_attr($hash) . '">';
    echo '<div class="cxgv1nat-head"><h2>Revisão editorial — layout nativo</h2>';
    echo '<p class="cxgv1nat-sub">Selecione um artigo na lista. A decisão continua usando o mecanismo nativo do Gate V1.</p></div>';

    echo '<div class="cxgv1nat-stats"><div><strong id="cxgv1nat-total">0</strong><span>Na fila</span></div>'
        . '<div><strong id="cxgv1nat-ready">0</strong><span>Prontos</span></div>'
        . '<div><strong id="cxgv1nat-blocked">0</strong><span>Com pendências</span></div></div>';

    echo '<div class="cxgv1nat-layout">';

    // Coluna esquerda — lista (preenchida via JS com dados de leitura nativos)
    echo '<section class="cxgv1nat-panel"><h3>Fila de artigos</h3>';
    echo '<div id="cxgv1nat-list" class="cxgv1nat-list"><p class="cxgv1nat-muted">Carregando...</p></div>';
    echo '</section>';

    // Coluna direita — preview + decisão
    echo '<section class="cxgv1nat-panel"><h3>Pré-visualização</h3>';
    echo '<div id="cxgv1nat-detail" class="cxgv1nat-detail"><p class="cxgv1nat-muted">Clique em um artigo.</p></div>';
    echo '<div class="cxgv1nat-tabs"><button type="button" class="cxgv1nat-tab active" data-tab="preview">Pré-visualização</button>'
        . '<button type="button" class="cxgv1nat-tab" data-tab="details">Detalhes</button>'
        . '<button type="button" class="cxgv1nat-tab" data-tab="verification">Verificação</button></div>';
    echo '<div id="cxgv1nat-tab-preview" class="cxgv1nat-tabcontent active"></div>';
    echo '<div id="cxgv1nat-tab-details" class="cxgv1nat-tabcontent"></div>';
    echo '<div id="cxgv1nat-tab-verification" class="cxgv1nat-tabcontent"></div>';

    echo '<div class="cxgv1nat-decision"><h3>Decisão editorial</h3>';
    echo '<div class="cxgv1nat-buttons">';
    echo '<button type="button" id="cxgv1nat-approve" class="cxgv1nat-btn-approve">APROVAR E PUBLICAR</button>';
    echo '<button type="button" id="cxgv1nat-reject" class="cxgv1nat-btn-reject">NÃO APROVAR</button>';
    echo '</div>';

    echo '<fieldset id="cxgv1nat-reasons" class="cxgv1nat-reasons" hidden><legend>Motivos da reprovação</legend>';
    foreach (cxgv1nat_rejection_reasons() as $key => $label) {
        echo '<label><input type="checkbox" name="cxgv1nat_reason" value="' . esc_attr($key) . '"> ' . esc_html($label) . '</label>';
    }
    echo '</fieldset>';

    echo '<div id="cxgv1nat-just-wrap" hidden><label>Justificativa (obrigatória)</label>';
    echo '<textarea id="cxgv1nat-just" rows="3"></textarea></div>';

    echo '<button type="button" id="cxgv1nat-save" class="cxgv1nat-btn-save" disabled>SALVAR RESPOSTA</button>';
    echo '<div id="cxgv1nat-msg" class="cxgv1nat-msg" hidden></div>';
    echo '</div>';

    echo '</section></div></div>';
}
