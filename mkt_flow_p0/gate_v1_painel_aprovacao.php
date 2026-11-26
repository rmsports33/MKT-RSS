<?php
/**
 * Conexo Editorial Gate V1 — Novo Painel de Aprovação Editorial
 * Layout de duas colunas: lista de artigos (esquerda) e preview (direita).
 * Decisão editorial: APROVO / DESAPROVO com motivos e justificativa.
 * Botão SALVAR RESPOSTA persiste a decisão sem publicar automaticamente.
 *
 * Este arquivo é código isolado para desenvolvimento e testes.
 * Não altera a instalação WordPress em produção.
 * Não é ativado como plugin ativo sem autorização específica.
 */

if (!defined('ABSPATH')) {
    // Modo isolado: define constantes mínimas para testes locais
    define('ABSPATH', __DIR__ . '/../../');
    define('WPINC', 'wp-includes');
    define('WP_CONTENT_DIR', __DIR__ . '/../../wp-content');
    define('WP_PLUGIN_DIR', __DIR__ . '/../../wp-content/plugins');
    define('WP_LANG_DIR', __DIR__ . '/../../wp-content/languages');
    define('WP_DEBUG', false);
}

// Em modo de teste isolado (definido antes do include), não carregar arquivos do WordPress
if (!defined('CXGV1_TEST_MODE') || !CXGV1_TEST_MODE) {
    require_once ABSPATH . 'wp-includes/functions.php';
    require_once ABSPATH . 'wp-includes/plugin.php';
    require_once ABSPATH . 'wp-includes/option.php';
    require_once ABSPATH . 'wp-includes/capabilities.php';
    require_once ABSPATH . 'wp-includes/user.php';
    require_once ABSPATH . 'wp-includes/post.php';
    require_once ABSPATH . 'wp-includes/taxonomy.php';
    require_once ABSPATH . 'wp-includes/media.php';
    require_once ABSPATH . 'wp-includes/http.php';
    require_once ABSPATH . 'wp-includes/rest-api.php';
    require_once ABSPATH . 'wp-includes/nav-menu.php';
    require_once ABSPATH . 'wp-includes/shortcode.php';
    require_once ABSPATH . 'wp-includes/http.php';
    require_once ABSPATH . 'wp-includes/authorize.php';
}

/**
 * Verifica se o usuário atual é o proprietário revisor autorizado.
 */
function cxgv1_is_owner_reviewer() {
    global $cxgv1_test_reviewer_id;

    // Em modo de teste isolado, permitir simular outro revisor
    if (defined('CXGV1_TEST_MODE') && CXGV1_TEST_MODE && $cxgv1_test_reviewer_id !== null) {
        $expected_id = $cxgv1_test_reviewer_id;
    } elseif (defined('CXEG_OWNER_REVIEWER_ID')) {
        $expected_id = CXEG_OWNER_REVIEWER_ID;
    } else {
        return false;
    }

    return get_current_user_id() === $expected_id
        && current_user_can('manage_options');
}

/**
 * Lista rascunhos elegíveis para revisão (3 a 5 artigos iniciais).
 */
function cxgv1_list_drafts($limit = 5) {
    if (!cxgv1_is_owner_reviewer()) {
        return array('error' => 'Usuário não autorizado.');
    }

    $drafts = get_posts(array(
        'post_type' => 'post',
        'post_status' => array('draft', 'pending'),
        'posts_per_page' => $limit,
        'orderby' => 'modified',
        'order' => 'DESC',
        'suppress_filters' => false,
    ));

    $result = array();
    foreach ($drafts as $post) {
        if (!($post instanceof WP_Post)) {
            continue;
        }
        if ($post->post_author === get_current_user_id()) {
            continue;
        }
        if (!current_user_can('edit_post', (int)$post->ID)) {
            continue;
        }

        $thumbnail_id = (int) get_post_thumbnail_id($post->ID);
        $thumbnail_url = $thumbnail_id ? wp_get_attachment_url($thumbnail_id) : '';
        $thumbnail_alt = $thumbnail_id ? trim((string) get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true)) : '';
        $categories = wp_get_post_categories((int)$post->ID);
        $category_names = array();
        foreach ($categories as $cat_id) {
            $cat = get_category($cat_id);
            if ($cat && !is_wp_error($cat)) {
                $category_names[] = $cat->name;
            }
        }

        $result[] = array(
            'id' => (int)$post->ID,
            'title' => $post->post_title,
            'date' => $post->post_modified,
            'categories' => $category_names,
            'status' => $post->post_status,
            'thumbnail_url' => $thumbnail_url,
            'thumbnail_alt' => $thumbnail_alt,
            'excerpt' => $post->post_excerpt,
            'content' => $post->post_content,
            'slug' => $post->post_name,
            'author_id' => (int)$post->post_author,
        );
    }

    return array('drafts' => $result, 'total' => count($result));
}

