# Contrato de integração — MKT-RSS e Gate V1

Data: 2026-11-25  
Escopo: análise e implementação isolada no MKT-RSS. Não autoriza alteração do Gate, merge, deploy ou escrita no WordPress.

## Decisão

O Gate V1 continua sendo a única autoridade WordPress para qualidade, revisão humana, aprovação por versão e autorização de escrita. O certificado factual do MKT-RSS é uma evidência adicional, não substitui nem duplica a aprovação do Gate.

Não instalar nem integrar o Gate V2. Seus padrões podem ser consultados como referência, mas não constituem uma dependência.

## Contrato V1 observado no código-fonte auditado

A cópia de código consultada foi a branch `audit-active-gate-rc5-20261111`, SHA `5f549f2a2c6da6cc6f2eb92d5e3bef7658cffe5a`, no repositório `rmsports33/-site-conexotech`. Ela corresponde à auditoria da família V1/rc5, não prova por si só que todos os detalhes são idênticos ao plugin instalado, identificado separadamente como 0.1.0-rc10.4.

Rotas encontradas no núcleo V1:

- `POST /conexo/v1/editorial/quality/record`: persiste parecer privado, exige usuário autenticado com capacidades de publicação/edição de outros posts, vincula o parecer ao snapshot hash e valida os 13 checks requeridos.
- `GET /conexo/v1/editorial/quality/{id}`: permite leitura autenticada do parecer conforme permissões do post.
- `POST /conexo/v1/editorial/review/approve`: exige revisor autorizado diferente do autor (salvo modo proprietário explicitamente configurado), hash do snapshot, hash da versão, referência de publicação e parecer de qualidade vigente.
- `GET /conexo/v1/editorial/snapshot/{id}`: devolve snapshot autenticado e seu hash.
- `POST /conexo/v1/editorial/write`: verifica HMAC do executor, identidade, versão, parecer, aprovação humana, nonce e readback.
- `POST /conexo/v1/editorial/broker/write`: broker para o executor MKT-RSS; revalida usuário de serviço, versão, parecer, aprovação e então chama o mesmo `cxeg_write`.

A função `cxeg_quality_record` grava `reviewer_id`, `reviewed_at`, `review_mode`, hash do snapshot e evidências dos checks. A função `cxeg_review_approve` grava `reviewer_id`, decisão, hash do snapshot, hash da versão e referência. O broker V1 já verifica os dois registros antes da escrita.

## Lacunas que impedem a ligação automática do certificado factual

1. O endpoint de leitura de qualidade expõe o parecer, mas a cópia de código auditada não expõe uma rota de leitura autenticada do registro `cxeg_review_{post_id}` completo. A rota de aprovação devolve confirmação e hash, não o registro integral com evidências e identidade.
2. Portanto, o MKT-RSS não deve fabricar um `review_record` a partir de um HTTP 200, de campos enviados pelo pacote ou de um nome de revisor não autenticado. O emissor `issue_factual_certificate` só pode receber um registro obtido de uma origem autenticada e verificável.
3. A cópia V1 auditada usa `add_option` como lock, faz uma comparação de snapshot e depois chama `wp_insert_post`; o lock é liberado no `finally`. Há readback e idempotência por nonce, mas isso não demonstra compare-and-swap transacional do post e de seus metadados. A função Python `supervised_atomic_publish` exige um backend servidor-side atômico; não pode ser ligada a um simples GET+POST nem declarada satisfeita pelo lock atual.
4. A fonte V1 consultada é rc5, enquanto o site foi identificado em leitura separada como rc10.4. Antes de depender do contrato exato, é necessário confirmar as rotas e semântica na cópia autenticada read-only dos arquivos realmente instalados. Não inferir igualdade entre versões.

## Sequência segura

1. Manter o emissor factual como primitiva isolada. Não chamar o emissor com registros sintéticos nem com dados fornecidos pelo pacote.
2. Confirmar, por leitura autenticada do código realmente instalado, as rotas V1, os campos e a semântica do broker e dos registros de qualidade/aprovação.
3. Definir com o Gate V1 uma interface somente leitura, autenticada e versionada para recuperar o registro de revisão/aprovação necessário ao certificado, ou uma emissão server-side equivalente. Essa alteração pertence ao repositório do Gate e exige autorização separada.
4. Definir e homologar um backend servidor-side de compare-and-swap no WordPress antes de conectar `supervised_atomic_publish`. A implementação atual de lock não é prova suficiente.
5. Só então integrar no MKT-RSS: leitura autenticada do rascunho → avaliação editorial obrigatória → certificado factual assinado e vinculado ao hash exato → aprovação V1 vigente → broker V1 → readback → recibo verificável.
6. Até todas as condições anteriores estarem implementadas e testadas, o transporte de publicação deve continuar bloqueado por qualquer ausência ou divergência; nenhuma tentativa de publicação deve ser repetida automaticamente após resultado ambíguo.

## Limites desta entrega

- Nenhum endpoint ou arquivo do Gate foi alterado.
- Nenhuma credencial ou chave real foi lida, criada ou gravada.
- Nenhuma chamada de escrita ao WordPress foi realizada.
- Nenhum merge, deploy, instalação ou ativação foi realizado.
- A análise da branch rc5 não substitui a validação da versão rc10.4 instalada.
