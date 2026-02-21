# Build stage
FROM node:20-alpine3.23

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .
EXPOSE 5173
# Start server
CMD ["npm", "run", "dev"]