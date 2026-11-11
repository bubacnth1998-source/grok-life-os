# Cómo usar Grok LIFE OS

1. Clona https://github.com/bubacnth1998-source/grok-life-os
2. En Linux del Chromebook:
   ```
   pip install -r requirements.txt
   export PYTHONPATH="${PWD}/backend"
   ./scripts/start.sh
   ```
3. La base local se guarda en `./data/grok_life_os.db` y los archivos en `./data/media` (no borres esa carpeta; está excluida de Git).\n4. Chrome: http://127.0.0.1:8000
5. Crea cuenta o usa la que registres
6. Módulos en la barra: Core, Finance, Projects, Time, Life, Memory, Sim, Audit, Nexus

Antes de reinstalar o cambiar de equipo, exporta desde Backup y conserva el archivo en un lugar seguro. Para restaurar, inicia sesión en la cuenta destino e importa el JSON.\n\nAPI docs: http://127.0.0.1:8000/api/docs\n\n**Despliegue serverless:** Vercel no admite SQLite local para datos persistentes. En ese entorno la aplicación falla de forma segura si no se configura PostgreSQL duradero y un secreto propio. No uses datos reales en previews sin esa configuración.
