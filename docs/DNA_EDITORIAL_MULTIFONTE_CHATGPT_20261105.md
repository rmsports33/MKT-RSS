# MKT-RSS + ChatGPT: DNA editorial compartilhado e pesquisa com múltiplas fontes

Data: 2026-11-05. Implementação: branch `feat/editorial-dna-multisource-20261105`.
Escopo: redação e **intercâmbio para revisão**. Sem deploy, sem publicação e sem serviço novo.

## O que muda

O MKT-RSS continua motor de **coleta + filtragem + extração + redação + SEO + imagem + WordPress**. Não foi transformado em simples alimentador de pautas.

- `mkt_flow_p0/editorial_identity.py` centraliza as instruções de voz ConexoTech, alinhadas ao `conexo-os/docs/EDITORIAL_DNA_V1.md`.
- `mkt_flow_p0/rewriter.py` usa esse mesmo DNA na instrução de sistema. A redação deixa de depender exclusivamente da matéria original **quando recebe** informações complementares identificadas.
- Fontes complementares continuam marcadas **PENDING_HUMAN_REVIEW**: URL declarada não é prova de autenticidade nem de exatidão. O redator deve atribuir a informação e não inventar medições.
- O retorno de `reescrever_materia` inclui `editorial_handoff` com identidade, origem RSS, fontes, Markdown, SEO, hash de versão e revisão pendente. Ele pode ser aberto pelo ChatGPT e também fornece `metadata` e `markdown` compatíveis com o renderizador offline existente.
- O `pipeline_rss.processar_item` recebe `contexto_complementar` e repassa esse conteúdo ao redator, sem criar novo publicador. O CLI aceita `--research-context` para uma pauta específica.

## Como fornecer pesquisa complementar, sem nova integração

Crie um JSON de pesquisa (apuração feita por ChatGPT ou outro pesquisador, **sem assumir que já foi verificada**):

```json
{
  "source_url": "https://veiculo.example/noticia-especifica",
  "sources": [
    {
      "name": "Fonte oficial",
      "url": "https://fabricante.example/ficha",
      "facts": [
        "A ficha técnica indica uma função concreta que merece conferência editorial."
      ]
    }
  ]
}
```

- `source_url` precisa corresponder **exatamente** à URL do item recebido pelo RSS. Sem correspondência, o contexto é ignorado e o pipeline emite `research_context_not_matched`; nunca atribui a pesquisa à pauta errada.
- `sources` admite até oito fontes HTTPS; cada uma pode conter até oito afirmações com até 600 caracteres. URLs com credenciais, HTTP e campos inesperados são recusados.
- Exemplo de execução pelo ambiente **já configurado** para o MKT-RSS, sem exigir computador físico do usuário:

```bash
python pipeline_rss.py --limit 1 --research-context pesquisa.json
```

- Mantenha a execução de WP em **rascunho** usando o fluxo já existente e apenas se houver credenciais/flags previamente configuradas. Esta alteração **não ativa** `CONEXO_RSS_DRAFT`, não usa Actions e não chama WordPress por si só.
- No resultado do pipeline, `editorial_handoff` traz um objeto para revisão por ChatGPT. O conteúdo é exportável como JSON. Se a entrega não tiver metadados mínimos, o handoff é omitido sem descartar a redação.
- A revisão pelo ChatGPT deve conservar as URLs de origem e a identidade editorial. Toda alteração no Markdown exige **nova versão/hash** e revisão; o handoff nunca contém `approved=true`.

## Critério de aceite

1. Redação original sem pesquisa complementar mantém caminho compatível.
2. Enriquecimento com duas fontes preserva URLs e explicita revisão pendente.
3. Um artigo enriquecido pode ser enviado ao `editorial_core_offline` usando `handoff.metadata` como JSON e `handoff.markdown` como arquivo Markdown, obtendo prévia e relatório offline.
4. Nenhum dos passos aprova publicação nem contorna o Gate instalado.

## Limites assumidos

O MKT-RSS **ainda não faz pesquisa complementar automática por conta própria** neste patch. O contexto precisa vir de um mecanismo de pesquisa existente ou de um pesquisador e corresponder ao item RSS. O transporte de handoff para um ChatGPT conectado também não é agendado automaticamente; o pacote existe no retorno JSON e pode ser consumido sem serviço adicional.

A execução real com Groq depende de chave e ambiente já existentes e não foi realizada nesta branch. Mudanças de provedor de IA e publicação são tarefas independentes.

## Compatibilidade

O PR #39 continua a integração maior em aberto. Esta branch parte de `ops/fast-track-20261105` e mantém os arquivos e contratos existentes. Não exige staging, migração Native SEO nem GitHub Actions para **rascunhos**; a revisão e autorização específicas permanecem obrigatórias para publicação.

