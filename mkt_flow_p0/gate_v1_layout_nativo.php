<?php
/**
 * Conexo Editorial Gate V1 RC10.4 — Layout nativo de duas colunas.
 *
 * ADITIVO: adiciona apenas apresentação (layout + preview dinâmico) à página
 * existente `cxeg_owner_page`. NÃO cria lógica paralela de aprovação, NÃO cria
 * filas próprias, NÃO cria endpoints duplicados, NÃO reescreve o core.
 *
 * Toda decisão continua passando pelos mecanismos nativos:
 *   - cxeg_owner_approve()      (aprovação do proprietário, version-bound)
 *   - cxq_process_approved_intent() (destino: hold/queue/now)
 *   - cxeg_snapshot() / cxeg_hash() (hash da versão)
 *   - cxgna_draft_readiness()   (verificação técnica)
 *   - cxeg_review_* / cxeg_quality_* (histórico e parecer)
 *
 * Este arquivo é código isolado para desenvolvimento e testes.
 * Não é ativado em produção sem autorização específica.
 */

if (!defined('ABSPATH')) {
    define('ABSPATH', __DIR__ . '/../../');
}

// Modo isolado: não carregar arquivos do WordPress em testes
if (!defined('CXGV1NAT_TEST_MODE') || !CXGV1NAT_TEST_MODE) {
    if (function_exists('get_current_user_id') && function_exists('current_user_can')) {
        // Executando dentro do WordPress real: funções nativas já disponíveis.
    }
}

/**
 * Verifica se o usuário atual é o proprietário revisor (função nativa do Gate).
 */
function cxgv1nat_is_owner() {
    if (function_exists('cxeg_owner_current')) {
        return cxeg_owner_current();
    }
    return false;
}

/**
 * Lista rascunhos elegíveis Using native readiness + snapshot.
 * Retorna dados de apresentação (miniaturas, datas, status) sem duplicar regras.
 */
function cxgv1nat_list_drafts($limit = 5) {
    if (!cxgv1nat_is_owner()) {
        return array('error' => 'Usuário não autorizado.');
    }

    // Usa a função nativa de elegibilidade do Gate V1 (já existente).
    if (!function_exists('cxgna_eligible_drafts')) {
        return array('error' => 'Fila nativa indisponível.');
    }
    $posts = cxgna_eligible_drafts($limit);

    $items = array();
    foreach ($posts as $post) {
        if (!($post instanceof WP_Post)) {
            continue;
        }
        $id = (int) $post->ID;
        $thumbnail_id = (int) get_post_thumbnail_id($id);
        $thumb_url = $thumbnail_id ? wp_get_attachment_url($thumbnail_id) : '';
        $thumb_alt = $thumbnail_id ? trim((string) get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true)) : '';
        $cats = array();
        foreach (wp_get_post_categories($id) as $cat_id) {
            $cat = get_category($cat_id);
            if ($cat && !is_wp_error($cat)) {
                $cats[] = $cat->name;
            }
        }
        $issues = function_exists('cxgna_draft_readiness') ? cxgna_draft_readiness($id) : array();
        $state = empty($issues) ? 'ready' : 'blocked';

        $items[] = array(
            'id' => $id,
            'title' => $post->post_title,
            'date' => $post->post_modified,
            'categories' => $cats,
            'status' => $state,
            'thumbnail_url' => $thumb_url,
            'thumbnail_alt' => $thumb_alt,
            'snapshot_sha256' => function_exists('cxeg_hash') ? cxeg_hash(cxeg_snapshot($id)) : '',
            'issues' => $issues,
        );
    }
    return array('items' => $items, 'total' => count($items));
}

/**
 * Detalhes do artigo para o preview — somente leitura, usando funções nativas.
 */
