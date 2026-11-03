# Memória do Projeto — MKT-RSS / MDA AUTO

## Diretrizes operacionais

- Consultar o [Contrato Operacional](https://github.com/rmsports33/conexo-os/blob/ec190d6b6c62df3235905499ee84eeb75ad9507d/docs/CONTRATO_OPERACIONAL.md), a política de execução e o protocolo de tarefas do núcleo.
- Priorizar entregas do ConexoTech, reaproveitar componentes e evidências e registrar escopo, branch/SHA, critérios, testes, bloqueios e próxima ação na issue/PR.
- Pesquisa de ferramentas é condicional a uma lacuna real. Antes de nova dependência, comparar capacidades existentes e consumidores; não repetir pesquisa em toda tarefa.
- Aplicar o [DNA reconciliado](https://github.com/rmsports33/conexo-os/blob/ec190d6b6c62df3235905499ee84eeb75ad9507d/docs/EDITORIAL_DNA_V1.md): voz inteligente e acessível, estrutura por gênero, fontes rastreáveis e contribuição verificável.
- Reinaldo Mendes é o autor humano; Conexo Insight é voz interna. Não inventar testes, números, preços ou experiências próprias.
- SEM_ALERTAS não comprova factualidade. Preservar o bloqueio de escrita quando o gate factual não estiver integrado.
- Trabalhar em branch isolada, validar proporcionalmente e preservar mudanças preexistentes. Merge, deploy, publicação e custos dependem do escopo autorizado.
- Drive V3 continua oficial; memória não concede autorização. Não ativar publicação ou agendamentos ao aplicar estas diretrizes.



## Correção da decisão operacional — 03/11/2026 (prevalece sobre instruções antigas)

**Executor atual do ConexoTech: ChatGPT Work/ChatGPT-first + WordPress REST/MCP.** Não solicitar criação, deploy ou ativação de executor Python permanente como condição para produzir artigos, gravar rascunhos, revisar ou publicar supervisionadamente. O WordPress já foi testado criando/editando draft #9752; o teste foi movido à lixeira sem publicação. Python do MKT-RSS permanece auxiliar de RSS, testes e transformação, e o modo `CONEXO_RSS_DRAFT_STAGING=1` do PR #39 é opção para quem realmente implantar esse pipeline, NÃO é o executor obrigatório.

**Distinção essencial:** o bloqueio factual no pipeline automático não deve impedir o ChatGPT Work de salvar um rascunho privado via WordPress; contudo, o código antigo do transporte editorial assinado mantém seus controles próprios e **não deve ser contornado** para realizar publicação automática. Quando o Gate está inativo, publicar supervisionadamente pelo WordPress atual requer revisão factual, conferência de imagem/direitos e links, autorização da versão exata e readback. Não pressupor que "execute" equivale a aprovação do artigo #9711 ou qualquer outro.

**Escopo emergencial temporário:** produção/rastreamento em WordPress via Work, depuração de código via Codex Cloud e GitHub. Sem Hostinger MCP, PowerShell, máquina física, novos serviços pagos ou GitHub Actions como pré-requisitos. A engenharia de Gate/SEO 0.5.2 continua separada para automação futura e não bloqueia artigo supervisionado. Se o WordPress existente está operacional, priorizar artigo real, não infraestrutura.

## Escrita editorial controlada — 30/10/2026

As referências antigas acima são proveniência, não a revisão atual. Consumir o
núcleo da PR conexo-os #42 conforme mkt_flow_p0/editorial_core.lock.json; conferir
os hashes antes de importar. Não copiar o motor nem reativar PASS booleano.
Artigo normal usa editorial_transport e a entrada assinada; chamadas MCP diretas
são somente leitura no cliente. stage é prévia técnica, não entrega. Publish e
schedule exigem aceite da versão e ordem específica. Sem fallback, merge,
publicação, chave exposta ou deploy automático por inferência destes arquivos.
A proteção remota só existe após instalar/homologar o MU-plugin correspondente.
