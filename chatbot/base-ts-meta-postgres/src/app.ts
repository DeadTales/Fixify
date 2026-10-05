import { createBot, createProvider, createFlow } from '@builderbot/bot'
import { crearBaseConversaciones } from './database/postgres'
import { MetaProvider } from '@builderbot/provider-meta'
import { cargarConfiguracion } from './config'
import { crearFlujoConsulta } from './flows/consulta.flow'
import { crearConsultaApi, crearConsultaDemo } from './services/consultar-servicio'

/**
 * Punto de composición: configura Meta y conecta los flujos con sus servicios.
 * PostgreSQL persiste eventos y contactos del bot en una base dedicada.
 * Las órdenes del negocio siguen consultándose por Backend, con autorización.
 */
const main = async () => {
    const config = cargarConfiguracion()
    const consultar = config.demo
        ? crearConsultaDemo(config.telefonoDemo)
        : crearConsultaApi(config.apiUrl, config.apiToken)
    // Espera conexión y tablas antes de recibir mensajes de Meta.
    const database = await crearBaseConversaciones(config.postgres)
    const provider = createProvider(MetaProvider, config.meta)
    const { httpServer } = await createBot({
        flow: createFlow([crearFlujoConsulta(consultar, config.demo)]),
        provider, database,
    })
    // El proveedor registra el webhook de Meta. No se exponen las rutas administrativas de la plantilla.
    httpServer(config.port)
}

// Una configuración inválida termina el proceso para evitar un bot parcialmente iniciado.
main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : 'No se pudo iniciar el chatbot')
    process.exitCode = 1
})
