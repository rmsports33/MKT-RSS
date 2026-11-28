# Plano de validação Linux do Bot Redator — 28/11/2026

PR de referência: `bot-redator-artigo` #6. SHA: `418be3556d15c001e5882e8c345626b0d78ea138`.

## Situação atual

Não há executor Linux disponível neste momento:

- WSL 2 sem distribuição instalada (`wsl --list --verbose` não retorna distro);
- Docker Desktop instalado, mas sem serviço ativo (daemon inacessível);
- nenhuma VPS listada;
- GitHub Actions e CircleCI fora da estratégia.

Portanto **nenhum teste Linux foi executado** e nada pode ser declarado validado.

## Caminhos possíveis — decisão do proprietário

| Opção | Característica | Risco |
|---|---|---|
| A — Codespaces | Linux em nuvem; verificar disponibilidade e limites da conta | depende da conta; não contratar sem verificar |
| B — VM já existente | reaproveitar ambiente disponível | pode não existir |
| C — WSL2 local | sem custo, mas cria dependência do computador pessoal | não atende à independência de máquina |

## Comandos a executar no ambiente escolhido

```bash
git clone --single-branch --branch docs/editorial-quality-contract-20261126 \
  https://github.com/rmsports33/bot-redator-artigo.git
cd bot-redator-artigo
git checkout 418be3556d15c001e5882e8c345626b0d78ea138
python3 --version
python3 -m pip install -r requirements.txt
python3 -m pytest -q tests/test_editorial_prompt_contract.py \
  tests/test_fundational_identity.py tests/test_ponte_editorial.py
python3 -m pytest -q
```

Ajustar os nomes dos testes ao conteúdo real do checkout, sem inventar resultados.

## Registro obrigatório

Sistema operacional e versão; versão do Python; SHA do checkout; comandos executados; quantidade de testes aprovados; falhas e causa; presença de credenciais reais (deve ser **não**).

## Tentativa local em 28/11/2026

Opção escolhida pelo proprietário: Docker Desktop local. Executado:

1. `Start-Process ...\Docker Desktop.exe` → `docker info` retornou `Docker Desktop is unable to start`.
2. Log do backend: `engine linux/wsl failed to start: checking preconditions: WSL update required`.
3. `wsl --update` → `O serviço não pode ser iniciado porque está desativado ou não tem dispositivos ativados associados`.
4. Reinício do Docker Desktop → mesmo erro.

Não foi possível iniciar o daemon. Habilitar o serviço WSL ou instalar uma distro exigiria mudança de configuração do sistema/administrador, que não foi autorizada. Nenhum contêiner foi criado e nenhum teste do Bot Redator foi executado.

## Resolução em 28/11/2026

Após instalação do WSL 2 com Ubuntu e reinício do Docker Desktop, a validação foi executada em contêiner `python:3.11-slim`:

- Linux `6.18.58.1-microsoft-standard-WSL2`, Python 3.11.18;
- SHA `418be3556d15c001e5882e8c345626b0d78ea138`;
- testes focados: **16 aprovados**;
- suíte completa: **143 aprovados**;
- nenhuma credencial real usada.

Evidência versionada no PR #6: `bot-redator-artigo/docs/LINUX_VALIDATION_EVIDENCE_20261128.md`, commit `f514e5d`.

## Estado da etapa

**PASS para ambiente Linux.** Homologação e merge do PR #6 continuam dependendo de decisão explícita do proprietário.
