# Build from chatbot/: docker build -f base-ts-meta-postgres/Dockerfile -t fixify-chatbot .
FROM node:22-bookworm-slim
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@12.9.1 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY base-ts-meta-postgres/package.json ./base-ts-meta-postgres/package.json
RUN pnpm install --frozen-lockfile
COPY base-ts-meta-postgres/src ./base-ts-meta-postgres/src
COPY base-ts-meta-postgres/tsconfig.json base-ts-meta-postgres/rollup.config.js ./base-ts-meta-postgres/
RUN pnpm build
ENV PORT=3008
EXPOSE 3008
WORKDIR /app/base-ts-meta-postgres
# Supply environment variables at runtime; no secrets copied into the image.
CMD ["node", "dist/app.js"]
