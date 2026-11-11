# Vercel preview

## Fix applied for build error

Vercel said: no FastAPI entrypoint in default locations.

Now the repo declares:

```toml
[tool.vercel]
entrypoint = "api.index:app"
```

`api/index.py` adds `backend/` to `sys.path` and re-exports `app` from `app.main`.

## Redeploy

1. Push is on `main` (this fix).
2. In Vercel → Deployments → Redeploy the latest commit, **or** wait for auto-deploy from GitHub.
3. Env (optional but recommended):
   - `LIFE_OS_SECRET_KEY` = long random string
   - `DATABASE_URL` = `sqlite:////tmp/grok_life_os.db`

## Note
SQLite on Vercel is ephemeral (data may reset on cold start). Preview only.
