<?php
/**
 * Conexo Editorial Gate V1 RC10.4 — Template do layout nativo de duas colunas.
 *
 * ADITIVO e conectado à tela nativa `cxeg_owner_page()`:
 *  - Renderiza via hook `admin_notices` somente em `page=conexo-owner-review`.
 *  - Lista e preview usam funções/rotas nativas existentes.
 *  - SALVAR RESPOSTA submete o FORMULÁRIO NATIVO identificado por ID único.
 *  - Não marca automaticamente os 13 critérios nem inventa evidências.
 *  - Não altera `publication_mode` (destino nativo preservado).
 *  - Reprovação é registrada na chave nativa `cxeg_review_{id}`.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** Enfileira CSS/JS somente na página nativa do Gate. */
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
        'formId' => 'cxgv1nat-native-form',
    ));
}
add_action('admin_enqueue_scripts', 'cxgv1nat_enqueue');

/**
 * Renderiza o painel de duas colunas ACIMA do formulário nativo existente.
 * Conexão efetiva: hook `admin_notices` dispara dentro da página nativa do Gate.
 */
function cxgv1nat_render_above_native_form() {
    if (!isset($_GET['page']) || sanitize_key(wp_unslash($_GET['page'])) !== 'conexo-owner-review') {
        return;
    }
    if (!function_exists('cxgv1nat_is_owner') || !cxgv1nat_is_owner()) {
        return;
    }
    $id = isset($_GET['post_id']) ? absint($_GET['post_id']) : 0;
    if (!$id) {
        return;
    }
    $snapshot = cxeg_snapshot($id);
    if (!$snapshot || !in_array($snapshot['post_status'], array('draft', 'pending'), true)) {
        return;
    }
    $hash = cxeg_hash($snapshot);

    // Lista nativa (usa cxgna_eligible_drafts via cxgv1nat_list_drafts).
    $listing = function_exists('cxgv1nat_list_drafts') ? cxgv1nat_list_drafts(5) : array('items' => array());

    echo '<div class="cxgv1nat-shell" id="cxgv1nat-root" data-post-id="' . esc_attr((string) $id) . '" data-snapshot="' . esc_attr($hash) . '">';
    echo '<div class="cxgv1nat-head"><h2>Revisão editorial — layout nativo</h2>';
    echo '<p class="cxgv1nat-sub">A decisão usa o formulário nativo do Gate V1. Os 13 critérios humanos devem ser conferidos por você.</p></div>';

    echo '<div class="cxgv1nat-stats"><div><strong>' . count($listing['items']) . '</strong><span>Na fila</span></div>'
        . '<div><strong>' . count(array_filter($listing['items'], function ($i) { return $i['status'] === 'ready'; })) . '</strong><span>Prontos</span></div>'
        . '<div><strong>' . count(array_filter($listing['items'], function ($i) { return $i['status'] === 'blocked'; })) . '</strong><span>Com pendências</span></div></div>';

    echo '<div class="cxgv1nat-layout">';

    // Coluna esquerda — lista renderizada no servidor com dados nativos.
    echo '<section class="cxgv1nat-panel"><h3>Fila de artigos</h3>';
    echo '<div id="cxgv1nat-list" class="cxgv1nat-list">';
    if (empty($listing['items'])) {
        echo '<p class="cxgv1nat-muted">Nenhum rascunho elegível.</p>';
    } else {
        foreach ($listing['items'] as $it) {
            $sel = ((int) $it['id'] === $id) ? ' sel' : '';
            $thumb = $it['thumbnail_url']
                ? '<img class="cxgv1nat-thumb" src="' . esc_url($it['thumbnail_url']) . '" alt="' . esc_attr($it['thumbnail_alt']) . '">'
                : '<div class="cxgv1nat-thumb-ph">Sem imagem</div>';
            echo '<div class="cxgv1nat-item' . $sel . '" data-id="' . esc_attr((string) $it['id']) . '" data-snapshot="' . esc_attr($it['snapshot_sha256']) . '">';
            echo $thumb . '<div><strong>' . esc_html($it['title']) . '</strong>';
            echo '<div class="cxgv1nat-meta"><span>' . esc_html($it['date']) . '</span>';
            echo '<span class="cxgv1nat-pill' . ($it['status'] === 'blocked' ? ' blocked' : '') . '">' . esc_html($it['status']) . '</span>';
            foreach ($it['categories'] as $c) {
                echo '<span>' . esc_html($c) . '</span>';
            }
            echo '</div></div></div>';
        }
    }
    echo '</div></section>';

    // Coluna direita — preview inicial do artigo selecionado (dados nativos).
    $detail = function_exists('cxgv1nat_get_detail') ? cxgv1nat_get_detail($id) : array();
    echo '<section class="cxgv1nat-panel"><h3>Pré-visualização</h3>';
    echo '<div id="cxgv1nat-detail" class="cxgv1nat-detail">';
    if (!empty($detail['title'])) {
        echo '<h4>' . esc_html($detail['title']) . '</h4>';
        echo '<p class="cxgv1nat-sub2">' . esc_html($detail['date']) . '</p>';
        echo '<div class="cxgv1nat-body">' . wp_kses_post($detail['content']) . '</div>';
    } else {
        echo '<p class="cxgv1nat-muted">Selecione um artigo.</p>';
    }
    echo '</div>';

    echo '<div class="cxgv1nat-tabs"><button type="button" class="cxgv1nat-tab active" data-tab="preview">Pré-visualização</button>'
        . '<button type="button" class="cxgv1nat-tab" data-tab="details">Detalhes</button>'
        . '<button type="button" class="cxgv1nat-tab" data-tab="verification">Verificação</button></div>';
    echo '<div id="cxgv1nat-tab-preview" class="cxgv1nat-tabcontent active"></div>';
    echo '<div id="cxgv1nat-tab-details" class="cxgv1nat-tabcontent"><p>ID: ' . esc_html((string) $id) . '</p><p>Status: ' . esc_html($detail['status'] ?? '') . '</p><p>Snapshot: <code>' . esc_html($hash) . '</code></p></div>';
    echo '<div id="cxgv1nat-tab-verification" class="cxgv1nat-tabcontent">';
    if (!empty($detail['issues'])) {
        echo '<ul>';
        foreach ($detail['issues'] as $issue) {
            echo '<li>' . esc_html($issue) . '</li>';
        }
        echo '</ul>';
    } else {
        echo '<p>Sem pendências técnicas detectadas.</p>';
    }
    echo '</div>';

    echo '<div class="cxgv1nat-decision"><h3>Decisão editorial</h3>';
    echo '<p class="cxgv1nat-sub">APROVAR: preencha os 13 critérios no formulário nativo abaixo e confirme. O layout não marca nem inventa evidências.</p>';
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

    // Marca o formulário nativo com ID único, sem depender de querySelector('form').
    echo '<script>(function(){var f=document.querySelector(".cx10-detail form");if(f){f.id="cxgv1nat-native-form";}})();</script>';
}
add_action('admin_notices', 'cxgv1nat_render_above_native_form', 5);