function cxgv1nat_get_detail($id) {
    if (!cxgv1nat_is_owner()) {
        return array('error' => 'Usuário não autorizado.');
    }
    $id = (int) $id;
    $post = get_post($id);
    if (!$post || $post->post_type !== 'post' ||
        !in_array($post->post_status, array('draft', 'pending'), true)) {
        return array('error' => 'Artigo não disponível.');
    }
    if (!current_user_can('edit_post', $id)) {
        return array('error' => 'Sem permissão para editar este artigo.');
    }

    $snapshot = cxeg_snapshot($id);
    $hash = cxeg_hash($snapshot);
    $thumbnail_id = (int) get_post_thumbnail_id($id);
    $cats = array();
    foreach (wp_get_post_categories($id) as $cat_id) {
        $cat = get_category($cat_id);
        if ($cat && !is_wp_error($cat)) {
            $cats[] = $cat->name;
        }
    }
    $review = get_option('cxeg_review_' . $id, false);
    $quality = get_option('cxeg_quality_' . $id, false);

    return array(
        'id' => $id,
        'title' => $post->post_title,
        'subtitle' => $post->post_excerpt,
        'content' => $post->post_content,
        'categories' => $cats,
        'status' => $post->post_status,
        'date' => $post->post_modified,
        'thumbnail_url' => $thumbnail_id ? wp_get_attachment_url($thumbnail_id) : '',
        'thumbnail_alt' => $thumbnail_id ? trim((string) get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true)) : '',
        'snapshot_sha256' => $hash,
        'review' => is_array($review) ? $review : null,
        'quality' => is_array($quality) ? $quality : null,
        'issues' => function_exists('cxgna_draft_readiness') ? cxgna_draft_readiness($id) : array(),
    );
}

/**
 * Motivos de reprovação (derivados das diretrizes existentes no projeto).
 */