/**
 * Obtém dados detalhados de um artigo para preview.
 */
function cxgv1_get_article_detail($id) {
    if (!cxgv1_is_owner_reviewer()) {
        return array('error' => 'Usuário não autorizado.');
    }

    $id = (int)$id;
    $post = get_post($id);
    if (!$post || $post->post_type !== 'post') {
        return array('error' => 'Artigo não encontrado.');
    }

    if (!in_array($post->post_status, array('draft', 'pending'), true)) {
        return array('error' => 'Artigo não está em rascunho ou pendência.');
    }

    if (!current_user_can('edit_post', $id)) {
        return array('error' => 'Sem permissão para editar este artigo.');
    }

    $thumbnail_id = (int) get_post_thumbnail_id($id);
    $thumbnail_url = $thumbnail_id ? wp_get_attachment_url($thumbnail_id) : '';
    $categories = wp_get_post_categories($id);
    $category_names = array();
    foreach ($categories as $cat_id) {
        $cat = get_category($cat_id);
        if ($cat && !is_wp_error($cat)) {
            $category_names[] = $cat->name;
        }
    }

    $review = get_option('cxeg_review_' . $id, false);
    $quality = get_option('cxeg_quality_' . $id, false);
    $owner_release = get_option('cxeg_owner_release_' . $id, false);

    return array(
        'id' => (int)$id,
        'title' => $post->post_title,
        'subtitle' => $post->post_excerpt,
        'content' => $post->post_content,
        'categories' => $category_names,
        'status' => $post->post_status,
        'date' => $post->post_modified,
        'thumbnail_url' => $thumbnail_url,
        'thumbnail_alt' => $thumbnail_id ? trim((string) get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true)) : '',
        'slug' => $post->post_name,
        'author_id' => (int)$post->post_author,
        'review' => is_array($review) ? $review : null,
        'quality' => is_array($quality) ? $quality : null,
        'owner_release' => is_array($owner_release) ? $owner_release : null,
        'hash' => cxgv1_hash_snapshot($post),
    );
}

/**
 * Calcula hash SHA-256 do snapshot do artigo.
 */