## Fechamento do intercâmbio (06/11/2026)

O CLI agora pode persistir a saída do MKT-RSS como arquivo JSON, **mesmo se a escrita de rascunho no WordPress estiver desativada**:

```bash
python pipeline_rss.py --fonte tecnoblog --limit 1 --research-context pesquisa.json --handoff-dir output/handoffs --handoff-only
```

- O arquivo é criado sob `output/handoffs/rss_<hash_da_url>-<prefixo_hash_da_versao>.json`; a mesma versão não é sobrescrita e uma revisão de texto gera arquivo distinto.
- `--research-context` só é aplicado quando `source_url` é exatamente a URL do item RSS; caso contrário, `research_context_not_matched` é reportado. Não combinar com `--editorial-package` nem com `--queue-only`.
- O retorno em stdout inclui `handoff_path`; falhas na persistência são reportadas como `handoff_error` sem duplicar escrita em WordPress.
- A integridade do arquivo é verificável **offline**, por quem recebeu o JSON:

```bash
python -m mkt_flow_p0.editorial_identity --verify-handoff output/handoffs/arquivo.json
```

- A validação rejeita edição sem novo hash, alteração do status de revisão, declaração de publicação, URLs conflitantes e claims sem origem. **Hash íntegro não significa informação verdadeira**, não equivale à revisão humana e não autoriza publicar.
- Para operar em modo apenas saída editorial, mantenha `CONEXO_RSS_DRAFT` desativado; Groq/LLM continua sendo exigido pelo caminho produtivo atual. Este patch não instala LLM nem cria agendador.

### Evidência executada nesta sessão

- Arquivo `mkt_flow_p0/editorial_identity.py` copiado integralmente para o ambiente de teste e conferido por `git hash-object` = `318599a270f45e406d51a8d47631d82000e73403`, idêntico ao blob no GitHub.
- `tests/test_editorial_handoff_operational.py` conferido por blob SHA `4123da61785af100b7c7f0fcbe2beb37bcc9e731`.
- `pytest -q -k 'not package_remains_compatible_with_existing_editorial_renderer'`: **14 PASS**, um teste não executado porque o checkout integral com dependências não estava disponível.
- Pacote real do piloto Android: validação positiva, três URLs e seis claims pendentes, rejeição de cinco adulterações, persistência idempotente e criação de segunda versão, sem uso de rede, Actions, Groq nem WordPress.
- O pipeline completo **não** foi executado nesta sessão, porque o clone público por `git` retorna `Could not resolve host: github.com`; o conector GitHub permite commits mas não executa Python. A próxima verificação em runtime é `pytest` da suíte integral do repositório e `pipeline_rss.py --limit 1 --handoff-dir ...` com Groq já configurado, sem publicar.

**Não disparar GitHub Actions só para gerar esta evidência**. Não criar serviços redundantes para superar o bloqueio DNS do executor da sessão.

### Proteção para execução real — 06/11/2026

Use **`--handoff-only`** para gerar um pacote revisável sem gravar no WordPress, mesmo que `CONEXO_RSS_DRAFT=1` esteja habilitado no ambiente. A opção também exige **`--fonte NOME --limit 1`** para limitar o ensaio a uma fonte e uma pauta, evitando chamadas inesperadas à API de IA. O nome da fonte deve existir em `FEEDS_PADRAO`; no exemplo, `tecnoblog` é apenas ilustrativo: o campo `source_url` da pesquisa precisa coincidir com o URL real de uma notícia daquela fonte. A opção exige `--handoff-dir` e não pode ser combinada com `--dry-run`, `--queue-only` ou `--editorial-package`. Ela executa a extração e o modelo já configurado, portanto **não garante ausência de custo da API de IA**. Antes de rodar, confira se o provedor e a quota existentes permitem a execução sem gasto.

O status da pauta neste modo é `pacote_editorial_criado`, com `escreveu=false` e `review_status=PENDING_HUMAN_REVIEW`. Se o pacote falhar na validação ou gravação, a ação é `falha`, e **nenhuma postagem remota é tentada**. A pauta não é marcada como vista neste modo; futuras execuções podem gerar nova versão, que será salva separadamente.

Sem `--handoff-only`, o comportamento anterior de `CONEXO_RSS_DRAFT=1` permanece: o pipeline pode enviar um **rascunho privado** ao WordPress configurado. Apenas `--handoff-dir`, isoladamente, **não desabilita** essa escrita remota. A decisão entre exportação offline e rascunho WP deve ser explícita.

Testes adicionais no GitHub: `tests/test_pipeline_handoff_only.py` (sem rede por mocks); execução integral desses novos testes está pendente do checkout real, embora o módulo isolado de handoff tenha 14 testes offline aprovados. Não declarar a execução do Groq/RSS a partir desses testes.

