# Integração editorial MKT-RSS / Conexo OS — checkpoint de 12/11/2026

Estado: PARCIAL. Correções de engenharia implementadas e testadas no ambiente de nuvem; homologação editorial e operacional externa pendente.

## Objetivo original
Analisar a conversa anterior, corrigir lacunas verificadas e executar as recomendações até a conclusão comprovada do fluxo editorial, preservando o Gate e as aprovações humanas.

## Referências verificadas
- Repositório: rmsports33/MKT-RSS.
- PR existente: https://github.com/rmsports33/MKT-RSS/pull/97 — aberto, não mesclado durante a consulta.
- Base desta correção: 543af06c571921fc863644546c831107389df785.
- Branch local: fix/editorial-integration-20261112.
- Commit de código testado: 75e6c8fb2c8155f891d116b7f9a5e3dd82cf8729.
- Núcleo Conexo OS realmente usado nos testes: b485d910c80501d64c5f15ab45366a61832fae17; hashes conferidos pelo transporte existente.
- WordPress conectado pelo plugin: ConexoTech, conexotech.com.br, ativo e acessível.
- Leitura autenticada do artigo 9798: draft, autor 3, imagem destacada 9797. Nenhuma escrita realizada.

## Correções executadas
1. Redator real exige briefing válido antes de abrir o cliente IA. O contrato compartilhado chega à mensagem system enviada ao adaptador do provedor.
2. RSS bloqueia geração quando o planejamento falha, o briefing é inválido ou seu gênero diverge da pauta. Não gasta uma segunda chamada produzindo prosa sem briefing.
3. Comparativo exige briefing inclusive quando forcar=True. As travas de fatos e especificações existentes continuam presentes.
4. Adaptação de artigo importado confere o gênero antes da redação, inclusive com planejador injetado.
5. Testes percorrem os seis gêneros pelo redator existente e pelos módulos reais de importação, HTML, SEO, imagem, prontidão e rastreabilidade. Fontes e artigos são sintéticos; o provedor é simulado. Todos permanecem sem autorização de publicação.
6. Testes antigos receberam briefings explícitos, preservando suas verificações de fatos, custos, transporte e ausência de bypass.
7. Incluída cryptography nas dependências de teste existentes: antes faltava na coleta de test_live_handoff_quality_audit.py.
8. Teste de publicação simulada foi atualizado para exigir trace por versão e executar o preflight real com consulta sintética. Não é recibo Turso verdadeiro.
9. CI preparado para obter o núcleo pelo commit do lock usando CONEXO_CORE_READ_TOKEN, somente leitura e sem persistência. Como conexo-os é privado, ausência desse segredo produz aviso explícito e mantém a integração como não executada; não afirma cobertura remota completa.

## Evidências
PASSOU: 1.255 testes, 13 subtestes; 2 testes ignorados explicitamente. Execução local em Python 3.12. CI usa Python 3.11 e ainda não foi executado para esta revisão.

Comando realmente usado, dentro de /workspace/work/MKT-RSS:

```bash
CONEXO_TEST_CORE_ROOT=/workspace/work/conexo-core-pinned /workspace/work/venv/bin/python -m pytest tests redator-artigo-blogs/tests -q -rs
```

PASSOU: verificação de whitespace; parse YAML do CI e sintaxe Bash dos passos. O parse não comprova execução do GitHub Actions.

SKIP: Python → PHP, pois runtime WASM/PHP e fixture do plugin não estão configurados.
SKIP: descoberta PR43, pois o consumidor e o adaptador de descoberta não compõem o checkout editorial testado. Tentativa com o consumidor real recuperado de 692ad4883e58987e291c9e63918edca727d1dd14 confirmou ausência de mkt_flow_p0.conexo_discovery_adapter; não foi sobreposto código de outra branch para esconder a lacuna.

NÃO EXECUTADO: geração com IA externa; autenticação Turso; escrita/readback do executor no WordPress; revisão humana dos seis artigos; comprovação de fontes e licenças; conferência real do tema em 390/1440; PHP do Gate; CI remoto desta revisão; push, merge, deploy, publicação e ativação de rotina.

