# ==============================================================================
# AI Study Buddy Frontend - Production Dockerfile
# ==============================================================================

# Stage 1: Build static assets
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: High-Performance Hardened Web Server
FROM nginx:alpine-slim

# Copy nginx security and reverse proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled SPA bundle
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
