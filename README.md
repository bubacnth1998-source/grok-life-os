# Grok LIFE OS

**Implementación independiente de Grok (xAI).**  
Repositorio exclusivo: `grok-life-os`.

Sistema operativo personal **local-first**: ledger financiero, proyectos, memoria, backup y NEXUS (reglas).

## Pruebas

```bash
export PYTHONPATH="${PWD}/backend"
pytest tests/ -v
# 7 passed
```

## Arranque

```bash
pip install -r requirements.txt
export PYTHONPATH="${PWD}/backend"
./scripts/start.sh
```

http://127.0.0.1:8000

## Docs

- [ARCHITECTURE](docs/ARCHITECTURE.md)
- [DECISIONS](docs/DECISIONS.md)
- [STATUS](docs/STATUS.md)
