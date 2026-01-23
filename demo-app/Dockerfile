FROM node:20-alpine

# Create app directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --omit=dev

# Copy source code
COPY src ./src

# Runtime config
ENV NODE_ENV=production
ENV PORT=8888

EXPOSE 8888

# Start the app
CMD ["node", "src/server.js"]