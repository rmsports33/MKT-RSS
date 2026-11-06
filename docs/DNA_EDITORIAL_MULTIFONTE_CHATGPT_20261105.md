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
