# Homologação factual e operacional — Android Drop #9711

Data: 2026-11-02. Escopo: artigo offline ChatGPT-first, sem escrever no WordPress.

## Evidências confirmadas

- Fonte primária Android Drop: https://blog.google/products-and-platforms/platforms/android/android-drop-september-2026/ (publicação 2026-09-01). O texto anuncia Find Hub/Android 16+, Motion Assist/Android 17, Guided Vision/Android 9+, notas Keep e temas de conversa.
- Fonte primária Guided Vision: https://blog.google/innovation-and-ai/products/gemini-app/guided-vision-gemini-live/ (publicação 2026-10-01). O anúncio confirma lançamento, orientação e limites da ferramenta; distribuição e acesso individual não foram testados.
- Três links internos existentes, verificados em leitura web:
  - https://conexotech.com.br/reviews/samsung-galaxy-a57-5g-vale-a-pena-em-2026/
  - https://conexotech.com.br/megapixels-nao-garantem-qualidade-avalie-a-camera-do-celular/
  - https://conexotech.com.br/comparativos/comparativo-galaxy-a54-vs-redmi-note-13/
- WordPress media ID #9714 confirmado por leitura autenticada: imagem 2172x1448; alt 'Detalhe da tela de um smartphone Android com ícones de aplicativos.'; legenda 'Imagem ilustrativa de smartphone Android. Foto: Deyvi Romero/Pexels.'; arquivo https://conexotech.com.br/wp-content/uploads/2026/10/smartphone-android-deyvi-romero-pexels.jpg
- Página original da foto: https://www.pexels.com/photo/black-android-smartphone-showing-instagram-and-gmail-application-89955/ ; fotógrafo Deyvi Romero; licença Pexels para uso comercial conforme https://help.pexels.com/hc/pt/articles/360042295174-Qual-%C3%A9-a-licen%C3%A7a-das-fotos-e-v%C3%ADdeos-no-Pexels

## Evidência técnica

- Núcleo integrado: PR #37; commit 1c51e48bd4c2c29a86c19a34f2ff8d3cbb0a87cf.
- Workflow artefatos: https://github.com/rmsports33/MKT-RSS/actions/runs/41532586084 — sucesso; ZIP 'chatgpt-first-android-drop-9711' com HTML offline, fragmento WordPress e relatório JSON. Prazo de retenção: 7 dias.
- CI pytest e validação editorial: aprovados nesse commit.
- Nenhuma escrita no WordPress, merge, deploy, publicação ou chamada a API de LLM.

## Pendências antes da aprovação editorial e publicação

1. Vincular cada alegação a trechos/capturas verificáveis no EditorialContract canônico; as fontes listadas ainda não certificam integralmente o texto.
2. Revisar manualmente disponibilidade Brasil/idioma/conta e requisitos precisos de todos os recursos (distinguindo anúncio de disponibilidade real).
3. Conferir visualmente a prévia no desktop e celular e a saída real no tema antes de publicação.
4. Tratar a imagem do Pexels como ilustração, nunca como captura demonstrativa dos recursos; confirmar que a versão publicada mantém crédito e alt.
5. Homologar autorização de escrita e readback no WordPress após reconciliação de PRs #33/#34/#35, Conexo OS #42, site #52. PR #34 e #42 apresentam conflitos, não integrar cegamente.
6. Preservar a separação entre Marco A offline (técnico) e Marco B (publicação). Não interpretar status de CI como aprovação factual.

**Status:** MARCO A técnicamente testado; revisão factual humana pendente; publicação não autorizada.
