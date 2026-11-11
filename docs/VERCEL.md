# Vercel — estado y política de despliegue

## Estado actual

Vercel **no está habilitado para datos personales ni producción**. El backend rechaza el arranque cuando detecta VERCEL=1 sin una clave propia y una base PostgreSQL duradera. SQLite en /tmp está bloqueado porque el almacenamiento serverless es efímero.

El entrypoint de la aplicación está definido en pyproject.toml como backend.app.main:app.

## Requisitos para habilitar Vercel en el futuro

1. PostgreSQL duradero y aislado, provisionado expresamente para Grok.
2. DATABASE_URL con driver PostgreSQL instalado.
3. LIFE_OS_SECRET_KEY único y aleatorio, de al menos 32 caracteres.
4. LIFE_OS_ENV=production, LIFE_OS_DEBUG=false y orígenes CORS explícitos.
5. Pruebas de migración, persistencia tras cold start, aislamiento multiusuario y backup/restore.
6. Revisión de almacenamiento de medios: el filesystem de funciones serverless no es persistente.

No crear bases de datos, no reutilizar las de Vision Finance o ICT Trading Intelligence y no publicar en producción sin autorización expresa.

## Estado de la rama

Los cambios se trabajan en fix/vercel-fastapi-entrypoint. No se debe indicar que el fix está en main ni fusionar ramas sin autorización.
