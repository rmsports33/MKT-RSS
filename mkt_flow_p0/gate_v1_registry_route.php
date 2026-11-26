<?php
/**
 * Conexo Editorial Gate V1 RC10.4 — Registro confiável assinado (ADITIVO).
 *
 * Rota GET autenticada que devolve `{record, signature}` compatível com
 * `editorial_trusted_review.verify_independent_review()` do MKT-RSS (PR #136).
 *
 * Correções aplicadas (PR #137):
 *  A. Independência real: revisão owner NÃO é aceita como independente.
 *  B. draft_sha256 = draft_digest() do Python (campos canônicos), não o hash
 *     interno do snapshot do Gate.
 *  C. Evidências: somente HTTPS explicitamente registradas no parecer.
 *  D. Chave separada obrigatória e distinta da chave do certificado.
 *  E. Permissões: identidade do revisor/proprietário, não edit_others_posts genérico.
 *
 * NÃO altera core RC10.4, NÃO modifica MU-plugins, NÃO cria outro Gate.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** Chave de verificação do registro (separada da chave do certificado). */
function cxeg_registry_key() {
    $key = defined('CONEXO_REVIEW_REGISTRY_KEY')
        ? CONEXO_REVIEW_REGISTRY_KEY
        : getenv('CONEXO_REVIEW_REGISTRY_KEY');
    return is_string($key) && strlen($key) >= 32 ? $key : null;
}

/** Chave do certificado, para garantir que são distintas (sem expor valores). */
function cxeg_registry_certificate_key() {
    $key = defined('CONEXO_EDITORIAL_GATE_KEY')
        ? CONEXO_EDITORIAL_GATE_KEY
        : getenv('CONEXO_EDITORIAL_GATE_KEY');
    return is_string($key) && strlen($key) >= 32 ? $key : null;
}

/**
 * Canonical JSON idêntico ao `_canonical_bytes()` do Python:
 * json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":")).
 */
function cxeg_registry_canonical($value) {
    if (function_exists('cxeg_sort')) {
        $value = cxeg_sort($value);
    }
    return json_encode($value, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_LINE_TERMINATORS);
}

/**
 * CORREÇÃO B — draft_digest() idêntico ao Python.
 *
 * Campos: id, status, title, content, slug, categories, featured_media.
 * - status deve ser 'draft'.
 * - categories: lista de int > 0, DEVE conter 10, NÃO pode conter 1; ordenada.
 * - featured_media: int > 0.
 * - title/content: strings não vazias (raw de arrays WP).
 * - canonical: sort_keys=True, ensure_ascii=False, separators=(",", ":").
 */
function cxeg_registry_draft_digest($id) {
    $post = get_post((int) $id);
    if (!$post || $post->post_type !== 'post' || $post->post_status !== 'draft') {
        return null;
    }
    $categories = array_map('intval', wp_get_post_categories((int) $id));
    if (!is_array($categories) || empty($categories)) {
        return null;
    }
    foreach ($categories as $cat) {
        if (!is_int($cat) || $cat <= 0) { return null; }
    }
    if (!in_array(10, $categories, true) || in_array(1, $categories, true)) {
        return null;
    }
    sort($categories, SORT_NUMERIC);
    $thumb = (int) get_post_thumbnail_id((int) $id);
    if ($thumb <= 0) { return null; }
    $slug = (string) $post->post_name;
    if ($slug === '') { return null; }

    $fields = array(
        'id' => (int) $post->ID,
        'status' => $post->post_status,
        'title' => (string) $post->post_title,
        'content' => (string) $post->post_content,
        'slug' => $slug,
        'categories' => $categories,
        'featured_media' => $thumb,
    );
    if (trim($fields['title']) === '' || trim($fields['content']) === '') {
        return null;
    }
    // Ordena chaves para equivaler a sort_keys=True do Python.
    ksort($fields);
    $encoded = json_encode($fields, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_LINE_TERMINATORS);
    if (!is_string($encoded)) { return null; }
    return hash('sha256', $encoded);
}

/**
 * CORREÇÃO A + C — constrói o registro a partir de evidências reais do Gate.
 * Retorna null (fail-closed) quando não há independência comprovada.
 */
