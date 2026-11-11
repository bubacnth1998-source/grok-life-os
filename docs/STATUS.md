# STATUS

**Última verificación CI:** la protección de persistencia Vercel del commit `8817d4d` pasó. Los cambios de pruebas IDOR, autenticación y driver PostgreSQL posteriores están pendientes de CI; no se consideran verificados hasta que terminen.

## Repositorio y despliegue

- Repo: https://github.com/bubacnth1998-source/grok-life-os
- Rama de trabajo: `fix/vercel-fastapi-entrypoint`
- Último cambio de integración: `6ebea978a2481b841ad4f4b5b18140541ccdd856` (documentación del contrato LIFE OS).
- Producción: no modificada.
- No se ha habilitado una conexión entre repositorios.

## Trabajo verificado en la rama

- Entry point FastAPI para Vercel e imports del backend.
- Backup ampliado con finanzas y dominios de vida, checksum SHA-256, validación de colecciones e importación transaccional.
- SQLite con claves foráneas activadas.
- CORS cerrado por defecto y rechazo de wildcard.
- Validación de configuración de producción: DEBUG desactivado y secreto único de al menos 32 caracteres.
- Protección de despliegue: Vercel rechaza el secreto de desarrollo y cualquier SQLite; requiere PostgreSQL duradero. Driver `psycopg` añadido.
- Interfaz: eliminado un segundo acceso duplicado a NEXUS en la navegación.
- PWA: manifiesto instalable, icono SVG, service worker y caché limitada a la carcasa estática; las respuestas autenticadas `/api/` nunca se almacenan en caché. Pruebas de rutas añadidas; CI pendiente.
- Prueba de aislamiento financiero: un usuario no puede crear una transacción usando la cuenta de otro usuario.
- Documentación del contrato de integración con LIFE OS en `docs/INTEGRATION_LIFE_OS.md`: API, autenticación, límites de confianza, adapter server-side, privacidad y criterios de aceptación.

## Límites conocidos

- **Persistencia local:** el valor predeterminado ahora es `./data/grok_life_os.db` y `./data/media`, ambos fuera de Git y persistentes en el disco local. El backup export/import permite migrar y recuperar datos.\n- **Despliegue Vercel:** no se habilita sin PostgreSQL duradero. No se creará ningún proyecto cloud ni se asumirán costes sin autorización.
- **Integración:** preparada a nivel documental, no conectada. No hay identidad federada, sincronización automática ni webhooks establecidos.
- **Verificación funcional:** CI pasa, pero esto no sustituye pruebas E2E completas de registro, login, CRUD, backup y restauración en navegador/preview.
- **Seguridad pendiente:** se añadieron pruebas de aislamiento entre usuarios para hábitos, memoria y calendario; su CI está pendiente. El rate limit de login actual es por proceso y no sustituye un limitador distribuido. Falta revisar CSP y política de retención de auditoría.
- **Despliegue:** no se ha fusionado esta rama con `main` ni se ha publicado producción.

No declarar el producto terminado hasta verificar persistencia durable, aislamiento por usuario en todos los módulos y pruebas E2E completas.
