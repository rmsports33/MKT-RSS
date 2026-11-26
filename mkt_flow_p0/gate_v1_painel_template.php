<?php
/**
 * Conexo Editorial Gate V1 — Template do novo painel de aprovação.
 * Layout de duas colunas com decisão editorial (APROVO / DESAPROVO).
 *
 * Este arquivo é renderizado pelo WordPress como página de administração.
 * Não altera a instalação WordPress em produção sem autorização específica.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Registra o novo painel de aprovação no menu admin do WordPress.
 */
function cxgv1_register_admin_menu() {
    add_management_page(
        'Aprovação Gate V1 — Novo Painel',
        'Aprovação Gate V1',
        'manage_options',
        'cxgv1-novo-painel',
        'cxgv1_render_admin_page'
    );
}
add_action('admin_menu', 'cxgv1_register_admin_menu');

/**
 * Registra endpoints REST para listar rascunhos, obter detalhes e salvar decisão.
 */
function cxgv1_register_rest_endpoints() {
    register_rest_route('cxgv1/v1', '/drafts', array(
        'methods' => 'GET',
        'permission_callback' => function() {
            return current_user_can('manage_options') && defined('CXEG_OWNER_REVIEWER_ID') && get_current_user_id() === CXEG_OWNER_REVIEWER_ID;
        },
        'callback' => 'cxgv1_rest_list_drafts',
    ));

    register_rest_route('cxgv1/v1', '/drafts/(?P<id>\d+)', array(
        'methods' => 'GET',
        'permission_callback' => function($request) {
            return current_user_can('manage_options') && defined('CXEG_OWNER_REVIEWER_ID') && get_current_user_id() === CXEG_OWNER_REVIEWER_ID;
        },
        'callback' => 'cxgv1_rest_get_detail',
    ));

    register_rest_route('cxgv1/v1', '/drafts/(?P<id>\d+)/history', array(
        'methods' => 'GET',
        'permission_callback' => function($request) {
            return current_user_can('manage_options') && defined('CXEG_OWNER_REVIEWER_ID') && get_current_user_id() === CXEG_OWNER_REVIEWER_ID;
        },
        'callback' => 'cxgv1_rest_get_history',
    ));

    register_rest_route('cxgv1/v1', '/decision', array(
        'methods' => 'POST',
        'permission_callback' => function() {
            return current_user_can('manage_options') && defined('CXEG_OWNER_REVIEWER_ID') && get_current_user_id() === CXEG_OWNER_REVIEWER_ID;
        },
        'callback' => 'cxgv1_rest_save_decision',
    ));
}
add_action('rest_api_init', 'cxgv1_register_rest_endpoints');

/**
 * REST: Listar rascunhos elegíveis.
 */
function cxgv1_rest_list_drafts() {
    require_once __DIR__ . '/gate_v1_painel_aprovacao.php';
    return cxgv1_list_drafts(5);
}

/**
 * REST: Obter detalhes de um artigo.
 */
function cxgv1_rest_get_detail($request) {
    require_once __DIR__ . '/gate_v1_painel_aprovacao.php';
    return cxgv1_get_article_detail((int)$request['id']);
}

/**
 * REST: Obter histórico de decisões.
 */
function cxgv1_rest_get_history($request) {
    require_once __DIR__ . '/gate_v1_painel_aprovacao.php';
    return cxgv1_get_decision_history((int)$request['id']);
}

/**
 * REST: Salvar decisão editorial.
 */
function cxgv1_rest_save_decision($request) {
    require_once __DIR__ . '/gate_v1_painel_aprovacao.php';

    $params = $request->get_json_params();
    $post_id = isset($params['post_id']) ? (int)$params['post_id'] : 0;
    $decision = isset($params['decision']) ? $params['decision'] : '';
    $snapshot_hash = isset($params['snapshot_hash']) ? $params['snapshot_hash'] : '';
    $reviewer_id = get_current_user_id();

    $rejection_reasons = array();
    if (isset($params['rejection_reasons']) && is_array($params['rejection_reasons'])) {
        $rejection_reasons = $params['rejection_reasons'];
    } elseif (isset($params['rejection_reasons']) && is_string($params['rejection_reasons'])) {
        $rejection_reasons = json_decode($params['rejection_reasons'], true);
        if (!is_array($rejection_reasons)) {
            $rejection_reasons = array();
        }
    }

    $justification = isset($params['justification']) ? $params['justification'] : '';

    return cxgv1_save_decision(
        $post_id,
        $decision,
        $rejection_reasons,
        $justification,
        $snapshot_hash,
        $reviewer_id
    );
}

