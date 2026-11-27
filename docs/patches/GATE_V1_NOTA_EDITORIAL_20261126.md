# Patch aditivo no Gate V1 — campo de nota editorial (26/11/2026)

**Autorização:** proprietário autorizou o passo 4 do plano de qualidade em 26/11/2026.
**Restrições:** Gate V1 RC10.4 preservado; sem Gate V2; sem lógica paralela; 13 checks e HMAC intactos.

## Arquivo alterado no site

`wp-content/plugins/conexo-editorial-gate/includes/conexo-owner-review.php`

Mudanças aditivas:

1. `cxeg_owner_approve(..., $publish_mode = 'hold', $nota_humana = -1)`.
2. Validação: nota humana inteira entre 0 e 100; fora disso, erro 422.
3. `nota_humana` incluída no payload aprovado e no `quality_record` — portanto vinculada ao hash da versão.
4. Formulário do proprietário mostra:
   - "Nota assistida" (orienta, nunca autoriza);
   - campo **Nota humana do proprietário (0–100)**, obrigatório.

## Contrato relacionado

- Canônico: `conexo-os/docs/EDITORIAL_QUALITY_CONTRACT.md`
- JSON: `conexo-os/contracts/editorial-quality-v1.json`
- Hash: `6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7`

Escala e linha de corte seguem **aguardando confirmação do proprietário**. Nenhuma nota é publicação automática.

## Verificação

- Upload via TUS: `201 Created` + `204 No Content`.
- Readback: `name="nota_humana"`, `_cxeg_nota_assistida` e `nota_humana` no payload presentes.
- Página do Gate: campo aparece; nota assistida aparece como "não registrada" até o MKT-RSS gravar o recibo (etapa 3 do plano).
- Site sem erro fatal; nenhuma publicação executada.
