FROM node:22-bookworm-slim AS builder
WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared-types/package.json ./packages/shared-types/package.json
RUN npm ci

COPY . .
RUN npm --workspace apps/web run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/package.json /app/package-lock.json ./
COPY --from=builder /app/apps/web ./apps/web
COPY --from=builder /app/packages/shared-types ./packages/shared-types
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "--workspace", "apps/web", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]