function cxgv1_hash_snapshot($post) {
    $snapshot = array(
        'ID' => (int)$post->ID,
        'post_type' => $post->post_type,
        'post_status' => $post->post_status,
        'post_title' => $post->post_title,
        'post_content' => $post->post_content,
        'post_excerpt' => $post->post_excerpt,
        'post_name' => $post->post_name,
        'post_author' => (int)$post->post_author,
        'post_category' => wp_get_post_categories((int)$post->ID),
        'meta_input' => array(
            '_thumbnail_id' => (int) get_post_thumbnail_id((int)$post->ID),
        ),
    );
    sort($snapshot['post_category']);
    return hash('sha256', json_encode($snapshot, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
}

/**
 * Motivos válidos para reprovação (conforme diretrizes do projeto).
 */
function cxgv1_rejection_reasons() {
    return array(
        'fontes_insuficientes' => 'Fontes insuficientes',
        'afirmacao_sem_comprovacao' => 'Afirmações sem comprovação',
        'divergencia_nao_explicada' => 'Divergências não explicadas',
        'dados_numericos_sem_fonte' => 'Dados numéricos sem fonte',
        'contexto_brasileiro_ausente' => 'Contexto brasileiro ausente',
        'analise_superficial' => 'Análise superficial',
        'texto_incompleto_repetitivo' => 'Texto incompleto ou repetitivo',
        'identidade_editorial_ausente' => 'Identidade editorial ConexoTech ausente',
        'seo_inadequado' => 'SEO inadequado',
        'imagem_ausente_inadequada' => 'Imagem ausente ou inadequada',
        'referencias_insuficientes' => 'Referências insuficientes',
        'briefing_persona_ausente' => 'Briefing ou persona ausente',
        'rastreabilidade_incompleta' => 'Rastreabilidade incompleta',
        'alteracao_apos_aprovacao' => 'Alteração após aprovação',
    );
}

/**
 * Salva a decisão editorial (APROVO ou DESAPROVO).
 *
 * @param int $post_id ID do artigo
 * @param string $decision 'approve' ou 'reject'
 * @param array $rejection_reasons Lista de motivos (obrigatório se reject)
 * @param string $justification Justificativa obrigatória se reject
 * @param string $snapshot_hash Hash da versão analisada
 * @param string $reviewer_id ID do revisor
 * @return array Resultado da operação
 */
function cxgv1_save_decision($post_id, $decision, $rejection_reasons = array(), $justification = '', $snapshot_hash = '', $reviewer_id = null) {
    if (!cxgv1_is_owner_reviewer()) {
        return array('success' => false, 'error' => 'Usuário não autorizado.');
    }

    $post_id = (int)$post_id;
    $post = get_post($post_id);
    if (!$post || $post->post_type !== 'post') {
        return array('success' => false, 'error' => 'Artigo não encontrado.');
    }

    if (!in_array($post->post_status, array('draft', 'pending'), true)) {
        return array('success' => false, 'error' => 'Artigo não está em rascunho ou pendência.');
    }

    if (!current_user_can('edit_post', $post_id)) {
        return array('success' => false, 'error' => 'Sem permissão para editar este artigo.');
    }

    // Validar hash da versão
    $current_hash = cxgv1_hash_snapshot($post);
    if ($snapshot_hash !== $current_hash) {
        return array('success' => false, 'error' => 'Versão diferente da analisada. Recarregue o artigo.');
    }

    $reviewer_id = $reviewer_id ?: get_current_user_id();
    $timestamp = time();
    $nonce = bin2hex(random_bytes(16));

    if ($decision === 'approve') {
        // Validar que há qualidade técnica antes de aprovar
        $quality = get_option('cxeg_quality_' . $post_id, false);
        if (!is_array($quality) || ($quality['veredito'] ?? '') !== 'APTO_PARA_APROVACAO') {
            return array('success' => false, 'error' => 'Parecer de qualidade completo e vigente ausente.');
        }

        $review = array(
            'decision' => 'approved',
            'reviewer_id' => $reviewer_id,
            'snapshot_sha256' => $snapshot_hash,
            'version_sha256' => hash('sha256', json_encode(array(
                'post' => $post,
                'decision' => 'approved',
                'timestamp' => $timestamp,
            ), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)),
            'publication_reference' => 'OWNER-' . $reviewer_id . '-' . $post_id . '-' . substr($nonce, 0, 16),
            'reviewed_at' => $timestamp,
            'review_mode' => 'owner',
            'decision_source' => 'gate_v1_new_panel',
        );

        $result = update_option('cxeg_review_' . $post_id, $review, false);
        if ($result === false) {
            return array('success' => false, 'error' => 'Falha ao salvar aprovação.');
        }

        // Encaminhar para fila de publicação (não publicar automaticamente)
        $queue_result = cxgv1_forward_to_publish_queue($post_id, $review, $snapshot_hash);
        if (is_wp_error($queue_result)) {
            return array('success' => false, 'error' => 'Aprovação salva, mas falha no encaminhamento: ' . $queue_result->get_error_message());
        }

        return array(
            'success' => true,
            'decision' => 'approved',
            'post_id' => $post_id,
            'reviewer_id' => $reviewer_id,
            'reviewed_at' => $timestamp,
            'snapshot_hash' => $snapshot_hash,
            'version_sha256' => $review['version_sha256'],
            'publication_reference' => $review['publication_reference'],
            'destination' => 'publish_queue',
            'message' => 'Artigo aprovado e encaminhado para fila de publicação.',
        );
    } elseif ($decision === 'reject') {
        // Validar motivos
        $valid_reasons = cxgv1_rejection_reasons();
        $selected_reasons = array_filter($rejection_reasons, function ($r) use ($valid_reasons) {
            return in_array($r, array_keys($valid_reasons), true);
        });

        if (empty($selected_reasons)) {
            return array('success' => false, 'error' => 'Pelo menos um motivo de reprovação é obrigatório.');
        }

        if (trim($justification) === '') {
            return array('success' => false, 'error' => 'Justificativa é obrigatória para reprovação.');
        }

        $review = array(
            'decision' => 'rejected',
            'reviewer_id' => $reviewer_id,
            'snapshot_sha256' => $snapshot_hash,
            'version_sha256' => hash('sha256', json_encode(array(
                'post' => $post,
                'decision' => 'rejected',
                'reasons' => $selected_reasons,
                'justification' => $justification,
                'timestamp' => $timestamp,
            ), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)),
            'reviewed_at' => $timestamp,
            'review_mode' => 'owner',
            'rejection_reasons' => $selected_reasons,
            'justification' => trim($justification),
            'decision_source' => 'gate_v1_new_panel',
        );

        $result = update_option('cxeg_review_' . $post_id, $review, false);
        if ($result === false) {
            return array('success' => false, 'error' => 'Falha ao salvar reprovação.');
        }

        // Encaminhar de volta ao MKT-RSS para correção
        $queue_result = cxgv1_forward_to_mkt_rss_correction($post_id, $review, $snapshot_hash);
        if (is_wp_error($queue_result)) {
            return array('success' => false, 'error' => 'Reprovação salva, mas falha no encaminhamento: ' . $queue_result->get_error_message());
        }

        return array(
            'success' => true,
            'decision' => 'rejected',
            'post_id' => $post_id,
            'reviewer_id' => $reviewer_id,
            'reviewed_at' => $timestamp,
            'snapshot_hash' => $snapshot_hash,
            'rejection_reasons' => $selected_reasons,
            'justification' => trim($justification),
            'version_sha256' => $review['version_sha256'],
            'destination' => 'mkt_rss_correction',
            'message' => 'Artigo reprovado e encaminhado para correção no MKT-RSS.',
        );
    }

    return array('success' => false, 'error' => 'Decisão inválida.');
}

/**
 * Encaminha artigo aprovado para fila de publicação.
 */
function cxgv1_forward_to_publish_queue($post_id, $review, $snapshot_hash) {
    $queue_key = 'cxgv1_publish_queue_' . $post_id;
    $existing = get_option($queue_key, false);

    // Impedir duplicidade: se já existe uma fila para este post_id e versão, não sobrescreve
    if (is_array($existing) && isset($existing['version_sha256']) && $existing['version_sha256'] === $review['version_sha256']) {
        return array('idempotent' => true, 'queue_key' => $queue_key);
    }

    $queue_entry = array(
        'post_id' => (int)$post_id,
        'snapshot_sha256' => $snapshot_hash,
        'version_sha256' => $review['version_sha256'],
        'publication_reference' => $review['publication_reference'],
        'reviewer_id' => $review['reviewer_id'],
        'reviewed_at' => $review['reviewed_at'],
        'status' => 'pending_publication',
        'created_at' => time(),
        'destination' => 'publish_queue',
    );

    return update_option($queue_key, $queue_entry, false);
}

/**
 * Encaminha artigo reprovado para correção no MKT-RSS.
 */
function cxgv1_forward_to_mkt_rss_correction($post_id, $review, $snapshot_hash) {
    $queue_key = 'cxgv1_correction_queue_' . $post_id;
    $existing = get_option($queue_key, false);

    // Impedir duplicidade
    if (is_array($existing) && isset($existing['version_sha256']) && $existing['version_sha256'] === $review['version_sha256']) {
        return array('idempotent' => true, 'queue_key' => $queue_key);
    }

    $queue_entry = array(
        'post_id' => (int)$post_id,
        'snapshot_sha256' => $snapshot_hash,
        'version_sha256' => $review['version_sha256'],
        'rejection_reasons' => $review['rejection_reasons'],
        'justification' => $review['justification'],
        'reviewer_id' => $review['reviewer_id'],
        'reviewed_at' => $review['reviewed_at'],
        'status' => 'pending_correction',
        'created_at' => time(),
        'destination' => 'mkt_rss_correction',
    );

    return update_option($queue_key, $queue_entry, false);
}

/**
 * Obtém histórico de decisões para um artigo.
 */
function cxgv1_get_decision_history($post_id) {
    $post_id = (int)$post_id;
    $review = get_option('cxeg_review_' . $post_id, false);
    $queue_publish = get_option('cxgv1_publish_queue_' . $post_id, false);
    $queue_correction = get_option('cxgv1_correction_queue_' . $post_id, false);

    $history = array();
    if (is_array($review)) {
        $history[] = array(
            'decision' => $review['decision'],
            'reviewer_id' => $review['reviewer_id'],
            'reviewed_at' => $review['reviewed_at'],
            'snapshot_hash' => $review['snapshot_sha256'],
            'version_sha256' => $review['version_sha256'],
            'rejection_reasons' => $review['rejection_reasons'] ?? null,
            'justification' => $review['justification'] ?? null,
            'destination' => $review['decision'] === 'approved' ? 'publish_queue' : 'mkt_rss_correction',
        );
    }

    return array('history' => $history, 'total' => count($history));
}

/**
 * Verifica se já existe decisão para esta versão (proteção contra duplicidade).
 */
function cxgv1_decision_exists($post_id, $snapshot_hash) {
    $post_id = (int)$post_id;
    $review = get_option('cxeg_review_' . $post_id, false);

    if (is_array($review) && isset($review['snapshot_sha256']) && $review['snapshot_sha256'] === $snapshot_hash) {
        return true;
    }

    return false;
}
