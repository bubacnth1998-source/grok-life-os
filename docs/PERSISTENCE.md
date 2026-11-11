# Persistencia — Grok LIFE OS

## Problema actual

En despliegues serverless (p. ej. Vercel) el filesystem es **efímero**.

Usar `DATABASE_URL=sqlite:////tmp/...` implica:

* los datos pueden desaparecer entre cold starts;
* no sirve como almacén de vida real;
* el export/import local sigue siendo el mecanismo fiable de recuperación.

En ejecución local (Chromebook Linux) SQLite en un path persistente del proyecto **sí** es válido:

```bash
export DATABASE_URL="sqlite:///${PWD}/data/grok_life_os.db"
```

## Alternativas gratuitas evaluadas (sin contratar servicios de pago)

| Opción | Coste | Duradero | Notas |
|--------|-------|----------|-------|
| SQLite local en disco del dispositivo | 0 € | Sí | Preferido para Chromebook / desarrollo |
| Export/import JSON + SHA-256 | 0 € | Sí (copia del usuario) | Ya implementado en `/backup` |
| SQLite en `/tmp` (serverless) | 0 € | **No** | Solo demos / preview |
| Turso / LibSQL free tier | 0 € (límites) | Sí | Requiere cuenta externa; no activado |
| Neon / Supabase free | 0 € (límites) | Sí | Postgres; requiere autorización y secretos del usuario |

## Política del proyecto

1. **No** se activan proveedores de base de datos en la nube sin autorización explícita.
2. **No** se introducen datos personales reales en entornos sin persistencia verificada.
3. El camino soportado sin coste adicional es: **local SQLite + backup export/import**.
4. Cualquier adaptador cloud futuro debe:
   * vivir detrás de variables de entorno;
   * no romper el arranque local sin esas variables;
   * mantener aislamiento por `user_id`.

## Estado

* Implementado: SQLite configurable, backup con integridad, rollback de import.
* Pendiente (bloqueado por política 0 € / autorización): conectar un backend cloud gratuito si el usuario lo autoriza.
