# Grok LIFE OS — Architecture

**Repo:** bubacnth1998-source/grok-life-os

Local-first: FastAPI + SQLAlchemy + SQLite + web shell. Local database defaults to `./data/grok_life_os.db`; media defaults to `./data/media`. Both paths are excluded from Git and persist on the user's local disk. Vercel/serverless is fail-closed unless durable PostgreSQL is configured; ephemeral SQLite is rejected.
Ledger finance (available vs reserved). Memory with revisions. Governance action classes. Simulator never mutates. NEXUS rules-first.

Modules: Auth, Core, Finance, Projects, Memory, Backup, Nexus, Governance, Simulator, Audit, Time, Life, Automation, Habits, Business, Travel, Learning, Media, Intelligence, Privacy.
