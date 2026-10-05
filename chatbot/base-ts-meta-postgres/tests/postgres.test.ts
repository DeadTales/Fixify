import { test } from 'node:test'
import assert from 'node:assert/strict'
import { crearBaseConversaciones } from '../src/database/postgres'

/** Opt-in: usa sólo una base de pruebas dedicada; el adaptador crea tablas y funciones. */
test('PostgreSQL persiste eventos entre dos conexiones independientes', {
    skip: process.env.CHATBOT_TEST_POSTGRES !== '1',
}, async (t) => {
    const config = {
        host: process.env.PG_TEST_HOST ?? '127.0.0.1',
        port: Number(process.env.PG_TEST_PORT ?? 55439),
        user: process.env.PG_TEST_USER ?? 'deadtales',
        password: process.env.PG_TEST_PASSWORD ?? 'prueba-local',
        database: process.env.PG_TEST_DATABASE ?? 'postgres',
    }
    const primera = await crearBaseConversaciones(config)
    t.after(() => primera.db.release(true))
    const from = `test-${Date.now()}`
    // Datos ficticios; el remitente único evita mezclar ejecuciones.
    await primera.save({ ref: 'test', keyword: 'estado', answer: 'Respuesta ficticia',
        refSerialize: 'test-ref', from, options: {} })
    const segunda = await crearBaseConversaciones(config)
    t.after(async () => {
        await segunda.db.query('DELETE FROM history WHERE phone = $1', [from])
        await segunda.db.query('DELETE FROM contact WHERE phone = $1', [from])
        segunda.db.release(true)
    })
    assert.equal((await segunda.getPrevByNumber(from))?.answer, 'Respuesta ficticia')
    assert.equal((await segunda.getContact({ from } as never))?.phone, from)
})
