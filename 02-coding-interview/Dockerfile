FROM node:18-alpine

WORKDIR /app

# Copy root package.json
COPY package.json ./

# Copy client and server package.json
COPY client/package.json ./client/
COPY server/package.json ./server/

# Install dependencies
RUN npm install
RUN cd client && npm install
RUN cd server && npm install

# Copy source code
COPY client ./client
COPY server ./server

# Build client
RUN cd client && npm run build

# Expose port
EXPOSE 3001

# Start server
CMD ["npm", "start", "--prefix", "server"]
