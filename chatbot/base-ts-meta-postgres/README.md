# Chatbot Fixify — flujo modelo con Meta

El ejemplo implementa consulta por folio y sirve como patrón para los demás flujos. Lee el [plan](../docs/PLAN_CHATBOT.ipynb) y el [contrato propuesto](../docs/CONTRATO_API.ipynb). El Backend todavía no tiene el endpoint de consulta: usa `demo` para aprender; `api` requiere implementarlo.

## Ejecutar

Desde esta carpeta, con Node 22 o superior y dependencias instaladas:

```bash
cp .env.example .env
# Completa las variables de Meta y DEMO_PHONE_NUMBER en .env.
pnpm lint
pnpm build
pnpm start
```

Para instalar en una copia nueva usa `pnpm install --frozen-lockfile`. Los comandos start/dev cargan `.env` mediante Node. No subas ese archivo a Git. `META_ACCESS_TOKEN` es el token de acceso, `META_PHONE_NUMBER_ID` el identificador del número, `META_VERIFY_TOKEN` el valor que acuerdas para verificar el webhook y `META_API_VERSION` la versión habilitada en tu aplicación; debe completarse explícitamente.

Configura en Meta la URL pública HTTPS del webhook `/webhook`, el mismo verify token y la suscripción a mensajes. En desarrollo puedes usar un túnel hacia el puerto 3008. Para el número de pruebas de Meta, autoriza el remitente de prueba. Usa el valor exacto que Meta entrega como remitente para `DEMO_PHONE_NUMBER`.

Prueba: envía `estado` → `DEMO-001`. Recibirás un resultado marcado **DATOS FICTICIOS**. Otro folio o remitente obtiene la respuesta de verificación fallida. Un formato inválido vuelve a pedir el folio; `cancelar` termina. Al concluir escribe `estado` para empezar otra consulta. No se probaron envíos reales sin tus credenciales.

Para integrar: cambia `CHATBOT_MODE=api`, configura `BACKEND_URL` y `BACKEND_BOT_TOKEN` y proporciona el endpoint del contrato. No hay cambio automático a demo ante errores.

## Qué hace cada parte del código

| Archivo | Responsabilidad |
| --- | --- |
| `src/app.ts` | Compone configuración, Meta, historial en PostgreSQL, servicio y flujo; inicia HTTP |
| `src/config.ts` | Exige variables y valida modo/puerto antes de iniciar |
| `src/flows/consulta.flow.ts` | Define entrada, captura, validación, cancelación y respuestas |
| `src/services/consultar-servicio.ts` | Tipos públicos, estados, validación, API con timeout y fixture demo |
| `tests/consulta.test.ts` | Pruebas de privacidad del DTO y comportamiento ante errores HTTP |

Cada bloque tiene comentarios de propósito. `addKeyword` activa el flujo, `addAnswer` presenta el mensaje; `capture: true` espera la siguiente respuesta. `ctx.body` es el mensaje y `ctx.from` el remitente. `fallBack` repite la captura, `endFlow` termina la conversación. El servicio se inyecta: el diálogo no necesita conocer la implementación HTTP ni una base de datos. No se guarda folio en estado porque este ejemplo resuelve la consulta en una sola captura.

## Cómo desarrollar el siguiente flujo

1. Elige una HU y escribe entradas, salidas y criterios de aceptación (por ejemplo HU-22 para FAQ).
2. Acuerda el contrato con Backend; no inventes horarios, precios ni diagnósticos.
3. Crea `src/services/preguntas-frecuentes.ts` con un resultado tipado y tratamiento de errores.
4. Crea `src/flows/preguntas-frecuentes.flow.ts` exportando una fábrica como `crearFlujoConsulta`. Usa palabras propias como `preguntas` para evitar conflictos.
5. Inyecta el servicio desde `app.ts` y agrega el flujo a `createFlow([...])`.
6. Para varios pasos, usa `state.update`/`state.get`, valida cada captura y limpia sólo los datos de ese flujo al concluir o cancelar. Define caducidad e intentos antes de captar datos sensibles.
7. Documenta HU/RF, contrato, conversación válida y fallida; prueba respuestas desconocidas, caída del Backend y contenido no autorizado.

Para avisos de equipo listo se necesita un evento del Backend y un servicio de envío, no una captura de folio. Programa recordatorios en Backend con control de duplicados y periodos configurables.

## Verificación

```bash
pnpm test
pnpm lint
pnpm build
```

Las pruebas de consulta no necesitan Meta ni PostgreSQL. La prueba de persistencia requiere una base dedicada y se habilita con CHATBOT_TEST_POSTGRES=1; se omite por defecto. Quedan pendientes pruebas completas por WhatsApp y contra el Backend real. PostgreSQL persiste eventos y contactos; no garantiza conservar todas las capturas pendientes tras reiniciar; la carpeta conserva el nombre de la plantilla postgres por compatibilidad de rutas.

La documentación completa, plan y código explicado están en [Documentacion_chatbot.ipynb](../../docs/Chatbot/Documentacion_chatbot.ipynb). Para instalar desde esta carpeta usa `pnpm --dir .. install --frozen-lockfile`.

Configura también POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD y POSTGRES_DB en .env. Crea previamente el rol y la base dedicada. La guía ampliada de [autenticación y PostgreSQL](../docs/AUTENTICACION_Y_POSTGRESQL.ipynb) explica permisos y límites.
