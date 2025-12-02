const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());

const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*',
        methods: ['GET', 'POST'],
    },
});

const PORT = process.env.PORT || 3001;

// Store sessions in memory
// session_id -> { code: string, language: string, users: Set<socket_id> }
const sessions = {};

io.on('connection', (socket) => {
    console.log('User connected:', socket.id);

    socket.on('join-session', (sessionId) => {
        socket.join(sessionId);
        if (!sessions[sessionId]) {
            sessions[sessionId] = {
                code: '// Start coding here...',
                language: 'javascript',
                users: new Set(),
            };
        }
        sessions[sessionId].users.add(socket.id);

        // Send current state to the user
        socket.emit('init-session', {
            code: sessions[sessionId].code,
            language: sessions[sessionId].language,
        });

        console.log(`User ${socket.id} joined session ${sessionId}`);
    });

    socket.on('code-change', ({ sessionId, code }) => {
        if (sessions[sessionId]) {
            sessions[sessionId].code = code;
            socket.to(sessionId).emit('code-update', code);
        }
    });

    socket.on('language-change', ({ sessionId, language }) => {
        if (sessions[sessionId]) {
            sessions[sessionId].language = language;
            socket.to(sessionId).emit('language-update', language);
        }
    });

    socket.on('disconnect', () => {
        console.log('User disconnected:', socket.id);
        // Cleanup logic if needed (e.g., remove user from sessions)
        for (const sessionId in sessions) {
            if (sessions[sessionId].users.has(socket.id)) {
                sessions[sessionId].users.delete(socket.id);
                if (sessions[sessionId].users.size === 0) {
                    // Optional: delete session if empty after some time
                }
            }
        }
    });
});

// Root route removed to allow static files to be served

// Serve static files from client/dist
const path = require('path');
app.use(express.static(path.join(__dirname, '../client/dist')));

app.get(/(.*)/, (req, res) => {
    res.sendFile(path.join(__dirname, '../client/dist/index.html'));
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Server is running on port ${PORT}`);
});
