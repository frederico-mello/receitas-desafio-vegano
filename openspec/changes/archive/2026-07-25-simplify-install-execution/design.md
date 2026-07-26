## Context

Projeto Python sem automação de build/instalação. Usuários precisam executar manualmente: criar venv, instalar deps, preparar diretório data, rodar testes.

## Goals / Non-Goals

**Goals:**
- Automatizar setup completo com `make`
- Reduzir friction para novos desenvolvedores
- Manter compatibilidade com workflow existente

**Non-Goals:**
- CLI tool (futuro)
- Docker/CI (fora do escopo)
- Alteração em código Python

## Decisions

- **Makefile** sobre `justfile`/scripts — padrão universal, sem dependências extras, funciona em qualquer sistema Unix-like
- **Shebang** — usa `#!/usr/bin/env make` padrão Make
- **Diretório data/** — criado automaticamente, não versionado

## Risks / Trade-offs

- **Windows** — `make` não nativo → mitigado com instruções alternatives no README
- **Venv isolation** — make cria venv dentro do repo → mitigado com `.gitignore` para `.venv/`
