# Preview en Vercel

Repo: https://github.com/bubacnth1998-source/grok-life-os

## Limitación crítica
SQLite en Vercel es **efímero**. El preview sirve para probar UI/API; los datos pueden borrarse entre arranques en frío.

## Env
```
LIFE_OS_SECRET_KEY=<secreto-largo>
DATABASE_URL=sqlite:////tmp/grok_life_os.db
```

## Prompt para ChatGPT
Despliega `bubacnth1998-source/grok-life-os` como preview en Vercel. Entry: `backend/app/main.py`. Solo preview, no producción definitiva.
