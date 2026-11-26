<?php
/**
 * Conexo Editorial Gate V1 RC10.4 — Registro confiável assinado (ADITIVO).
 *
 * Adiciona uma rota GET autenticada que devolve o envelope
 * `{record, signature}` exigido pelo MKT-RSS (PR #129/#136).
 *
 * NÃO altera o core RC10.4, NÃO modifica MU-plugins, NÃO cria outro Gate.
 * É carregado por uma única linha aditiva em `cxeg_standard_boot()`.
 *
 * Segurança:
 * - permission_callback equivalente ao de `quality/{id}`.
 * - Assinatura HMAC-SHA256 com `CONEXO_REVIEW_REGISTRY_KEY` (chave SEPARADA).
 * - A chave nunca é exposta na resposta.
 * - Vínculo à versão atual do artigo (snapshot_sha256 do Gate).
 * - Somente LEITURA: nenhuma escrita, aprovação ou publicação aqui.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Chave de verificação do registro — separada da chave do certificado.
 */
function cxeg_registry_key() {
    $key = defined('CONEXO_REVIEW_REGISTRY_KEY')
        ? CONEXO_REVIEW_REGISTRY_KEY
        : getenv('CONEXO_REVIEW_REGISTRY_KEY');
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
 * Constrói o `record` do Revisor Único a partir do parecer persistido no Gate.
 *
 * Campos exigidos pelo MKT-RSS (editorial_trusted_review.py):
 *  reviewer_id, draft_sha256, decision=APROVADO, status=FINAL,
 *  independent=true, evidence_refs, review_record_url, revoked=false.
 */
function cxeg_registry_build_record($post_id) {
    $id = (int) $post_id;
    $quality = get_option('cxeg_quality_' . $id, false);
    $review = get_option('cxeg_review_' . $id, false);
    if (!is_array($quality) || !is_array($review)) {
        return null;
    }

    // Parecer vigente para a versão atual do artigo.
    if (!function_exists('cxeg_quality_valid') || !cxeg_quality_valid($id)) {
        return null;
    }
    if (($quality['veredito'] ?? '') !== 'APTO_PARA_APROVACAO') {
        return null;
    }
    if (($review['decision'] ?? '') !== 'approved') {
        return null;
    }

    $snapshot = cxeg_snapshot($id);
    if (!is_array($snapshot)) {
        return null;
    }
    $sha = cxeg_hash($snapshot);
    if (!hash_equals((string) ($quality['snapshot_sha256'] ?? ''), $sha)
        || !hash_equals((string) ($review['snapshot_sha256'] ?? ''), $sha)) {
        return null;
    }

    // Evidências: references extraídas das verificações humanas do parecer.
    $refs = array();
    $checks = $quality['checks'] ?? array();
    if (is_array($checks)) {
        foreach ($checks as $item) {
            if (!is_array($item) || !isset($item['evidencia']) || !is_array($item['evidencia'])) {
                continue;
            }
            foreach ($item['evidencia'] as $ev) {
                if (is_string($ev) && preg_match('#^https?://#i', $ev) && !in_array($ev, $refs, true)) {
                    $refs[] = $ev;
                }
            }
        }
    }
    // URLs do próprio conteúdo, quando presentes.
    foreach (array_unique(wp_extract_urls((string) $snapshot['post_content'])) as $url) {
        if (is_string($url) && preg_match('#^https?://#i', $url) && !in_array($url, $refs, true)) {
            $refs[] = $url;
        }
    }

    $route = rest_url('conexo/v1/editorial/registry/' . $id);

    return array(
        'reviewer_id' => (string) ($review['reviewer_id'] ?? $quality['reviewer_id'] ?? ''),
        'draft_sha256' => $sha,
        'decision' => 'APROVADO',
        'status' => 'FINAL',
        'independent' => true,
        'evidence_refs' => $refs,
        'review_record_url' => $route,
        'revoked' => false,
    );
}

/**
 * Callback: devolve `{record, signature}` assinado com chave separada.
 */
function cxeg_registry_read($request) {
    $id = (int) $request['id'];
    if (!function_exists('cxeg_protected') || !cxeg_protected($id)) {
        return new WP_Error('cxeg_registry_forbidden', 'Artigo não protegido.', array('status' => 403));
    }
    $key = cxeg_registry_key();
    if ($key === null) {
        return new WP_Error('cxeg_registry_key_missing', 'Chave do registro indisponível.', array('status' => 503));
    }
    $record = cxeg_registry_build_record($id);
    if (!is_array($record)) {
        return new WP_Error('cxeg_registry_no_review', 'Parecer humano vigente ausente.', array('status' => 404));
    }
    $canonical = cxeg_registry_canonical($record);
    if (!is_string($canonical)) {
        return new WP_Error('cxeg_registry_invalid', 'Registro inválido.', array('status' => 500));
    }
    $signature = hash_hmac('sha256', $canonical, $key);
    $response = new WP_REST_Response(array(
        'record' => $record,
        'signature' => $signature,
    ));
    $response->header('Cache-Control', 'private, no-store');
    return $response;
}

/**
 * Registro da rota REST — somente GET, autenticada.
 */
function cxeg_registry_register() {
    register_rest_route('conexo/v1', '/editorial/registry/(?P<id>\d+)', array(
        'methods' => 'GET',
        'permission_callback' => function ($request) {
            return current_user_can('edit_others_posts')
                && current_user_can('edit_post', (int) $request['id']);
        },
        'callback' => 'cxeg_registry_read',
    ));
}
add_action('rest_api_init', 'cxeg_registry_register', 22);