function cxgv1nat_rejection_reasons() {
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
 * APROVAR — usa EXCLUSIVAMENTE os mecanismos nativos do Gate V1.
 * Não grava em filas próprias. Não cria review paralelo.
 */
function cxgv1nat_approve($id, $expected_hash, $mode = 'hold', $checks = null) {
    if (!cxgv1nat_is_owner()) {
        return array('error' => 'Usuário não autorizado.');
    }
    $id = (int) $id;
    $snapshot = cxeg_snapshot($id);
    if (!$snapshot || !in_array($snapshot['post_status'], array('draft', 'pending'), true)) {
        return array('error' => 'Artigo não disponível.');
    }
    $hash = cxeg_hash($snapshot);
    if (!is_string($expected_hash) || !hash_equals($hash, $expected_hash)) {
        return array('error' => 'Versão diferente da analisada. Recarregue o artigo.');
    }
    if (!in_array($mode, array('hold', 'queue', 'now'), true)) {
        return array('error' => 'Destino inválido.');
    }

    // Verificação técnica nativa (não duplicada).
    if (function_exists('cxgna_draft_readiness')) {
        $issues = cxgna_draft_readiness($id);
        if (!empty($issues)) {
            return array('error' => 'Pendências técnicas: ' . implode('; ', $issues));
        }
    }

    // SEO nativo, vinculado ao snapshot — mesmo padrão da tela existente.
    $seo = array(
        'provider' => 'native',
        'title' => $snapshot['post_title'],
        'description' => wp_strip_all_tags($snapshot['post_excerpt']),
        'canonical' => rtrim(home_url(), '/') . '/' . $snapshot['post_name'] . '/',
    );
    if (function_exists('cxeg_reviewed_seo_valid') && !cxeg_reviewed_seo_valid($seo, $snapshot)) {
        return array('error' => 'SEO inválido.');
    }

    // Verificação obrigatória nativa (13 itens).
    // NUNCA inventar evidências: exige os checks reais do formulário nativo.
    if (!is_array($checks)) {
        return array('error' => 'Checklist humano ausente. Preencha os 13 critérios no formulário nativo.');
    }
    foreach (cxeg_quality_required_checks() as $key) {
        $check = $checks[$key] ?? null;
        if (!is_array($check) || ($check['estado'] ?? '') !== 'VERIFICADO'
            || !is_array($check['evidencia'] ?? null) || count($check['evidencia']) !== 1
            || !is_string($check['evidencia'][0]) || strlen(trim($check['evidencia'][0])) < 8) {
            return array('error' => 'Falta verificação humana com evidência: ' . $key);
        }
    }

    // Aceite nativo do proprietário (grava cxeg_review_ e cxeg_quality_).
    $approved = cxeg_owner_approve($id, $hash, $seo, $checks, true, $mode);
    if (is_wp_error($approved) || empty($approved['approved'])) {
        return array('error' => is_wp_error($approved) ? $approved->get_error_message() : 'Falha ao aprovar.');
    }

    // Destino nativo (hold não publica; queue/now usam o publicador existente).
    $result = cxq_process_approved_intent($id, $mode);
    if (is_wp_error($result)) {
        return array('error' => 'Aprovação salva, mas destino falhou: ' . $result->get_error_message());
    }

    return array(
        'ok' => true,
        'decision' => 'approved',
        'post_id' => $id,
        'version_sha256' => $approved['version_sha256'] ?? '',
        'snapshot_sha256' => $hash,
        'destination' => $mode,
        'message' => $mode === 'hold'
            ? 'Aprovado e mantido em espera (sem publicação).'
            : 'Aprovado e encaminhado ao destino nativo.',
    );
}

/**
 * DESAPROVAR — registra no próprio cxeg_review_ (mecanismo nativo de histórico),
 * sem criar fila paralela. O Gate já trata decisão != approved como reprovação.
 */
function cxgv1nat_reject($id, $expected_hash, $reasons = array(), $justification = '') {
    if (!cxgv1nat_is_owner()) {
        return array('error' => 'Usuário não autorizado.');
    }
    $id = (int) $id;
    $snapshot = cxeg_snapshot($id);
    if (!$snapshot || !in_array($snapshot['post_status'], array('draft', 'pending'), true)) {
        return array('error' => 'Artigo não disponível.');
    }
    $hash = cxeg_hash($snapshot);
    if (!is_string($expected_hash) || !hash_equals($hash, $expected_hash)) {
        return array('error' => 'Versão diferente da analisada. Recarregue o artigo.');
    }

    $valid = cxgv1nat_rejection_reasons();
    $selected = array_values(array_filter($reasons, function ($r) use ($valid) {
        return is_string($r) && array_key_exists($r, $valid);
    }));
    if (empty($selected)) {
        return array('error' => 'Selecione pelo menos um motivo.');
    }
    if (trim($justification) === '') {
        return array('error' => 'A justificativa é obrigatória.');
    }

    // Usa a chave nativa de histórico; decisão 'rejected' nunca autoriza publicação.
    $record = array(
        'decision' => 'rejected',
        'reviewer_id' => get_current_user_id(),
        'snapshot_sha256' => $hash,
        'version_sha256' => hash('sha256', wp_json_encode(array(
            'post' => $snapshot, 'reasons' => $selected,
            'justification' => trim($justification), 'at' => time(),
        ), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)),
        'publication_reference' => 'OWNER-REJECT-' . get_current_user_id() . '-' . $id . '-' . bin2hex(random_bytes(8)),
        'reviewed_at' => time(),
        'review_mode' => 'owner',
        'rejection_reasons' => $selected,
        'justification' => trim($justification),
        'decision_source' => 'gate_v1_native_layout',
    );
    update_option('cxeg_review_' . $id, $record, false);

    return array(
        'ok' => true,
        'decision' => 'rejected',
        'post_id' => $id,
        'version_sha256' => $record['version_sha256'],
        'rejection_reasons' => $selected,
        'justification' => trim($justification),
        'message' => 'Reprovado. Pendência registrada para correção no MKT-RSS.',
    );
}
