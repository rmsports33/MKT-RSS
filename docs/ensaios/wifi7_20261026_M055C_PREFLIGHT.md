# M05.5-C — Preflight de execução remota
Data: 2026-10-26 | PR #20 | Status factual: NAO_VERIFICADO | WordPress: BLOQUEADO

## CI remota após correção
Commit bb0b08dcc73378cfb1cf32818864f62338d53602:
- CI run https://github.com/rmsports33/MKT-RSS/actions/runs/40333021491 — SUCCESS. Logs: 519 passed (tests) e 52 passed (redator-artigo-blogs/tests).
- Validação editorial run https://github.com/rmsports33/MKT-RSS/actions/runs/40333022167 — SUCCESS.
- Correção de teste legado de autoria isolada na branch: bf5297a5cfc142c3980dc8d04a39723d1d951209. Nenhum código de produção foi alterado por essa correção.

## Análise do mecanismo real
- pipeline_rss.py: processar_item chama extrair_conteudo(url_fonte), rewriter, auditorias; bloqueia escrita com verificacao_factual NAO_VERIFICADO, escreveu False.
- mkt_flow_p0/rewriter.py: provedor Groq; requer GROQ_API_KEY, consulta GROQ_MODEL e contabiliza custo_usd_estimado **após** a chamada.
- .env.example: contém parâmetros de preço estimado para cálculo, não prova orçamento/limite aprovado.
- .python-version: 3.11.13; workflow ci.yml usa Python 3.11. O ensaio cloud deve inicialmente respeitar o Python efetivamente testado e isolar eventual migração a 3.12.
- Não há evidência de limite financeiro pré-chamada aprovado, conta/cota autorizada, nem disponibilidade segura de GROQ_API_KEY no executor. Portanto o gate para chamadas reais permanece fechado.

## Decisão e restrições
Não criar workflow adicional, scheduler, segredo nem disparar chamada Groq sem autorização orçamentária verificável. Reutilizar os workflows existentes. Não usar credenciais de WordPress nem reabilitar publicador. Sem merge ou deploy.

## Próxima implementação necessária
1. Implementar gate financeiro fail-closed ANTES de qualquer chamada Groq (orçamento por execução, limites de tokens, modelo permitido, parada ao atingir orçamento).
2. Criar teste de integração cloud source→modelo→output com credenciais apenas em ambiente autorizado, rede de WP inacessível, uma pauta e evidências persistidas.
3. Validar todas as alegações nos campos de saída e N1–N7. Revisão independente adicional.
4. Em caso de indisponibilidade de credenciais/cota, declarar BLOQUEADO sem fallback para provedor pago.
5. Rascunho WordPress é tarefa futura separada e depende de autorização específica.

**Este checkpoint registra CI real executada; não declara que o pipeline IA real foi executado.**
