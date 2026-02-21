# Build stage
FROM node:20-alpine3.23

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Start server
RUN npm run dev