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
  tests/test_fundamental_identity.py tests/test_ponte_editorial.py
python3 -m pytest -q
```

Ajustar os nomes dos testes ao conteúdo real do checkout, sem inventar resultados.

## Registro obrigatório

Sistema operacional e versão; versão do Python; SHA do checkout; comandos executados; quantidade de testes aprovados; falhas e causa; presença de credenciais reais (deve ser **não**).

## Estado da etapa

**BLOCKED** — aguardando ambiente Linux. Nenhuma credencial de produção deve ser usada.
