import { test } from 'node:test'
import assert from 'node:assert/strict'
import { crearConsultaApi, crearConsultaDemo, leerServicio, validarFolio } from '../src/services/consultar-servicio'
const publico = { folio: 'FIX-001', estado: 'En revisión', equipo: 'Laptop', actualizadoEn: '2026-10-04T12:00:00-06:00' }

test('normaliza folios y rechaza entradas inválidas', () => {
    assert.equal(validarFolio(' fix-001 '), 'FIX-001')
    for (const f of ['', 'AB', '../orden', 'A'.repeat(41)]) assert.equal(validarFolio(f), null)
})
test('el DTO elimina información privada y rechaza inconsistencias', () => {
    assert.deepEqual(leerServicio({ ...publico, notaInterna: 'privado' }, 'FIX-001'), publico)
    for (const s of [null, { ...publico, estado: 'Inventado' }, { ...publico, actualizadoEn: 'ayer' }, { ...publico, folio: 'OTRO' }]) {
        assert.equal(leerServicio(s, 'FIX-001'), null)
    }
})
test('demo restringe folio y remitente', async () => {
    const consultar = crearConsultaDemo('5213300000000')
    assert.equal((await consultar('DEMO-001', '5213300000000')).tipo, 'encontrado')
    assert.equal((await consultar('DEMO-001', 'otro')).tipo, 'no_autorizado')
    assert.equal((await consultar('OTRO', '5213300000000')).tipo, 'no_autorizado')
})
// Mock del transporte: verifica el cliente, no la autorización del Backend real.
test('API envía identidad/token y controla respuestas inválidas y fallos', async (t) => {
    const original = globalThis.fetch
    t.after(() => { globalThis.fetch = original })
    const consultar = crearConsultaApi('http://localhost/api/v1', 'token-prueba')
    globalThis.fetch = async (url, options) => {
        assert.equal(String(url), 'http://localhost/api/v1/chatbot/servicios/consulta')
        assert.deepEqual(JSON.parse(options.body as string), { folio: 'FIX-001', telefono: 'remitente-meta' })
        assert.equal((options.headers as Record<string, string>).Authorization, 'Bearer token-prueba')
        assert.ok(options.signal)
        return new Response(JSON.stringify({ ...publico, notaInterna: 'privado' }))
    }
    assert.deepEqual(await consultar('FIX-001', 'remitente-meta'), { tipo: 'encontrado', servicio: publico })
    for (const status of [403, 404, 401, 429, 500]) {
        globalThis.fetch = async () => new Response('', { status })
        assert.equal((await consultar('FIX-001', 'remitente-meta')).tipo,
            [403, 404].includes(status) ? 'no_autorizado' : 'no_disponible')
    }
    for (const body of ['no es JSON', JSON.stringify({ ...publico, estado: 'Inventado' })]) {
        globalThis.fetch = async () => new Response(body)
        assert.equal((await consultar('FIX-001', 'remitente-meta')).tipo, 'no_disponible')
    }
    globalThis.fetch = async () => { throw new DOMException('Timeout', 'TimeoutError') }
    assert.equal((await consultar('FIX-001', 'remitente-meta')).tipo, 'no_disponible')
})