## Meta entregue em 06/11/2026 — importar artigo real sem Groq nem WordPress

Quando o redator Groq/runner RSS estiver indisponível, o MKT-RSS pode receber artigo produzido e pesquisado pelo ChatGPT **sem perder sua identidade editorial**. Isso é um caminho complementar, não a substituição do coletor/redator RSS original.

Arquivo novo: `mkt_flow_p0/editorial_import.py`. Entrada JSON estrita:

```json
{
  "source_url": "https://developer.android.com/ai/appfunctions",
  "source_name": "Android Developers",
  "article": {
    "titulo_seo": "Android e agentes de IA",
    "meta_description": "Uma explicação verificada dos recursos Android.",
    "slug": "android-agentes-de-ia",
    "texto_markdown": "Corpo completo do artigo Markdown, com pelo menos 200 palavras"
  },
  "research": {
    "sources": [{
      "name": "Documentação complementar",
      "url": "https://developer.android.com/blog",
      "facts": ["A documentação explica as funções utilizadas por assistentes."]
    }]
  }
}
```

Execução **sem fazer rede nem escrever em WordPress**:

```bash
python -m mkt_flow_p0.editorial_import --import-article artigo-importacao.json --handoff-dir output/handoffs
python -m mkt_flow_p0.editorial_identity --verify-handoff output/handoffs/rss_...json
```

O arquivo resultante é verificável por SHA-256, preserva a fonte inicial, links complementares, dados SEO, voz ConexoTech e `PENDING_HUMAN_REVIEW`. Uma edição cria outra versão e não transfere aceitação anterior. Este comando **não gera texto por IA, não pesquisa e não coleta RSS**: importa texto já produzido, para coexistir com o pipeline original.

**Evidência real:** importado o artigo sobre agentes Android (1.029 palavras, 3 fontes, 6 alegações complementares pendentes), obtendo novamente o SHA de versão `307051c85ed2616ca4b69b4a9350aff32d91b5f310c74fc23cc683b94801d92d`. Testes locais `python -m pytest` totalizaram **31 PASS e 1 teste não executado** por ausência do renderizador integral no checkout parcial. Dois arquivos têm blobs idênticos entre execução e GitHub: `editorial_import.py` (`eaef5746c8f22e5e8e2a55ae2607db1a18b66098`) e `test_editorial_import_public.py` (`de3ff933e8c030a3e507cb17a44412b4c4ab34b0`).

**Pendências separadas:** (1) testar os módulos do pipeline `tests/test_pipeline_handoff_only.py` num checkout integral; (2) executar a coleta de RSS e o rewriter do MKT-RSS com provedor realmente configurado e quota conhecida; (3) comprovar o rascunho privado no WordPress pelo executor MKT-RSS, sem publicar antes de aprovação. Não reabrir staging nem criar serviços apenas por causa dessas pendências.

## Publicador de rascunhos: correções de confiabilidade (06/11/2026)

Foram reproduzidas falhas em testes com código cujo blob Git SHA coincidia com o repositório: (1) mudança de título gerava novo slug para uma mesma URL, (2) draft antigo era declarado entregue sem comparar conteúdo e (3) readback do POST não verificava o corpo; além disso, (4) a consulta REST por slug não explicitava `status=draft` e outros estados, podendo ignorar rascunhos.

**Correção aplicada** em `mkt_flow_p0/wp_draft_staging.py` (blob SHA `b5a023613abf402a96be97045573fa68fbe4ba60`):
- Slug de novas pautas baseado **na URL de origem**, invariável quando a IA altera o título. A rotina também procura o slug legado com o **mesmo título atual**, mas um post legado cujo título mudou antes da migração pode exigir reconciliação manual — não presumir migração global.
- Consulta explícita por status `draft,pending,publish,future,private`, contexto `edit`, sem criar o post se a listagem falhar.
- Ao encontrar um post, lê `content.raw` e `title.raw` por ID e exige correspondência exata da versão atual; versão divergente retorna `bloqueado` e não sobrescreve.
- Após um POST, exige leitura confirmada de ID, slug, título, conteúdo e status `draft`; readback divergente retorna falha sem retry automático. Resposta 201 sem ID confiável reporta `escrita_indeterminada=true`.

**Evidência:** módulo Python exato copiado do GitHub, hash do arquivo confirmado; suíte offline focal com **16 passed** (13 testes de contrato, três regressões reproduzidas e depois corrigidas). A suíte do repositório foi atualizada em `tests/test_wp_draft_staging.py`; seus casos ainda não foram executados no checkout integral. Nenhum teste dessa suíte chamou o WordPress real.

**Importante:** estas correções **não** fazem upload automático de imagem destacada nem homologam o executor Groq. O WordPress #9768 foi salvo por conector MCP supervisionado e confirmado por leitura, não pelo `stage_rss_draft` Python.
