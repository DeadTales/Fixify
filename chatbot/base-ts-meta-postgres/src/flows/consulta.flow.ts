import { addKeyword, MemoryDB } from '@builderbot/bot'
import { MetaProvider } from '@builderbot/provider-meta'
import { ConsultarServicio, validarFolio } from '../services/consultar-servicio'

/**
 * Flujo modelo: HU-21 / RF-19, apoyado por HU-16/17 y RF-17.
 * Entrada -> captura de folio -> validación -> Backend -> respuesta pública -> cierre.
 * La dependencia se inyecta para usar el mismo diálogo en demo y con API real.
 */
export const crearFlujoConsulta = (consultar: ConsultarServicio, demo: boolean) =>
    addKeyword<MetaProvider, MemoryDB>(['hola', 'menu', 'menú', 'estado', 'consulta'], { sensitive: true })
        .addAnswer([
            'Bienvenido a Fixify. Aquí puedes consultar el estado de tu reparación.',
            ...(demo ? ['MODO DEMOSTRACIÓN: sólo datos ficticios. Folio de ejemplo: DEMO-001.'] : []),
            'Escribe tu folio o *cancelar* para salir.',
        ], { capture: true }, async (ctx, { fallBack, endFlow }) => {
            // Cancelar no consulta la API ni conserva información adicional en estado.
            if (ctx.body.trim().toLowerCase() === 'cancelar') return endFlow('Consulta cancelada. Escribe *estado* para empezar de nuevo.')
            const folio = validarFolio(ctx.body)
            // fallBack mantiene la captura en este paso hasta recibir un folio válido.
            if (!folio) return fallBack('Usa un folio de 3 a 40 caracteres: letras, números o guiones. También puedes escribir *cancelar*.')
            const resultado = await consultar(folio, ctx.from)
            if (resultado.tipo === 'no_autorizado') {
                return endFlow('No pudimos verificar un servicio con esos datos. Revisa tu folio o contacta a recepción. Escribe *estado* para reintentar.')
            }
            if (resultado.tipo === 'no_disponible') {
                return endFlow('La consulta no está disponible en este momento. Intenta después o contacta a recepción.')
            }
            const s = resultado.servicio
            // Se muestran exclusivamente los campos del DTO; no se vuelca el JSON del Backend.
            return endFlow([
                ...(demo ? ['DATOS FICTICIOS — DEMOSTRACIÓN'] : []),
                `Folio: ${s.folio}`, `Equipo: ${s.equipo}`, `Estado: ${s.estado}`,
                `Última actualización: ${s.actualizadoEn}`,
                'Escribe *estado* para otra consulta.',
            ].join('\n'))
        })
