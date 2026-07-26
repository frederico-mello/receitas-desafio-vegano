## Why

O software atual exige 4 passos manuais (venv, instalar deps, criar diretório data, rodar pytest). Usuários podem configurar o ambiente e executar testes com um único comando.

## What Changes

- Adicionar `Makefile` com targets para automação completa
- `make install` — configura venv + instala todas as dependências
- `make setup-db` — cria diretório `data/` para banco SQLite
- `make test` — executa suite de testes
- `make dev` — pipeline completo (install + setup-db + test)
- `make clean` — remove artefatos de build/venv
- Atualizar README.md com comandos simplificados

## Capabilities

### New Capabilities
- `onboarding`: automation of environment setup, dependency installation, database preparation, and test execution via Makefile

## Impact

- Novo arquivo: `Makefile`
- Modificado: `README.md` (documentação atualizada)
- Nenhum código Python alterado