## Correções na interpretação da conversa anterior
- Não há comprovação de seis geradores especializados independentes. O código inspecionado tem um redator comum que aceita os seis gêneros e um comparativo especializado. Reutilizar esses caminhos evita criar executores redundantes.
- Briefing e CI verde são requisitos técnicos; não certificam profundidade, fatos, direitos ou aceite humano.
- Revisão assistida pelo próprio provedor não é avaliação humana independente.
- O modo owner já existe nas instruções do projeto: aceite do proprietário não deve ser descrito como revisão por outra pessoa. Não alterei essa política nem os recibos exigidos pelo Gate.
- Testes do transporte antes eram ignorados sem CONEXO_TEST_CORE_ROOT; o CI anterior não comprovava essa integração.
- A existência de conexão WordPress pelo plugin não entrega automaticamente credenciais ao processo Python.
- Nenhum percentual ou prazo da conversa anterior foi promovido a resultado medido.

## Acessos e pré-requisitos pendentes
O usuário escolheu configurar os acessos existentes. A última consulta ao ambiente ainda mostrou secrets=[], runtime_variables=[] e outbound_identities=[]. A ferramenta desta sessão apenas consulta a configuração; não cadastra segredos.

Nas configurações do ambiente de nuvem, cadastrar as conexões já existentes, sem enviar valores no chat:
- GROQ_API_KEY; GROQ_MODEL somente se houver modelo já definido para uso gratuito/autorizado.
- WP_URL, WP_USER, WP_APP_PASSWORD para a identidade de serviço existente, se necessário testar o executor Python. A leitura pelo plugin já funciona sem essa etapa.
- TURSO_DATABASE_URL, TURSO_AUTH_TOKEN e CONEXO_TRACE_TURSO_ALLOWED_HOST. A allowlist deve corresponder exatamente ao host do banco escolhido.
- Rede: api.groq.com e host exato Turso. conexotech.com.br já está permitido.
- CI: CONEXO_CORE_READ_TOKEN no GitHub Actions, com leitura restrita ao núcleo privado. Não reutilizar a chave IA para isso.
- A configuração do transporte assinado ou broker deve ser verificada no destino antes de escolher o modo. Não criar, exportar ou copiar HMAC do servidor por inferência.

## Pendências e impacto
RESOLVER AGORA: disponibilizar acessos e executar homologação real, pois ainda impedem afirmar conclusão operacional.
RESOLVER AGORA: enviar as correções para revisão/CI após autorização concreta. O código está salvo localmente, não no PR remoto.
PENDENTE: testar Gate remoto sem aprovação, versão antiga e replay em ambiente isolado ou operação controlada autorizada; não fazer tentativas de publicação pública como teste.
PENDENTE: seis artigos completos de pautas reais com apuração, licenças, revisão e evidências de apresentação. Nenhum artigo sintético deste teste serve como entrega editorial.
PENDENTE: merge após revisão e CI aplicável; ativação de rotina somente após homologação. Aceite de engenharia não aprova publicação de um artigo específico.

## Próxima ação exata
1. Revisar este pacote e autorizar o envio do commit de código à branch do PR97, sem merge, deploy ou publicação nesta ação.
2. Concluir o cadastro dos acessos no ambiente e conferir prontidão com nova leitura; testar conexões sem revelar valores.
3. Executar um ciclo real por gênero pelo motor existente, registrar hashes e pendências e corrigir o que a execução revelar.
4. Somente após evidências e aceite da versão, concluir integração e operação controlada.

## Nova recomendação
Tornar o resultado da integração com o núcleo um critério visível de aceite no PR: quando CONEXO_CORE_READ_TOKEN estiver configurado, exigir a execução efetiva desse grupo e tratar o aviso de ausência como pendência de homologação. Isso evita confundir o pytest geral verde com cobertura do transporte privado.

## Limites e recuperação
Não foram alterados WordPress, Turso, segredos, DNS, hospedagem, Rank Math, cron, staging ou conteúdo público. Não houve gasto deliberado com provedores. O commit de código pode ser revertido por git revert após eventual integração; o patch entregue se aplica à base do PR97, não diretamente a qualquer versão de master. O Conexo OS original foi preservado, com worktree separado para a revisão fixada.
