# Protocolo drástico de recuperação operacional — ConexoTech

Data: 2026-11-05. Status: **implementado na branch experimental `ops/fast-track-20261105`, não implantado em produção.**

## Regra-mãe: entregar antes de expandir

O produto mínimo é **um artigo real, revisado, salvo em rascunho e publicado de forma supervisionada, com leitura de confirmação**. Não medir andamento por número de PRs, auditorias, fases ou porcentagens fictícias.

### Via rápida (obrigatória por padrão)

1. Recuperar a **última evidência operacional**, sem refazer instalação: rascunhos #9749/#9763 já demonstram a API WordPress em execuções anteriores; revalidar apenas se houver mudança relevante.
2. Pesquisar, produzir **um** artigo com valor original, fontes verificáveis e título/conteúdo completos. A prévia pode ser entregue sem WordPress e sem aprovação final; não confundir prévia com publicação.
3. Salvar **rascunho privado** por WordPress REST/MCP autenticado já conectado; ou, quando a integração OpenCode/Python existente for mais simples, usar a função `mkt_flow_p0.wp_draft_staging.stage_rss_draft`. Para RSS manual: `CONEXO_RSS_DRAFT=1` habilita somente o rascunho; `CONEXO_RSS_DRAFT_STAGING=1` continua compatível. Destino explícito `WP_URL`: `https://conexotech.com.br` ou `https://staging.conexotech.com.br`; nenhum outro host permitido na função. Credenciais devem vir do ambiente do executor já configurado, nunca do chat.
4. Conferir no WordPress **ID, status=draft, slug, conteúdo e mídia**. Não recriar o mesmo artigo se o slug já estiver ocupado. Erro ou timeout: consultar antes de repetir.
5. Realizar revisão factual e substantiva, incluir imagem com direitos, links internos e SEO atual com Rank Math. Solicitar aceite explícito da **versão específica** para publicar/agendar. Se a revisão não estiver pronta, o artigo permanece em rascunho sem bloquear a redação de outros.
6. Publicar/agendar **supervisionadamente** pelas permissões nativas do WordPress quando o Gate não estiver ativo no destino. Se o Gate estiver ativo, respeitar sua autorização atual; não tentar bypass. Conferir status, permalink, corpo, destaque e SEO após a operação; corrigir só a divergência observada.

### O que deixa de ser bloqueio da via rápida

- Staging, snapshot isolado de banco, novas chaves HMAC, SEO 0.5.2, substituição de Rank Math, automação assíncrona, Cloudflare, FTP/SFTP, GitHub Actions, runners Windows, TinyFish, painel, crawler externo, reauditoria geral e fusão dos PRs históricos.
- Esses trabalhos permanecem **separados**, só entram na pauta se houver defeito comprovado na operação atual ou risco real de perda de dados. O staging serve a mudanças de plugins/tema, não como obstáculo à geração de rascunhos.
- Um executor não possui exclusividade: Work, OpenCode ou cliente já autenticado podem cumprir o mesmo contrato. **Um operador de escrita por vez** para evitar duplicações.
- A implantação de Gate assinado e Native SEO continua projeto futuro de automação estrita; não é pré-requisito para uma publicação manual revisada quando o Gate não está instalado/ativo no ambiente-alvo.

### Quatro salvaguardas curtas (não são burocracia)

1. Não expor segredos nem ampliar permissões administrativas por conveniência.
2. Não publicar sem revisão factual/substantiva e aceite da versão; rascunhos não exigem isso.
3. Não apagar/alterar conteúdo publicado sem possibilidade de recuperação e escopo conhecido.
4. Não afirmar sucesso sem retorno real e readback. Se o site está saudável, **não tirá-lo do ar** por conveniência; indisponibilidade exige causa técnica e autorização específica.

### Critérios objetivos de conclusão

- **MVP editorial:** artigo revisado → draft ID confirmado → aceite → publish ID/link confirmado → leitura de confirmação.
- **RSS:** um item de fonte real → um rascunho privado verificado sem duplicata; depois aumentar volume.
- **Automação estrita:** assinatura, idempotência e recuperação em uma execução E2E própria, sem bloquear MVP.
- **Infraestrutura:** somente se a operação realmente exigir; um único teste proporcional ao arquivo alterado, sem auditoria repetida.

### Regra de parada

Dois bloqueios consecutivos na mesma ferramenta = parar de configurá-la; recuperar o caminho anterior comprovado. Não iniciar outra arquitetura. Para cada alteração, registrar no PR apenas: **o que falhou, o que mudou, teste e resultado, próxima ação**.

### Limites de implantação desta branch

A alteração técnica nesta branch faz só duas coisas: (A) aceita `CONEXO_RSS_DRAFT=1` como alias explícito da flag legada; (B) admite o staging como destino opcional na mesma função de rascunho, mantendo destino em lista fechada, idempotência por slug, `status=draft` e readback. **Não ativa qualquer flag, não configura credenciais, não dispara RSS, não escreve no WordPress e não publica.** Fluxos de escrita no ambiente atual dependem da ferramenta autenticada acessível na execução.
