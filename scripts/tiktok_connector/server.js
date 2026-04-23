// Serveur WebSocket Node.js pour TikTok-Live-Connector
// Lancez ce script avec: node scripts/tiktok_connector/server.js

const WebSocket = require('ws');
const { TikTokLiveConnection, WebcastEvent, ControlEvent } = require('tiktok-live-connector');

const wss = new WebSocket.Server({ port: 8765 });

let tiktokConnection = null;
let currentUsername = null;

function sendToAllClients(type, data) {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ type, data }));
        }
    });
}

function setupTikTokConnection(username, options = {}) {
    if (tiktokConnection) {
        tiktokConnection.disconnect();
        tiktokConnection = null;
    }
    tiktokConnection = new TikTokLiveConnection(username, options);
    currentUsername = username;

    // Contrôle
    tiktokConnection.on(ControlEvent.CONNECTED, (state) => {
        sendToAllClients('connected', state);
    });
    tiktokConnection.on(ControlEvent.DISCONNECTED, (info) => {
        sendToAllClients('disconnected', info);
    });
    tiktokConnection.on(ControlEvent.ERROR, (err) => {
        sendToAllClients('error', err);
    });

    // Événements principaux
    Object.values(WebcastEvent).forEach(eventName => {
        tiktokConnection.on(eventName, (data) => {
            sendToAllClients(eventName, data);
        });
    });
}

wss.on('connection', (ws) => {
    ws.on('message', async (message) => {
        let msg;
        try {
            msg = JSON.parse(message);
        } catch (e) {
            ws.send(JSON.stringify({ type: 'error', data: 'Invalid JSON' }));
            return;
        }
        if (msg.type === 'connect') {
            if (!msg.username) {
                ws.send(JSON.stringify({ type: 'error', data: 'Username required' }));
                return;
            }
            setupTikTokConnection(msg.username, msg.options || {});
            try {
                await tiktokConnection.connect();
            } catch (err) {
                sendToAllClients('error', err.toString());
            }
        } else if (msg.type === 'disconnect') {
            if (tiktokConnection) {
                tiktokConnection.disconnect();
                tiktokConnection = null;
                sendToAllClients('disconnected', { reason: 'Manual disconnect' });
            }
        } else if (msg.type === 'sendMessage') {
            if (tiktokConnection && msg.content) {
                try {
                    await tiktokConnection.sendMessage(msg.content);
                    ws.send(JSON.stringify({ type: 'messageSent', data: msg.content }));
                } catch (err) {
                    ws.send(JSON.stringify({ type: 'error', data: err.toString() }));
                }
            }
        } else if (msg.type === 'fetchRoomInfo') {
            if (tiktokConnection) {
                try {
                    const info = await tiktokConnection.fetchRoomInfo();
                    ws.send(JSON.stringify({ type: 'roomInfo', data: info }));
                } catch (err) {
                    ws.send(JSON.stringify({ type: 'error', data: err.toString() }));
                }
            }
        } else if (msg.type === 'fetchAvailableGifts') {
            if (tiktokConnection) {
                try {
                    const gifts = await tiktokConnection.fetchAvailableGifts();
                    ws.send(JSON.stringify({ type: 'availableGifts', data: gifts }));
                } catch (err) {
                    ws.send(JSON.stringify({ type: 'error', data: err.toString() }));
                }
            }
        }
    });
    ws.send(JSON.stringify({ type: 'ready', data: 'WebSocket server ready' }));
});

console.log('TikTok Connector WebSocket server running on ws://localhost:8765');
