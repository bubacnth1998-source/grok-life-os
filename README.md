# Grok LIFE OS

Implementación independiente de Grok (xAI). Repositorio: `grok-life-os`.

## Estado verificado

- **Pruebas:** 9 tests aprobados en GitHub Actions (última ejecución completa: commit `35fb7f0`).
- **Stack:** FastAPI + SQLAlchemy + SQLite + frontend web adaptable.
- **Ejecución principal:** local en Linux/Chromebook, sin servicios de pago obligatorios.
- **Preview Vercel:** disponible para validar la interfaz y las rutas HTTP. No equivale a producción ni garantiza persistencia duradera en un filesystem efímero.

## Arranque local

```bash
git clone https://github.com/bubacnth1998-source/grok-life-os.git
cd grok-life-os
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="${PWD}/backend"
chmod +x scripts/start.sh
./scripts/start.sh
```

Abre http://127.0.0.1:8000

## Módulos API

Auth, Core, Finance (ledger), Projects, Memory, Backup, Nexus, Governance, Simulator, Audit, Time, Life domains, Automation, Habits, Business, Travel, Learning, Media, Intelligence, Privacy.

## Recuperación de datos

La exportación incluye cuentas, movimientos y apuntes contables. La importación restaura las cuentas y reconstruye las referencias de movimientos; los archivos con checksum SHA-256 se verifican antes de escribir. Importar crea registros nuevos y no sobrescribe los existentes.

## CI

GitHub Actions ejecuta `pytest -q` en pushes y pull requests para las ramas `main` y `fix/**`.

## Documentación

- docs/ARCHITECTURE.md
- docs/STATUS.md
- docs/INTEGRATION_LIFE_OS.md — contrato de integración aislada con el ecosistema LIFE OS (preparación, no conexión activa).
- docs/USE.md
- docs/ADDENDUM.md
