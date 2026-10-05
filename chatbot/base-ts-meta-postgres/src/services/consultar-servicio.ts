/** Estados oficiales: RN-03. El bot sólo presenta datos; no cambia órdenes. */
export const ESTADOS = ['Recibido', 'En revisión', 'Reparando', 'Listo', 'Entregado'] as const
export type EstadoServicio = typeof ESTADOS[number]

/** DTO público propuesto: excluye notas técnicas, costos internos y datos personales. */
export interface ServicioPublico {
    folio: string
    estado: EstadoServicio
    equipo: string
    actualizadoEn: string
}
export type ResultadoConsulta =
    | { tipo: 'encontrado'; servicio: ServicioPublico }
    | { tipo: 'no_autorizado' }
    | { tipo: 'no_disponible' }
export type ConsultarServicio = (folio: string, telefono: string) => Promise<ResultadoConsulta>

/** Formato provisional, pendiente de acordar con Backend; no es un requisito del PDF. */
export const validarFolio = (texto: string): string | null => {
    const folio = texto.trim().toUpperCase()
    return /^[A-Z0-9][A-Z0-9-]{2,39}$/.test(folio) ? folio : null
}

/** Valida la respuesta externa y selecciona únicamente los campos públicos permitidos. */
export const leerServicio = (dato: unknown, folio: string): ServicioPublico | null => {
    if (!dato || typeof dato !== 'object') return null
    const s = dato as Record<string, unknown>
    if (s.folio !== folio || !ESTADOS.includes(s.estado as EstadoServicio) ||
        typeof s.equipo !== 'string' || !s.equipo.trim() || s.equipo.length > 160 ||
        typeof s.actualizadoEn !== 'string' || !Number.isFinite(Date.parse(s.actualizadoEn))) return null
    return { folio, estado: s.estado as EstadoServicio, equipo: s.equipo, actualizadoEn: s.actualizadoEn }
}

/**
 * Adaptador HTTP del contrato PROPUESTO (el endpoint aún no existe en Backend).
 * El teléfono proviene de ctx.from, nunca de una respuesta escrita por el cliente.
 * Backend debe autenticar al bot Y comprobar la propiedad del servicio (RN-08/RN-11).
 * Fallos, respuestas inválidas y timeout no generan estados inventados.
 */
export const crearConsultaApi = (url: string, token: string): ConsultarServicio => async (folio, telefono) => {
    try {
        const response = await fetch(new URL('chatbot/servicios/consulta', url.endsWith('/') ? url : `${url}/`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ folio, telefono }),
            signal: AbortSignal.timeout(5000),
            redirect: 'error',
        })
        // No revelar si el folio existe cuando la propiedad no coincide.
        if ([403, 404].includes(response.status)) return { tipo: 'no_autorizado' }
        if (!response.ok) return { tipo: 'no_disponible' }
        const servicio = leerServicio(await response.json(), folio)
        return servicio ? { tipo: 'encontrado', servicio } : { tipo: 'no_disponible' }
    } catch {
        // No registrar teléfonos, credenciales ni el contenido de la respuesta externa.
        return { tipo: 'no_disponible' }
    }
}

/** Fixture educativo, separado de producción; sólo acepta el remitente demo configurado. */
export const crearConsultaDemo = (telefonoDemo: string): ConsultarServicio => async (folio, telefono) => {
    if (folio !== 'DEMO-001' || telefono !== telefonoDemo) return { tipo: 'no_autorizado' }
    return { tipo: 'encontrado', servicio: {
        folio: 'DEMO-001', estado: 'En revisión', equipo: 'Laptop de demostración',
        actualizadoEn: '2026-10-04T12:00:00-06:00',
    } }
}
