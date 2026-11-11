# Marco MDA AUTO — A/B controlado de qualidade editorial

**Status atualizado em 10/11/2026:** experimento A/B real concluído pelo Groq Free (PR #88, workflow #42917583190), com **8 artigos completos em 4 pares**, evidência cifrada e nenhum write/publicação WordPress. Os artigos originais foram preservados na Biblioteca privada e organizados em caderno cego; a segunda análise assistida identificou falhas factuais e **não demonstrou melhora editorial universal**. A instrumentação do Gate e da voz foi corrigida no PR #89. **Ainda falta parecer humano independente, direitos de imagem, checagem factual final e prova real de publicação bloqueada pelo Gate.**

## Por que o caderno anterior não bastava

As versões A/B antigas do guia #9798 eram revisões de datas e condições distintas, criadas antes do adaptador MDA. Servem para comparar edição, mas **não isolam o efeito do MDA**. Não usar essa comparação antiga como resultado do novo módulo.

## Experimento reproduzível

O único tratamento muda um sufixo da instrução de voz dentro do prompt do MKT-RSS; sem novos agentes ou jornalistas fictícios.

- Controle: montar_prompt(..., voice_variant="control") — usa briefing e DNA existentes sem apêndice MDA.
- Tratamento: montar_prompt(..., voice_variant="mda") — acrescenta exclusivamente writing_voice_guidance(brief); MDA continua sendo o padrão da produção após PR #86.
- Variáveis comuns: mesmo título, artigo-fonte completo, links/documentos citados, briefing de seis campos, modelo, temperatura, limite de saída, contexto, data da coleta e regras factuais. Diferença nos insumos invalida a comparação.
- Fonte: os rascunhos WordPress são material de entrada privado, não fatos automaticamente comprovados. A leitura de uma URL não comprova que a afirmação apareça nela.
- Custo: preparar e embalar pares não chama IA; gerar os dois artigos reais exige chamadas autorizadas e pode consumir créditos. Este PR não aciona geração.

## Componentes reutilizáveis, sem executor paralelo

1. scripts/prepare_mda_ab.py prepara prompts completos offline, para caso único (schema conexo-mda-ab-source/1) ou lote de até 8 casos (schema conexo-mda-ab-batch/1). Compara caractere por caractere que a única diferença é a orientação MDA. Grava hashes SHA-256, parâmetros e arquivos privados. Nunca versionar as pastas de saída.
2. scripts/seal_mda_ab_review.py recebe dois artigos realmente gerados, prepara pacote cego de textos integrais, sorteia A/B, mantém chave em pasta privada separada. A ferramenta NÃO atesta a origem dos artigos, que requer recibos autênticos de execução.
3. tests/test_mda_controlled_ab.py testa paridade de entradas, contrato/hash, privacidade, rejeição de dados inválidos, ausência de chamada de provedor e proibição de aprovação automática.
4. O corpus real está guardado em documento privado do Google Drive, fora do GitHub público. São quatro entradas completas: guia #9798, notícia #9635, análise #9687 e comparativo #9681. Os posts originais não são alterados.

### Comando offline com corpus privado

Exportar o JSON privado para arquivo fora do repositório e executar:

    python -m scripts.prepare_mda_ab --input /private/mda_cases.json --out /private/mda_ab_prompts

São produzidas quatro subpastas com control.prompt.txt, mda.prompt.txt e manifest.private.json. Mesmo com o preflight, generated_articles_present continua false.

Somente **após geração real de dois artigos completos com mesmo modelo e parâmetros**:

    python -m scripts.seal_mda_ab_review --manifest /private/mda_ab_prompts/guia-9798/manifest.private.json --control-article /private/outputs/guia-control.md --mda-article /private/outputs/guia-mda.md --blind-dir /private/avaliador/guia --private-key-dir /private/chaves/guia

Não compartilhar a chave com o avaliador. Erro ou resposta truncada mantém o caso pendente.

## Protocolo de aceitação cega por gênero

Manter os cinco critérios vigentes: necessidade do leitor, recorte, contribuição, voz e limites das fontes (0–4). Exigir trechos e justificativas. Verificar função dos parágrafos, progressão, contradição real e fechamento, sem premiar volume ou artificialidade.

Critério para demonstrar ganho: contribuição e voz melhores no MDA em cada gênero avaliado, sem novas falhas factuais. Registrar também empates e regressões, sem omitir resultados negativos. O avaliador deve ser humano, independente e não conhecer a identidade das variantes. Avaliação assistida por IA não substitui parecer externo.

Direitos de imagem, verificação factual, Gate Editorial WordPress e aprovação da versão continuam separados. Não publicar automaticamente.

## Estado deste marco

- [x] Controle e MDA diferem apenas por uma orientação.
- [x] Mesmo insumo e parâmetros declarados para cada par.
- [x] Lote privado de quatro gêneros completo e estruturado.
- [x] Instrumentação de sorteio A/B e chave separada.
- [ ] Duas gerações completas reais por gênero em provedor autorizado.
- [ ] Recibos de execução e versões cifradas/privadas.
- [ ] Avaliação humana externa, cega e justificada.
- [ ] Apuração factual das duas versões e aceitação por gênero.

**Conclusão:** o experimento foi preparado tecnicamente; melhoria editorial ainda não foi comprovada.


## Evidência da execução offline em quatro casos

Após a integração do PR #87 (merge `8f07c10759beab529084a6faa750a857e295149d`), foi executado, com código restaurado de arquivos GitHub verificados por SHA de blob, o preparo real sobre o corpus privado exportado do Google Drive. **Resultado de `scripts.prepare_mda_ab`: 4 casos, 8 prompts, exit code 0; nenhuma chamada Groq/WordPress.** O preparador conferiu que em cada par a orientação MDA era a única diferença do prompt completo. Códigos, textos e hashes estão armazenados **somente em área privada** da Biblioteca ChatGPT:

- `/ConexoOS/AuditoriaEditorial/mda_ab_prompts_privados_20261110.zip` (prompts e manifestos privados).
- `/ConexoOS/AuditoriaEditorial/mda_ab_preflight_resumo_20261110.json` (apenas hashes/estados).
- Corpus de entrada estruturado em documento privado no Google Drive, nunca no repositório público.

| Caso | Gênero | Fonte completa | Contraste MDA |
|---|---|---|---|
| guia-9798 | guia | snapshot do rascunho #9798 | prompt controle/MDA verificado |
| noticia-9635 | notícia | snapshot do rascunho #9635 | prompt controle/MDA verificado |
| analise-9687 | análise | snapshot do rascunho #9687 | prompt controle/MDA verificado |
| comparativo-9681 | comparativo | snapshot do rascunho #9681 | prompt controle/MDA verificado |

A origem factual continua pendente de revisão independente. **Atualização:** os oito artigos A/B foram gerados posteriormente pelo run #42917583190 e permanecem privados. O marco de qualidade dependerá de parecer humano independente, checagem factual e comparação dos resultados, não apenas da geração. Os documentos temporários usados apenas para transportar cópias de código foram apagados do Google Drive.


## Prova real da geração e revisão assistida — 10/11/2026

**PR #88 integrado:** https://github.com/rmsports33/MKT-RSS/pull/88. **Workflow real:** https://github.com/rmsports33/MKT-RSS/actions/runs/42917583190. Recibo público: `COMPLETE_GENERATION_REVIEW_PENDING`, 4 pares, 8 chamadas ao Groq `openai/gpt-oss-120b`, 0 escritas WordPress, 0 publicações, evidências AES-GCM/RSA-OAEP cifradas. As quatro pautas originais continuam como rascunhos. Os artigos, prompts e textos-fonte estão no armazenamento privado `/ConexoOS/AuditoriaEditorial/MDA_AB_20261110/`, com chave A/B **separada** do material do revisor; não publicar o corpus no GitHub.

**Pré-avaliação do GPT-6 (NÃO humana e não totalmente cega)**, com critérios leitor/recorte/contribuição/voz/fontes, escala 0–4:

| Gênero | Controle (soma/20) | MDA (soma/20) | Evidência limitadora |
|---|---:|---:|---|
| Guia iPhone | 17 | 14 | MDA introduziu contradição sintoma→ajuste, com risco de orientar desligamento de recurso desejado |
| SpaceSail | 12 | 16 | MDA apresentou mais clareza; controle acrescentou preço internacional sem lastro para Brasil; verificar certificado e disponibilidade |
| IA nos jogos | 11 | 12 | Ambos especulam causalidade sem base adequada; controle reintroduziu percentual inconsistente |
| Galaxy A36/A16 | 14 | 16 | MDA mais prudente; controle sugeriu gravação 4K no A16, recurso incompatível com especificação oficial |

**Conclusão técnica limitada:** zero dos quatro pares satisfizeram integralmente a exigência prévia de melhorar **ao mesmo tempo** voz e contribuição sem regressão factual. Esse resultado é exploratório, sujeito à revisão humana independente, e não prova nem refuta sozinho a eficácia futura do adaptador. Não ajustar notas por saber qual braço era MDA. Não selecionar apenas os resultados favoráveis.

**Gate pós-IA existente aplicado sobre todos os oito artigos:** alertas numéricos frequentemente incluem falsos positivos por títulos numerados ou apresentação de milhares/unidades; `SEM_ALERTAS` não detecta contradição semântica. O PR #89 (https://github.com/rmsports33/MKT-RSS/pull/89) corrigiu a normalização de quantidades e a redação das instruções MDA sem reexecutar Groq. CI: **1.123 testes do núcleo aprovados, 1 ignorado, 11 subtestes e 52 testes do redator aprovados**; validação editorial Conexo OS aprovada.

**Aceite editorial NÃO declarado:** o pacote com os oito textos integrais já foi montado para um avaliador humano externo, com a identidade dos braços em chave privada à parte. Faltam parecer cego assinado, fontes conferidas por versão, correção de fatos nas cópias de trabalho, imagens licenciadas e prova do Gate WordPress no caminho real. O status de publicação permanece `BLOQUEADO`.

## QA-v2 e bloqueio de tabela quebrada — complemento de 10/11/2026

Após a geração real de oito artigos do workflow #42917583190 e a avaliação assistida que mostrou resultados mistos, foram preparadas **quatro cópias de trabalho QA-v2**, sem alterar os oito braços experimentais congelados nem os rascunhos WordPress. Elas estão exclusivamente na Biblioteca privada em `/ConexoOS/AuditoriaEditorial/MDA_AB_20261110/mda_4_versoes_qa_v2_privadas.zip`; há também um caderno privado no Google Drive para parecer externo, com notas ainda em branco. Nenhum manuscrito privado foi enviado ao repositório.

A verificação documental das cópias utilizou fontes oficiais: manuais Apple para autocorreção, teclado e idiomas; ficha brasileira Samsung SM-A166M, comunicado Galaxy A36 e especificações de atualização/IP/carregamento; pesquisa GDC 2026 e Quantic Foundry 2025 para distinguir grupos e dados; Exame e espelho do certificado Anatel para destacar que homologação **não equivale** a assinatura disponível. Essas consultas apoiam correções pontuais, não constituem aceite factual integral nem substituem o processo regulatório primário.

**Mudanças QA-v2:** guia agora começa pela reversão pontual, qualifica disponibilidade de previsões por idioma e corrige o menu Teclados; SpaceSail tem tabela de três colunas válida e ressalvas de disponibilidade/certificado; análise retira inferência de silêncio dos jogadores e números de produtividade de hardware sem fontes primárias rastreadas; comparativo retira garantia de suporte a contar da compra e evita veredito de processador sem testes. Cada cópia contém referências identificadas e checksum completo do arquivo, distinto do hash do corpo sem o aviso de revisão no manifesto anterior.

**Prevenção permanente:** [PR #90](https://github.com/rmsports33/MKT-RSS/pull/90) integrado à master, commit `85e54f7511aa98ef52025a90e6f4312fbfb0f0cb`. A prontidão editorial detecta colunas irregulares ou falta de separador em tabelas Markdown padrão, desconsidera blocos de código e mantém `pronto_para_publicar=false`. CI do PR: **1.127 testes aprovados, 1 ignorado, 11 subtestes e 52 testes adicionais do redator**, além de validação Conexo OS verde. Esses testes **não** comprovam qualidade humana, integridade das fontes ou Gate WordPress em produção.

**Status final deste complemento:** pronto para solicitar parecer independente sobre A/B original e revisão factual das quatro cópias QA-v2. Direitos de imagem, prova de bloqueio real pelo Gate 0.1.0-rc5 e aprovação humana vinculada à versão continuam PENDENTES. Não houve nova chamada Groq, deploy, staging ou gravação WordPress neste complemento.
