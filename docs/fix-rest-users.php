<?php
/**
 * fix-rest-users.php — Bloqueia exposição de logins via REST API.
 * COMO APLICAR (5 min, sem código novo para escrever):
 * 1. Hostinger → Gerenciador de Arquivos → public_html → wp-content → themes
 *    → pasta do SEU tema ativo → functions.php → Editar.
 * 2. Cole TODO o conteúdo deste arquivo no FINAL do functions.php
 *    (antes do "?>" final, se existir).
 * 3. Salvar. Pronto — /wp-json/wp/v2/users passa a retornar 401 para visitantes.
 * COMO VERIFICAR: abra em aba anônima
 * https://conexotech.com.br/wp-json/wp/v2/users
 * Esperado: {"code":"rest_forbidden",...} em vez da lista de usuários.
 */
// Bloqueia exposição de usuários via REST API (segurança)
add_filter('rest_endpoints', function($endpoints){
    if (isset($endpoints['/wp/v2/users'])) unset($endpoints['/wp/v2/users']);
    if (isset($endpoints['/wp/v2/users/(?P<id>[\d]+)'])) unset($endpoints['/wp/v2/users/(?P<id>[\d]+)']);
    return $endpoints;
});
