<?php
/**
 * P0 Hostinger: observar um feed RSS em PHP CLI sem escrita em Turso/WordPress.
 * Não é substituto homologado do pipeline Python. Executar manualmente antes
 * de qualquer Cron. Uso: php rss_shadow_probe.php --self-test | --probe
 */
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(403); exit("CLI only\n"); }
$mode = $argv[1] ?? '--help';
if ($mode === '--self-test') {
    $ok = extension_loaded('curl') && function_exists('simplexml_load_string');
    echo json_encode(['mode'=>'SHADOW_SELF_TEST','ready'=>$ok,'curl'=>extension_loaded('curl'),'xml'=>function_exists('simplexml_load_string')]) . PHP_EOL;
    exit($ok ? 0 : 2);
}
if ($mode !== '--probe') { fwrite(STDERR, "Usage: php rss_shadow_probe.php --self-test|--probe\n"); exit(2); }
if (!extension_loaded('curl') || !function_exists('simplexml_load_string')) {
    echo json_encode(['status'=>'BLOCKED','reason'=>'MISSING_CURL_OR_XML']) . PHP_EOL;
    exit(2);
}
$endpoint = 'https://www.tecnoblog.net/feed/';
$ch = curl_init($endpoint);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 8,
    CURLOPT_TIMEOUT => 20,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_MAXREDIRS => 2,
    CURLOPT_SSL_VERIFYPEER => true,
    CURLOPT_SSL_VERIFYHOST => 2,
    CURLOPT_HTTPHEADER => ['Accept: application/rss+xml, application/atom+xml, application/xml'],
    CURLOPT_USERAGENT => 'ConexoOS-Shadow-Probe/0.1 (read-only)',
]);
$body = curl_exec($ch);
$code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
$failed = curl_errno($ch) !== 0;
curl_close($ch);
if ($failed || !is_string($body) || $code !== 200 || strlen($body) > 2 * 1024 * 1024) {
    echo json_encode(['status'=>'BLOCKED','reason'=>'FEED_HTTP_OR_SIZE_ERROR','http'=>$code]) . PHP_EOL;
    exit(1);
}
// XML externo deliberadamente desabilitado.
$previous = libxml_use_internal_errors(true);
$xml = simplexml_load_string($body, 'SimpleXMLElement', LIBXML_NONET);
libxml_clear_errors();
libxml_use_internal_errors($previous);
if ($xml === false) {
    echo json_encode(['status'=>'BLOCKED','reason'=>'XML_PARSE_ERROR']) . PHP_EOL;
    exit(1);
}
$items = [];
if (isset($xml->channel->item)) {
    foreach ($xml->channel->item as $item) {
        $title = trim((string) $item->title);
        $link = trim((string) $item->link);
        if ($title !== '' && preg_match('~^https://~i', $link)) {
            $items[] = ['source'=>'tecnoblog','title'=>$title,'link'=>$link];
        }
        if (count($items) >= 3) break;
    }
}
if (count($items) === 0) {
    echo json_encode(['status'=>'BLOCKED','reason'=>'NO_RSS_ITEMS']) . PHP_EOL;
    exit(1);
}
echo json_encode([
    'status'=>'PASS','mode'=>'SHADOW_NO_WRITES',
    'feed'=>'tecnoblog','sample_count'=>count($items),
    'titles'=>$items,
    'turso_modified'=>false,'wordpress_modified'=>false,'utc'=>gmdate('c')
], JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES) . PHP_EOL;
