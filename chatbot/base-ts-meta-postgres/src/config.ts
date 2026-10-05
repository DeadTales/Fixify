/** Lee variables obligatorias sin incluir sus valores en mensajes de error. */
const requerida = (nombre: string): string => {
    const valor = process.env[nombre]?.trim()
    if (!valor) throw new Error(`Falta configurar ${nombre}`)
    return valor
}

/** Falla antes de iniciar si la configuración es incompleta; API es el modo predeterminado. */
export const cargarConfiguracion = () => {
    const modo = process.env.CHATBOT_MODE ?? 'api'
    if (!['api', 'demo'].includes(modo)) throw new Error('CHATBOT_MODE debe ser api o demo')
    const port = Number(process.env.PORT ?? 3008)
    if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('PORT inválido')
    const meta = {
        jwtToken: requerida('META_ACCESS_TOKEN'), numberId: requerida('META_PHONE_NUMBER_ID'),
        verifyToken: requerida('META_VERIFY_TOKEN'), version: requerida('META_API_VERSION'),
    }
    const apiUrl = modo === 'api' ? requerida('BACKEND_URL') : ''
    if (modo === 'api' && !['http:', 'https:'].includes(new URL(apiUrl).protocol)) throw new Error('BACKEND_URL inválida')
    return { port, meta, demo: modo === 'demo', apiUrl,
        apiToken: modo === 'api' ? requerida('BACKEND_BOT_TOKEN') : '',
        telefonoDemo: modo === 'demo' ? requerida('DEMO_PHONE_NUMBER') : '',
    }
}
