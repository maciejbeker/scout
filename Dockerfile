# Build stage
FROM node:16 AS builder
WORKDIR /app

# Install dependencies
COPY package*.json ./
COPY tsconfig.json ./

RUN npm install

# Copy source and dist
COPY src/ ./src/
COPY dist/ ./dist/

# Build TypeScript
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=builder /app/dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]