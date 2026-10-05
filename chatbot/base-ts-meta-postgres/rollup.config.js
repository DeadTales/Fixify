import typescript from '@rollup/plugin-typescript'

export default {
    input: 'src/app.ts',
    output: { file: 'dist/app.js', format: 'esm' },
    external: (id) => !id.startsWith('.') && !id.startsWith('/') && !id.startsWith('src/'),
    plugins: [typescript({ tsconfig: './tsconfig.json', incremental: false })],
}