function cxeg_registry_build_record($post_id, $requested_mode = 'independent') {
    $id = (int) $post_id;
    $quality = get_option('cxeg_quality_' . $id, false);
    $review = get_option('cxeg_review_' . $id, false);
    if (!is_array($quality) || !is_array($review)) { return null; }
    if (!function_exists('cxeg_quality_valid') || !cxeg_quality_valid($id)) { return null; }
    if (($quality['veredito'] ?? '') !== 'APTO_PARA_APROVACAO') { return null; }
    if (($review['decision'] ?? '') !== 'approved') { return null; }

    $snapshot = cxeg_snapshot($id);
    if (!is_array($snapshot)) { return null; }
    $sha = cxeg_hash($snapshot);
    if (!hash_equals((string) ($quality['snapshot_sha256'] ?? ''), $sha)
        || !hash_equals((string) ($review['snapshot_sha256'] ?? ''), $sha)) { return null; }

    // CORREÇÃO B: draft_sha256 = draft_digest(), não o hash do snapshot.
    $draft_sha = cxeg_registry_draft_digest($id);
    if (!is_string($draft_sha)) { return null; }

    // CORREÇÃO A: independência real.
    $q_mode = (string) ($quality['review_mode'] ?? 'independent');
    $r_mode = (string) ($review['review_mode'] ?? 'independent');
    if ($q_mode !== $r_mode) { return null; } // coerência entre qualidade e aprovação
    $q_reviewer = $quality['reviewer_id'] ?? null;
    $r_reviewer = $review['reviewer_id'] ?? null;
    if (!is_int($q_reviewer) || !is_int($r_reviewer) || $q_reviewer !== $r_reviewer) { return null; }

    // Contrato exige revisão independente: owner NUNCA satisfaz.
    if ($requested_mode === 'independent' && $r_mode !== 'independent') { return null; }
    if ($r_mode === 'independent') {
        if ($r_reviewer === (int) $snapshot['post_author']) { return null; }
    } elseif ($r_mode === 'owner') {
        // owner é permitido apenas se explicitamente solicitado pelo chamador.
        if ($requested_mode !== 'owner') { return null; }
        if (!defined('CXEG_OWNER_REVIEWER_ID') || $r_reviewer !== CXEG_OWNER_REVIEWER_ID) { return null; }
    } else {
        return null; // modo desconhecido: falha segura
    }
    if (!function_exists('cxeg_review_identity_valid')
        || !cxeg_review_identity_valid($r_reviewer, $snapshot, $r_mode)) { return null; }

    // CORREÇÃO C: evidências explícitas HTTPS registradas no parecer.
    $refs = array();
    $checks = $quality['checks'] ?? array();
    if (!is_array($checks)) { return null; }
    foreach ($checks as $item) {
        if (!is_array($item) || !isset($item['evidencia']) || !is_array($item['evidencia'])) { continue; }
        foreach ($item['evidencia'] as $ev) {
            if (!is_string($ev)) { continue; }
            $ev = trim($ev);
            // Aceita apenas URLs HTTPS válidas registradas explicitamente.
            if (preg_match('#^https://[^\s]+$#i', $ev) && filter_var($ev, FILTER_VALIDATE_URL)
                && !in_array($ev, $refs, true)) {
                $refs[] = $ev;
            }
        }
    }
    if (empty($refs)) { return null; } // sem evidência explícita: falha segura

    $route = rest_url('conexo/v1/editorial/registry/' . $id);

    return array(
        'reviewer_id' => (string) $r_reviewer,
        'draft_sha256' => $draft_sha,
        'decision' => 'APROVADO',
        'status' => 'FINAL',
        'independent' => ($r_mode === 'independent'),
        'evidence_refs' => $refs,
        'review_record_url' => $route,
        'revoked' => false,
    );
}

/** Callback: envelope `{record, signature}` assinado com chave separada. */
function cxeg_registry_read($request) {
    $id = (int) $request['id'];
    if (!function_exists('cxeg_protected') || !cxeg_protected($id)) {
        return new WP_Error('cxeg_registry_forbidden', 'Artigo não protegido.', array('status' => 403));
    }
    $key = cxeg_registry_key();
    $cert_key = cxeg_registry_certificate_key();
    if ($key === null || $cert_key === null || hash_equals($key, $cert_key)) {
        return new WP_Error('cxeg_registry_keys_invalid', 'Chaves do registro inválidas ou repetidas.', array('status' => 503));
    }
    $mode = $request->get_param('mode') === 'owner' ? 'owner' : 'independent';
    $record = cxeg_registry_build_record($id, $mode);
    if (!is_array($record)) {
        return new WP_Error('cxeg_registry_no_review', 'Parecer humano vigente ausente.', array('status' => 404));
    }
    $canonical = cxeg_registry_canonical($record);
    if (!is_string($canonical)) {
        return new WP_Error('cxeg_registry_invalid', 'Registro inválido.', array('status' => 500));
    }
    $signature = hash_hmac('sha256', $canonical, $key);
    $response = new WP_REST_Response(array('record' => $record, 'signature' => $signature));
    $response->header('Cache-Control', 'private, no-store');
    return $response;
}

/** CORREÇÃO E — permissão restrita ao revisor autorizado. */
function cxeg_registry_permission($request) {
    $id = (int) $request['id'];
    if (!current_user_can('edit_post', $id)) { return false; }
    if (function_exists('cxeg_owner_current') && cxeg_owner_current()) { return true; }
    $actors = get_option('cxeg_broker_authorized_actors', false);
    return is_array($actors) && isset($actors['mkt_rss'])
        && (int) $actors['mkt_rss'] === get_current_user_id();
}

/** Registro da rota REST — somente GET, autenticada. */
function cxeg_registry_register() {
    register_rest_route('conexo/v1', '/editorial/registry/(?P<id>\d+)', array(
        'methods' => 'GET',
        'permission_callback' => 'cxeg_registry_permission',
        'callback' => 'cxeg_registry_read',
    ));
}
add_action('rest_api_init', 'cxeg_registry_register', 22);
