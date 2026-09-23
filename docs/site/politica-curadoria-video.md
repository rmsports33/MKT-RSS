# Política de curadoria — reviews em vídeo (YouTube)

Vale para todos os projetos ConexoTech (gerador redator-artigo-blogs + site + plugin afiliados).
Aprovada em 21/09/2026. Revisar a cada 6 meses.

## 1. Por que vídeo de terceiro
- Corrobora a ficha técnica com imagem real do aparelho (tela ligada, câmera, construção).
- Gera rich result (VideoObject), tempo de página e superfície de citação para IAs.
- Nunca substitui teste próprio nem apuração: no texto, o vídeo "corrobora", nunca "prova".

## 2. Critérios do canal (todos obrigatórios)
1. Mostra o aparelho **ligado e em uso** (não só unboxing da caixa).
2. Sem jabá evidente: sem cupom do criador no título, sem "link na descrição" como argumento.
3. Sem clickbait no título do vídeo ("DESTRUIU", "NÃO COMPRE" em caps como regra).
4. Canal com histórico de reviews técnicos (não só shorts de oferta).
5. Incorporação **permitida** pelo dono (player carrega normalmente).

## 3. Como registrar na ficha (inserção automática)
- O gerador lê sozinho os campos `youtube_*` da ficha: basta preencher,
  sem parâmetro manual — o bloco entra no artigo automaticamente.
- Campo `youtube_id`: só o ID de 11 caracteres (ex.: `dQw4w9WgXcQ`), nunca URL completa.
- Campos obrigatórios junto: `youtube_titulo` (título real do vídeo),
  `youtube_canal` (nome exato do canal).
- Opcionais e só com dado real: `youtube_resumo` (1 frase do que o vídeo mostra),
  `youtube_pontos` (lista com até 4 bullets do que foi visto — exige ter assistido),
  `youtube_duracao` (texto, ex. `8:32`), `youtube_uploadDate`, `youtube_duracao_iso` (ex. `PT8M32S`).
- Sem `youtube_id` válido na ficha, nenhum bloco é criado (primeiro modelo válido vence).
- Proibido: inventar qualquer campo; copiar título/resumo de memória.

## 4. Como citar no artigo
- O bloco "O que dizem os reviews em vídeo" é inserido automaticamente pelo gerador.
- O redator (humano ou LLM) pode citar o canal em **1 frase no Veredito**.
- Proibido alegar ter assistido ("como vimos no vídeo") quando ninguém assistiu.
- Crédito visível e link "Assistir no YouTube" sempre presentes.

## 5. Conformidade YouTube (resumo operacional)
- Só player oficial incorporado (`youtube-nocookie`), nunca download/reupload.
- Vídeo é **seção** do artigo, nunca o artigo inteiro (exigência dos Termos).
- Crédito ao canal sempre visível.

## 6. Manutenção
- URLs de vídeo entram na checagem do plugin afiliados (via oEmbed):
  removido/privado = alerta na Saúde dos links.
- Na queda: remover o bloco e regenerar, ou trocar por outro vídeo aprovado.
- Cron diário já cobre; Verificar agora para checagem imediata.
