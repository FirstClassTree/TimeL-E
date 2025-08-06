# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install curl for health checks and clean up package managers
RUN apk add --no-cache curl

# Copy package files for dependency caching
COPY package*.json ./

# Configure npm for faster builds
RUN npm config set fund false && \
    npm config set audit-level moderate

# Install dependencies (cached layer)
RUN npm ci --only=production=false && \
    npm cache clean --force

# Copy source code (separate layer)
COPY . .

# Build the application
RUN npm run build && \
    npm prune --production

# Production stage
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user first
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder --chown=nodejs:nodejs /app/dist /usr/share/nginx/html

# Change ownership of nginx directories in one layer
RUN chown -R nodejs:nodejs /var/cache/nginx && \
    chown -R nodejs:nodejs /var/log/nginx && \
    chown -R nodejs:nodejs /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nodejs:nodejs /var/run/nginx.pid

# Switch to non-root user
USER nodejs

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
