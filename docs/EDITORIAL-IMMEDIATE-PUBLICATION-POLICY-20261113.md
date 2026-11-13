# Política permanente de publicação editorial — 13/11/2026

## Decisão do proprietário
**Não agendar matérias.** Uma vez que o MKT-RSS tenha concluído um artigo completo, seus anexos/licenças, fontes, revisão de SEO e links internos, o post permanece `draft` até a revisão autenticada. **A confirmação humana no Gate Único inicia a publicação imediata na mesma operação**, via writer assinado `cxeg_write(intent=publish)`. Não usar `future`, cron Hostinger ou GitHub Actions de publicação para o fluxo normal.

### Fluxo de uma sessão no WordPress
1. MKT-RSS (autor técnico WP ID4) entrega artigo integral como draft com título, SEO, fontes, licença ou crédito, capa própria e links apenas para posts públicos.
2. Proprietário/revisor WP ID3 abre [Conexo — revisar e publicar](https://conexotech.com.br/wp-admin/tools.php?page=conexo-gate-revisar-lote) e seleciona até 12 rascunhos elegíveis.
3. Página carrega dois previews autenticados (390px e 1440px) sob demanda; script local calcula overflow horizontal, tabelas largas e imagens quebradas sem Actions e sem serviço pago. **A análise automatizada não substitui confirmação humana de qualidade visual e textual**.
4. Para cada versão, revisor confere os 13 critérios, registra observação editorial e confirma. Uma confirmação final vinculada aos hashes atuais emite o parecer autenticamente via Gate e executa o writer de publicação imediatamente.
5. O Gate exige assinatura HMAC, aprovação por versão, autor diferente do revisor e lê o WordPress depois da escrita. Se qualquer pré-checagem falhar, nada é publicado. Se alguma execução ficar incerta, interromper sem retry e reconciliar.
6. Se Gate já contém parecer vigente da versão, a mesma tela aceita **publicar agora** sem preencher ou assinar novamente. Histórico dos seis posts 9810/9813/9814/9815/9816/9817 está em `publish`; não reabrir, replicar ou reagendar.

### Ambiente
- Plugin integrado **Conexo Gate — Publicação Imediata 0.3.0** substitui os arquivos da antiga **Agenda Nativa** na mesma pasta `wp-content/plugins/conexo-gate-agenda-nativa`; mantém Gate Único rc5 como autorizador.
- ZIP v0.3.0 e rollback v0.2.2 no Google Drive `/ConexoTech`. UpdraftPlus instalado no WordPress e arquivos do backup no Google Drive `/UpdraftPlus` (DB, plugins, temas, uploads, MU-plugins e outros). **Não executar restauração integral**, por decisão explícita do proprietário.
- Não agendar nem criar tarefas de servidor; o WP-Cron do WordPress pode continuar existindo para manutenção normal do site, mas **não é usado para esperar data de matéria**.
- GitHub permanece para desenvolvimento, testes e versionamento do MKT-RSS, não para publicar por artigo.

## Limites de homologação
- Testes isolados (PHP lint, 33 verificações de Gate e QA visual) PASS, CI da PR #73 aprovado, plugin 0.3.0 instalado e ativo. Primeiro caso de **novo artigo** ainda precisa de observação de publicação real para provar a ponta a ponta desta nova versão; **não criar aprovação humana artificial**.
- O auditor visual via iframe funciona na sessão autenticada do proprietário, quando a prévia abre no mesmo domínio. Se houver bloqueio por frame/login, mostra `medição automática indisponível` e requer leitura manual, sem inventar PASS.
- SEO Native assinado é finalizado se o signer oficial estiver disponível, caso contrário exibir necessidade de verificação; manter Rank Math para a saída pública. Não declarar contrato Native concluído sem recibo.
- Backups presentes **não significam restauração integral testada**; não é requisito da política atual.

## Repositórios e evidências
- [Plugin 0.3.0 — PR #73](https://github.com/rmsports33/-site-conexotech/pull/73)
- [Seis posts publicados em 12/11](https://github.com/rmsports33/MKT-RSS/blob/master/docs/editorial-evidence/six-publication-verification-20261113.json)
- [Pacote anterior 0.2.2 no Drive](https://drive.google.com/file/d/1oDng-rZvRY2QV2lNU1aVdLLYxSsjJs8W/view)
- [Pacote imediato 0.3.0 no Drive](https://drive.google.com/file/d/1KxCcpaTfTRw-To-e5ZiawOgQI-_YbInw/view)
