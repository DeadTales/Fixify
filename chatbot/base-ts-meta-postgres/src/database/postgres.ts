import { PostgreSQLAdapter } from '@builderbot/database-postgres'

/** Configuración de la base de eventos/contactos de BuilderBot, separada del negocio. */
export interface ConfiguracionPostgres {
    host: string
    user: string
    password: string
    database: string
    port: number
}

/**
 * El adaptador 1.4.2 llama init desde su constructor sin esperar las tablas.
 * ready permite esperar también su creación antes de abrir el webhook.
 * Se resuelve false ante un fallo para no dejar rechazos sin manejar en el constructor.
 */
class BaseConversaciones extends PostgreSQLAdapter {
    declare ready: Promise<boolean>

    override init(): Promise<boolean> {
        this.ready = (async () => {
            try {
                await super.init()
                // El init original inicia esta operación sin esperarla.
                // Capturamos esa operación mediante el método sobrescrito de abajo.
                await this.tablasListas
                return true
            } catch {
                return false
            }
        })()
        return this.ready
    }

    declare tablasListas: Promise<void>

    override checkTableExistsAndSP(): Promise<void> {
        this.tablasListas = super.checkTableExistsAndSP()
        // El init del paquete no observa este rechazo; ready sí lo comprueba.
        void this.tablasListas.catch(() => undefined)
        return this.tablasListas
    }
}

/** No inicia Meta si PostgreSQL no está disponible; nunca cambia a memoria automáticamente. */
export const crearBaseConversaciones = async (config: ConfiguracionPostgres): Promise<PostgreSQLAdapter> => {
    const database = new BaseConversaciones(config)
    if (!await database.ready) throw new Error('No se pudo preparar PostgreSQL para el chatbot')
    return database
}