/**
 * Renderiza a página de administração do novo painel.
 */
function cxgv1_render_admin_page() {
    if (!defined('CXEG_OWNER_REVIEWER_ID') || get_current_user_id() !== CXEG_OWNER_REVIEWER_ID) {
        echo '<div class="wrap"><h1>Acesso Negado</h1><p>Somente o proprietário autorizado pode acessar este painel.</p></div>';
        return;
    }

    // Carregar CSS e JS
    wp_enqueue_style('cxgv1-painel', plugins_url('mkt_flow_p0/gate_v1_painel_aprovacao.css', __FILE__), array(), '0.1.0-rc10.4');
    wp_enqueue_script('cxgv1-painel', plugins_url('mkt_flow_p0/gate_v1_painel_aprovacao.js', __FILE__), array('jquery'), '0.1.0-rc10.4', true);

    // Variáveis globais para JS
    wp_localize_script('cxgv1-painel', 'cxgv1_nonce', wp_create_nonce('wp_rest'));
    wp_localize_script('cxgv1-painel', 'cxgv1_current_user_id', get_current_user_id());
    wp_localize_script('cxgv1-painel', 'ajaxurl', admin_url('admin-ajax.php'));

    $rejection_reasons = cxgv1_rejection_reasons();

    echo '<div class="cxgv1-shell">';
    echo '<header class="cxgv1-head">';
    echo '<div>';
    echo '<h1>Conexo Gate V1 — Aprovação Editorial</h1>';
    echo '<p class="cxgv1-sub">Layout de duas colunas: lista de artigos à esquerda, preview e decisão à direita.</p>';
    echo '</div>';
    echo '</header>';

    echo '<div class="cxgv1-stats">';
    echo '<div class="cxgv1-stat"><strong id="cxgv1-stat-total">0</strong><span>Artigos na fila</span></div>';
    echo '<div class="cxgv1-stat"><strong id="cxgv1-stat-ready">0</strong><span>Prontos para revisão</span></div>';
    echo '<div class="cxgv1-stat"><strong id="cxgv1-stat-blocked">0</strong><span>Com pendências</span></div>';
    echo '<div class="cxgv1-stat"><strong id="cxgv1-stat-approved">0</strong><span>Já aprovados</span></div>';
    echo '</div>';

    echo '<div class="cxgv1-layout">';

    // COLUNA ESQUERDA — Lista de artigos
    echo '<section class="cxgv1-panel">';
    echo '<h2>Lista de Artigos</h2>';
    echo '<p style="font-size:13px;color:var(--cxgv1-muted);margin-bottom:12px;">Selecione um artigo para revisar e decidir.</p>';
    echo '<div id="cxgv1-article-list" class="cxgv1-article-list">';
    echo '<p style="color:var(--cxgv1-muted);font-style:italic;">Carregando rascunhos...</p>';
    echo '</div>';
    echo '</section>';

    // COLUNA DIREITA — Preview e decisão
    echo '<section class="cxgv1-panel cxgv1-preview-panel">';
    echo '<div id="cxgv1-preview-empty" style="text-align:center;padding:40px 20px;color:var(--cxgv1-muted);">';
    echo '<p>Nenhum artigo selecionado.</p>';
    echo '<p style="font-size:13px;">Clique em um artigo na lista à esquerda.</p>';
    echo '</div>';

    echo '<div id="cxgv1-preview-content" style="display:none;">';
    echo '<img id="cxgv1-preview-image" src="" alt="" style="display:none;">';
    echo '<h2 id="cxgv1-preview-title"></h2>';
    echo '<p id="cxgv1-preview-subtitle"></p>';
    echo '<div id="cxgv1-preview-content-body"></div>';
    echo '<div class="cxgv1-preview-meta">';
    echo '<span id="cxgv1-preview-category"></span>';
    echo '<span id="cxgv1-preview-date"></span>';
    echo '<span id="cxgv1-preview-status"></span>';
    echo '</div>';

    // Abas
    echo '<div class="cxgv1-tabs" role="group" aria-label="Abas do artigo">';
    echo '<button type="button" class="cxgv1-tab" data-tab="preview" aria-pressed="true">Pré-visualização</button>';
    echo '<button type="button" class="cxgv1-tab" data-tab="details">Detalhes</button>';
    echo '<button type="button" class="cxgv1-tab" data-tab="verification">Verificação</button>';
    echo '</div>';

    // Conteúdo das abas
    echo '<div id="cxgv1-tab-preview" class="cxgv1-tab-content active">';
    echo '<div id="cxgv1-preview-full"></div>';
    echo '</div>';

    echo '<div id="cxgv1-tab-details" class="cxgv1-tab-content">';
    echo '<p>Detalhes técnicos do artigo serão exibidos aqui após seleção.</p>';
    echo '</div>';

    echo '<div id="cxgv1-tab-verification" class="cxgv1-tab-content">';
    echo '<p>Verificações técnicas (13 itens) serão exibidas aqui após seleção.</p>';
    echo '</div>';

    // Decisão editorial
    echo '<div class="cxgv1-decision">';
    echo '<h3>Decisão Editorial</h3>';

    echo '<div class="cxgv1-decision-buttons">';
    echo '<button type="button" id="cxgv1-btn-approve" class="cxgv1-btn-approve">APROVO</button>';
    echo '<button type="button" id="cxgv1-btn-reject" class="cxgv1-btn-reject">NÃO APROVO</button>';
    echo '</div>';

    echo '<div class="cxgv1-rejection-reasons" id="cxgv1-rejection-reasons" style="display:none;">';
    echo '<label>Motivo(s) da reprovação (seleção múltipla):</label>';
    $rejection_reasons = cxgv1_rejection_reasons();
    foreach ($rejection_reasons as $key => $label) {
        echo '<label class="cxgv1-reason-item">';
        echo '<input type="radio" name="cxgv1-reject-reason" value="' . esc_attr($key) . '">';
        echo esc_html($label);
        echo '</label>';
    }
    echo '</div>';

    echo '<div class="cxgv1-justification-field" id="cxgv1-justification-field" style="display:none;">';
    echo '<label>Justificativa (obrigatória para reprovação):</label>';
    echo '<textarea id="cxgv1-justification" rows="4" placeholder="Explique o motivo da reprovação..."></textarea>';
    echo '</div>';

    echo '<button type="button" id="cxgv1-btn-save" class="cxgv1-save-btn" disabled>SALVAR RESPOSTA</button>';
    echo '<div id="cxgv1-save-message" class="cxgv1-save-message"></div>';

    echo '<div class="cxgv1-decision-history" id="cxgv1-decision-history">';
    echo '<h3>Histórico de Decisões</h3>';
    echo '<div id="cxgv1-history-list">Nenhuma decisão registrada.</div>';
    echo '</div>';

    echo '</div>'; // Fim cxgv1-decision

    echo '</div>'; // Fim cxgv1-preview-panel

    echo '</div>'; // Fim cxgv1-layout
    echo '</div>'; // Fim cxgv1-shell

    // Inserir JS inline para inicializar
    echo '<script>';
    echo 'window.cxgv1_nonce = ' . json_encode(wp_create_nonce('wp_rest')) . ';';
    echo 'window.cxgv1_current_user_id = ' . intval(get_current_user_id()) . ';';
    echo 'window.cxgv1_ajaxurl = ' . json_encode(admin_url('admin-ajax.php')) . ';';
    echo '</script>';
}
