# Grok LIFE OS

Implementación independiente de Grok (xAI). Repo: `grok-life-os`.

## Estado

- **Tests:** 15 passed (`pytest tests/test_core.py`)
- **Stack:** FastAPI + SQLite + PWA local-first
- **Sin Vercel/hosting externo** — ejecuta en Chromebook Linux

## Arranque

```bash
git clone https://github.com/bubacnth1998-source/grok-life-os.git
cd grok-life-os
pip install -r requirements.txt
export PYTHONPATH="${PWD}/backend"
chmod +x scripts/start.sh
./scripts/start.sh
```

Abre http://127.0.0.1:8000

## Módulos API

Auth, Core, Finance (ledger), Projects, Memory, Backup, Nexus, Governance, Simulator, Audit, Time, Life domains, Automation, Habits, Business, Travel, Learning, Media, Intelligence, Privacy

## Docs

- docs/ARCHITECTURE.md
- docs/STATUS.md
- docs/USE.md
- docs/ADDENDUM.md
