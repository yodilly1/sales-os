# Sales OS Frontend Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Base
# =============================================================================
FROM node:20-alpine AS base
RUN apk add --no-cache libc6-compat
WORKDIR /app

# =============================================================================
# Stage 2: Dependencies
# =============================================================================
FROM base AS dependencies

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm ci

# =============================================================================
# Stage 3: Development
# =============================================================================
FROM base AS development

# Copy dependencies
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

# Expose port
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Development server with hot reload
CMD ["npm", "run", "dev"]

# =============================================================================
# Stage 4: Builder
# =============================================================================
FROM base AS builder

# Copy dependencies
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

# Build arguments for environment
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_ENV=production

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# =============================================================================
# Stage 5: Production
# =============================================================================
FROM base AS production

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.* ./
COPY --from=builder /app/node_modules ./node_modules

# Set ownership
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start production server
CMD ["npm", "start"]
