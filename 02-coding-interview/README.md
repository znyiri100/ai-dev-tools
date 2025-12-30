# Coding Interview Platform

A real-time collaborative coding interview platform with code execution.

## Features
- Real-time code collaboration (Socket.io)
- Syntax highlighting (Monaco Editor)
- Code execution for JavaScript and Python (Pyodide)
- Dockerized deployment

## Prerequisites
- Node.js
- Docker (optional)

## Installation

```bash
npm install
npm run install:all
```

## Running Locally

To run both client and server:

```bash
npm run dev
```

Client: http://localhost:5173
Server: http://localhost:3001

## Running Tests

```bash
cd client
npm test
```

## Docker

Build the image:

```bash
docker build -t coding-interview .
```

Run the container:

```bash
docker run -p 3001:3001 coding-interview
```

Access at http://localhost:3001
