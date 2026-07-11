FROM node:22-alpine AS deps
WORKDIR /app
COPY package*.json ./
# Production dependencies only.
RUN npm ci --omit=dev

FROM node:22-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app

# Run as an unprivileged user.
RUN addgroup -S nodejs && adduser -S signaling -G nodejs

COPY --from=deps --chown=signaling:nodejs /app/node_modules ./node_modules
COPY --chown=signaling:nodejs package.json ./
COPY --chown=signaling:nodejs src ./src

USER signaling
EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||3001)+'/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "src/server.js"]
