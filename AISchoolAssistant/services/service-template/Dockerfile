# syntax=docker/dockerfile:1

# Multi-stage build for the golden NestJS service template.
# Uses Turborepo pruning so the image only contains this service and its
# workspace dependencies. Final stage runs as a non-root user.

ARG NODE_VERSION=22.13.0

# --- Base -------------------------------------------------------------------
FROM node:${NODE_VERSION}-bookworm-slim AS base
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable
WORKDIR /app

# --- Prune: isolate this service's subset of the monorepo -------------------
FROM base AS pruner
RUN pnpm add -g turbo@^2
COPY . .
RUN turbo prune @asa/service-template --docker

# --- Install + build --------------------------------------------------------
FROM base AS builder
COPY --from=pruner /app/out/json/ .
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile
COPY --from=pruner /app/out/full/ .
RUN pnpm turbo run build --filter=@asa/service-template
RUN pnpm install --prod --frozen-lockfile --ignore-scripts

# --- Runtime ----------------------------------------------------------------
FROM node:${NODE_VERSION}-bookworm-slim AS runner
ENV NODE_ENV=production
WORKDIR /app

# Drop privileges: the base image ships an unprivileged `node` user.
USER node

COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/packages ./packages
COPY --from=builder --chown=node:node /app/services/service-template/dist ./services/service-template/dist
COPY --from=builder --chown=node:node /app/services/service-template/package.json ./services/service-template/package.json

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||3000)+'/api/v1/health/ready').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

WORKDIR /app/services/service-template
CMD ["node", "dist/main.js"]
