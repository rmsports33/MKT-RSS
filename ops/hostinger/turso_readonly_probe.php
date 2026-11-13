<?php
/**
 * Leitura privada do Turso a partir do PHP CLI (Hostinger).
 * NAO cria tabelas, NAO executa WordPress, NAO tem interface HTTP.
 * Uso: php turso_readonly_probe.php --self-test | --probe
 */
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit("CLI only\n");
}
$mode = $argv[1] ?? '--help';
if ($mode === '--self-test') {
    $ok = extension_loaded('curl') && extension_loaded('json') && extension_loaded('openssl')
        && version_compare(PHP_VERSION, '8.0', '>=');
    echo json_encode(['mode' => 'SELF_TEST', 'ready' => $ok, 'php' => PHP_VERSION],
        JSON_UNESCAPED_SLASHES) . PHP_EOL;
    exit($ok ? 0 : 2);
}
if ($mode !== '--probe') {
    fwrite(STDERR, "Usage: php turso_readonly_probe.php --self-test | --probe\n");
    exit(2);
}
if (!extension_loaded('curl') || !extension_loaded('json')) {
    fwrite(STDERR, "BLOCKED: missing PHP extensions\n");
    exit(2);
}
$rawUrl = trim((string) getenv('TURSO_DATABASE_URL'));
$token = trim((string) getenv('TURSO_AUTH_TOKEN'));
if ($rawUrl === '' || $token === '') {
    echo json_encode(['status' => 'BLOCKED', 'reason' => 'PRIVATE_CREDENTIALS_NOT_CONFIGURED']) . PHP_EOL;
    exit(2);
}
$base = preg_replace('~^libsql://~', 'https://', $rawUrl);
$parts = parse_url((string) $base);
if (!is_array($parts) || ($parts['scheme'] ?? '') !== 'https'
    || !preg_match('~(^|\\.)turso\\.io$~i', (string) ($parts['host'] ?? ''))
    || !empty($parts['user']) || !empty($parts['pass']) || !empty($parts['query'])
    || !empty($parts['fragment'])) {
    echo json_encode(['status' => 'BLOCKED', 'reason' => 'INVALID_TURSO_HOST']) . PHP_EOL;
    exit(2);
}
$url = rtrim($base, '/') . '/v2/pipeline';
// SQL estatico e somente leitura: nao aceita query fornecida pelo usuario.
$sql = "SELECT 'rss_pautas' AS tabela, COUNT(*) AS total FROM rss_pautas "
    . "UNION ALL SELECT 'rss_notas_editoriais', COUNT(*) FROM rss_notas_editoriais "
    . "UNION ALL SELECT 'rss_product_links', COUNT(*) FROM rss_product_links "
    . "UNION ALL SELECT 'rss_vistos', COUNT(*) FROM rss_vistos";
$payload = json_encode([
    'requests' => [
        ['type' => 'execute', 'stmt' => ['sql' => $sql]],
        ['type' => 'close'],
    ],
], JSON_THROW_ON_ERROR);
$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $token,
        'Content-Type: application/json',
    ],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 8,
    CURLOPT_TIMEOUT => 18,
    CURLOPT_FOLLOWLOCATION => false,
    CURLOPT_SSL_VERIFYPEER => true,
    CURLOPT_SSL_VERIFYHOST => 2,
]);
$response = curl_exec($ch);
$status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
$networkError = curl_errno($ch) !== 0;
curl_close($ch);
unset($token, $payload);
if ($networkError || $response === false || $status !== 200) {
    echo json_encode([
        'status' => 'BLOCKED',
        'reason' => $networkError ? 'NETWORK_ERROR' : ('HTTP_' . $status),
    ]) . PHP_EOL;
    exit(1);
}
try {
    $data = json_decode((string) $response, true, 128, JSON_THROW_ON_ERROR);
    $result = $data['results'][0]['response']['result'] ?? null;
    if (!is_array($result) || !is_array($result['rows'] ?? null)) {
        throw new RuntimeException('UNEXPECTED_RESPONSE');
    }
    $counts = [];
    foreach ($result['rows'] as $row) {
        $values = array_map(static function ($v) {
            return is_array($v) ? ($v['value'] ?? null) : $v;
        }, $row);
        if (count($values) !== 2 || !is_string($values[0]) || !is_numeric($values[1])) {
            throw new RuntimeException('UNEXPECTED_ROW');
        }
        $counts[$values[0]] = (int) $values[1];
    }
    if (count($counts) !== 4) {
        throw new RuntimeException('MISSING_TABLE');
    }
    echo json_encode([
        'mode' => 'READ_ONLY',
        'status' => 'PASS',
        'counts' => $counts,
        'wordpress_binding_verified' => false,
        'utc' => gmdate('c'),
    ], JSON_UNESCAPED_SLASHES) . PHP_EOL;
} catch (Throwable $e) {
    echo json_encode(['status' => 'BLOCKED', 'reason' => 'INVALID_DB_RESPONSE']) . PHP_EOL;
    exit(1);
}
