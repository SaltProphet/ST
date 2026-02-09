// Dashboard WebSocket client

class TelemetryDashboard {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.pidData = {};
        this.init();
    }

    init() {
        // Connect to Socket.io
        this.socket = io({
            transports: ['websocket', 'polling']
        });

        // Setup event handlers
        this.socket.on('connect', () => this.onConnect());
        this.socket.on('disconnect', () => this.onDisconnect());
        this.socket.on('telemetry_data', (data) => this.onTelemetryData(data));
        this.socket.on('connect_error', (error) => this.onError(error));
    }

    onConnect() {
        console.log('Connected to telemetry gateway');
        this.connected = true;
        this.updateStatus(true);
    }

    onDisconnect() {
        console.log('Disconnected from telemetry gateway');
        this.connected = false;
        this.updateStatus(false);
    }

    onError(error) {
        console.error('Connection error:', error);
        this.updateStatus(false);
    }

    onTelemetryData(data) {
        const pidName = data.pid_name;
        this.pidData[pidName] = data;
        this.updateGauge(pidName, data);
    }

    updateStatus(connected) {
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        
        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    }

    updateGauge(pidName, data) {
        // Update main value
        const valueElement = document.getElementById(`value-${pidName}`);
        if (valueElement) {
            valueElement.textContent = data.converted_value.toFixed(2);
        }

        // Update raw value
        const rawElement = document.getElementById(`raw-${pidName}`);
        if (rawElement) {
            rawElement.textContent = data.raw_value.toFixed(2);
        }

        // Update timestamp
        const timeElement = document.getElementById(`time-${pidName}`);
        if (timeElement) {
            const date = new Date(data.timestamp * 1000);
            timeElement.textContent = date.toLocaleTimeString();
        }

        // Update warning
        const warningElement = document.getElementById(`warning-${pidName}`);
        if (warningElement) {
            if (data.warning) {
                warningElement.textContent = `⚠ ${data.warning}`;
                warningElement.style.display = 'block';
            } else {
                warningElement.style.display = 'none';
            }
        }

        // Add visual feedback
        const card = document.getElementById(`card-${pidName}`);
        if (card) {
            card.style.animation = 'none';
            setTimeout(() => {
                card.style.animation = 'pulse-subtle 0.3s';
            }, 10);
        }
    }

    subscribeToPID(pidName) {
        if (this.connected) {
            this.socket.emit('subscribe', { pid: pidName });
        }
    }

    unsubscribeFromPID(pidName) {
        if (this.connected) {
            this.socket.emit('unsubscribe', { pid: pidName });
        }
    }
}

// Add subtle pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse-subtle {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);

// Initialize dashboard
const dashboard = new TelemetryDashboard();

// Log connection status
console.log('Focus ST Telemetry Dashboard initialized');
