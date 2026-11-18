# Fingerprint canônico da proveniência editorial — 18/11/2026

## Objetivo

Definir uma única representação UTF-8 do contrato `cxeg-package:v1`, compartilhada pelo produtor MKT-RSS (Python) e pelo consumidor Conexo Editorial Gate (PHP). O campo `version_sha256` não pode ser escolhido pelo chamador nem ser aceito apenas por ter 64 caracteres hexadecimais.

## Descritor canônico

O texto abaixo é a entrada exata do SHA-256. As quebras de linha são LF (`0x0A`), sem BOM e sem newline final:

```text
cxeg-package:v1
contract:2026-11-18-rc1
fields:content_sha256,version_sha256,modules,voice_status,substance_status,image_rights_confirmed
modules:editorial_identity,editorial_core_offline,seo,editorial_readiness,editorial_substance
hash:sha256
```

Fingerprint esperado:

```text
80d09ee7c49505560862a0364c1af8b4aa5b694f9db954b52b35f26b82bdbfaa
```

## Regras do produtor

- `version_sha256_esperado()` calcula o digest sobre os bytes UTF-8 do descritor.
- `marcar()` usa o fingerprint esperado por padrão.
- Se o chamador fornecer um digest, o produtor exige correspondência exata; um SHA-256 bem formado, mas divergente, é recusado.
- `validar_integridade()` também compara o digest recebido ao fingerprint esperado e retorna `version_hash_mismatch` quando divergir.
- Não há fallback, migração silenciosa nem digest arbitrário.

## Regras do Gate

O PHP calcula o mesmo descritor em `cxeg_provenance_expected_version_sha256()` e compara com o valor recebido usando `hash_equals()`. O teste contratual PHP deve fixar o mesmo vetor de teste; o teste Python também fixa o fingerprint acima. Assim, uma alteração acidental em qualquer byte, campo, módulo, ordem ou versão quebra o teste de compatibilidade.

## Escopo da garantia

O fingerprint identifica a versão do contrato de manifesto, não a versão do software MKT-RSS, a identidade de quem executou os módulos, nem prova que os módulos foram realmente executados. A integridade do corpo e os estados editoriais continuam sendo validados separadamente. A aprovação humana e a autorização de publicação continuam obrigatórias.

## Validação necessária

Executar no checkout isolado MKT-RSS:
- `python -m pytest -q tests/test_editorial_provenance.py`;
- testes de todos os módulos que chamam `marcar()` ou consomem `version_sha256`;
- bateria editorial relevante.

Executar no patch kit Gate:
- `php ops/gate-provenance-rc10.5/test_conexo_editorial_provenance.php`;
- `php -l ops/gate-provenance-rc10.5/conexo-editorial-provenance.php`.

Depois, gerar uma fixture usando o produtor Python real e validá-la pelo PHP real. A fixture deve permanecer fora da produção; o resultado precisa demonstrar aceitação do fingerprint correspondente e rejeição de um digest divergente. Não declarar compatibilidade ponta a ponta antes dessa execução.

Nenhuma integração em WordPress ativo, merge, deploy ou publicação é autorizada por este documento.
