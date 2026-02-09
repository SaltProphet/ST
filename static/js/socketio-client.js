// Minimal Socket.io-compatible WebSocket client
// This is a simplified implementation for demonstration

class SocketIOClient {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.handlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect(options = {}) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/socket.io/?transport=websocket`;
        
        console.log('Connecting to:', wsUrl);
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.trigger('connect');
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.connected = false;
                this.trigger('disconnect');
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.trigger('connect_error', error);
            };
            
            this.ws.onmessage = (event) => {
                try {
                    // Socket.io protocol parsing
                    const data = event.data;
                    if (data.startsWith('42')) {
                        // Event message
                        const payload = JSON.parse(data.substring(2));
                        const [eventName, eventData] = payload;
                        this.trigger(eventName, eventData);
                    } else if (data === '0') {
                        // Connected
                        this.ws.send('40'); // Connect to namespace
                    } else if (data === '2') {
                        // Ping
                        this.ws.send('3'); // Pong
                    }
                } catch (e) {
                    console.error('Error parsing message:', e);
                }
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.attemptReconnect();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(2000 * Math.pow(2, this.reconnectAttempts - 1), 30000);
            console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
            setTimeout(() => this.connect(), delay);
        }
    }
    
    on(event, handler) {
        if (!this.handlers[event]) {
            this.handlers[event] = [];
        }
        this.handlers[event].push(handler);
    }
    
    emit(event, data) {
        if (this.connected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = `42${JSON.stringify([event, data])}`;
            this.ws.send(message);
        }
    }
    
    trigger(event, data) {
        const handlers = this.handlers[event] || [];
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (e) {
                console.error(`Error in ${event} handler:`, e);
            }
        });
    }
}

// Create global io function to match Socket.io API
window.io = function(options) {
    const client = new SocketIOClient();
    client.connect(options);
    return client;
};