/**
 * Handler de reprovação: registra no histórico NATIVO `cxeg_review_{id}`.
 * Usa o nonce nativo (csrf) e a função nativa cxgv1nat_reject().
 */
function cxgv1nat_handle_reject() {
    if (!isset($_POST['cxgv1nat_reject'])) {
        return;
    }
    $id = isset($_POST['post_id']) ? absint($_POST['post_id']) : 0;
    if (!$id || !function_exists('cxgv1nat_is_owner') || !cxgv1nat_is_owner()) {
        return;
    }
    check_admin_referer('cxeg_owner_review_' . $id); // nonce nativo do artigo correto

    // Defesa em profundidade: o post_id do POST deve ser o da página
    // (evita aplicar decisão ao artigo errado).
    $page_id = isset($_GET['post_id']) ? absint($_GET['post_id']) : 0;
    if ($page_id && $page_id !== $id) {
        return;
    }
    $snapshot = cxeg_snapshot($id);
    $hash = $snapshot ? cxeg_hash($snapshot) : '';
    $expected = isset($_POST['snapshot_sha256']) ? sanitize_text_field(wp_unslash($_POST['snapshot_sha256'])) : '';
    if (!$hash || !hash_equals($hash, $expected)) {
        return; // versão divergente: não registra
    }
    $reasons_raw = isset($_POST['cxgv1nat_reason']) && is_array($_POST['cxgv1nat_reason'])
        ? array_map('sanitize_key', wp_unslash($_POST['cxgv1nat_reason'])) : array();
    $just = isset($_POST['cxgv1nat_justification']) ? sanitize_textarea_field(wp_unslash($_POST['cxgv1nat_justification'])) : '';
    if (!$reasons_raw || trim($just) === '') {
        return;
    }
    if (function_exists('cxgv1nat_reject')) {
        cxgv1nat_reject($id, $hash, $reasons_raw, $just);
    }
    wp_safe_redirect(add_query_arg(array('page' => 'conexo-owner-review', 'post_id' => $id, 'cxgv1nat' => 'rejected'), admin_url('tools.php')));
    exit;
}
add_action('admin_init', 'cxgv1nat_handle_reject', 5);
