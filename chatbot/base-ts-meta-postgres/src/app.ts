import { createBot, createProvider, createFlow, MemoryDB } from '@builderbot/bot'
import { MetaProvider } from '@builderbot/provider-meta'
import { cargarConfiguracion } from './config'
import { crearFlujoConsulta } from './flows/consulta.flow'
import { crearConsultaApi, crearConsultaDemo } from './services/consultar-servicio'

/**
 * Punto de composición: configura Meta y conecta los flujos con sus servicios.
 * MemoryDB guarda el historial conversacional en memoria, no datos del negocio.
 * Las órdenes se consultan exclusivamente por Backend; no hay acceso a PostgreSQL.
 */
const main = async () => {
    const config = cargarConfiguracion()
    const consultar = config.demo
        ? crearConsultaDemo(config.telefonoDemo)
        : crearConsultaApi(config.apiUrl, config.apiToken)
    const provider = createProvider(MetaProvider, config.meta)
    const { httpServer } = await createBot({
        flow: createFlow([crearFlujoConsulta(consultar, config.demo)]),
        provider, database: new MemoryDB(),
    })
    // El proveedor registra el webhook de Meta. No se exponen las rutas administrativas de la plantilla.
    httpServer(config.port)
}

// Una configuración inválida termina el proceso para evitar un bot parcialmente iniciado.
main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : 'No se pudo iniciar el chatbot')
    process.exitCode = 1
})
