// Focus ST Telemetry Dashboard - WebSocket Client
class TelemetryDashboard {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.lastUpdateTime = 0;
        this.updateCount = 0;
        this.updateRateInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.startUpdateRateMonitor();
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.updateStatus(true);
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus(false);
            this.attemptReconnect();
        };
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'status':
                this.updateStatus(message.connected);
                break;
                
            case 'telemetry':
                this.updateTelemetry(message.data);
                this.updateCount++;
                break;
                
            case 'error':
                console.error('Telemetry error:', message.message);
                break;
        }
    }
    
    updateTelemetry(data) {
        // Update primary gauges
        this.updateElement('rpm', Math.round(data.rpm || 0));
        this.updateElement('speed', Math.round(data.speed || 0));
        this.updateElement('boost', (data.boost_pressure || 0).toFixed(1));
        
        // Update engine metrics
        this.updateElement('engine-load', Math.round(data.engine_load || 0));
        this.updateElement('throttle', Math.round(data.throttle_position || 0));
        this.updateElement('timing', (data.timing_advance || 0).toFixed(1));
        this.updateElement('afr', (data.air_fuel_ratio || 14.7).toFixed(2));
        
        // Update temperatures
        this.updateElement('coolant-temp', Math.round(data.coolant_temp || 0));
        this.updateElement('oil-temp', Math.round(data.oil_temp || 0));
        this.updateElement('intake-temp', Math.round(data.intake_air_temp || 0));
        this.updateElement('manifold-pressure', (data.manifold_pressure || 14.7).toFixed(1));
        
        // Update fuel & electrical
        this.updateElement('fuel-level', Math.round(data.fuel_level || 0));
        this.updateElement('fuel-pressure', Math.round(data.fuel_pressure || 0));
        this.updateElement('mpg', Math.round(data.instant_mpg || 0));
        this.updateElement('battery', (data.battery_voltage || 0).toFixed(2));
        
        // Update last update timestamp
        const now = new Date();
        this.updateElement('last-update', now.toLocaleTimeString());
        this.lastUpdateTime = Date.now();
        
        // Apply warning colors for critical values
        this.applyWarnings(data);
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    applyWarnings(data) {
        // Coolant temperature warning (>220°F)
        this.applyWarningClass('coolant-temp', data.coolant_temp > 220);
        
        // Oil temperature warning (>280°F)
        this.applyWarningClass('oil-temp', data.oil_temp > 280);
        
        // Battery voltage warning (<12V or >15V)
        this.applyWarningClass('battery', 
            data.battery_voltage < 12 || data.battery_voltage > 15);
        
        // Boost pressure warning (>22 PSI)
        this.applyWarningClass('boost', data.boost_pressure > 22);
    }
    
    applyWarningClass(id, shouldWarn) {
        const element = document.getElementById(id);
        if (element) {
            if (shouldWarn) {
                element.classList.add('warning');
            } else {
                element.classList.remove('warning');
            }
        }
    }
    
    updateStatus(connected) {
        const statusElement = document.getElementById('ecu-status');
        if (statusElement) {
            if (connected) {
                statusElement.classList.remove('disconnected');
                statusElement.classList.add('connected');
                statusElement.querySelector('.status-text').textContent = 'Connected';
            } else {
                statusElement.classList.remove('connected');
                statusElement.classList.add('disconnected');
                statusElement.querySelector('.status-text').textContent = 'Disconnected';
            }
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.setupWebSocket();
            }, this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    setupEventListeners() {
        // Reconnect button
        const reconnectBtn = document.getElementById('reconnect-btn');
        if (reconnectBtn) {
            reconnectBtn.addEventListener('click', () => {
                this.manualReconnect();
            });
        }
    }
    
    async manualReconnect() {
        console.log('Manual reconnect triggered');
        
        // Close existing WebSocket
        if (this.ws) {
            this.ws.close();
        }
        
        // Call reconnect API
        try {
            const response = await fetch('/api/reconnect', {
                method: 'POST'
            });
            const result = await response.json();
            console.log('Reconnect result:', result);
        } catch (error) {
            console.error('Failed to reconnect:', error);
        }
        
        // Reset reconnect attempts and establish new connection
        this.reconnectAttempts = 0;
        setTimeout(() => {
            this.setupWebSocket();
        }, 1000);
    }
    
    startUpdateRateMonitor() {
        let lastCount = 0;
        
        this.updateRateInterval = setInterval(() => {
            const rate = this.updateCount - lastCount;
            this.updateElement('update-rate', rate);
            lastCount = this.updateCount;
        }, 1000);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Focus ST Telemetry Dashboard');
    window.dashboard = new TelemetryDashboard();
});
