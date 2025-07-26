class HMIVirtualNumpad {
    constructor() {
        this.isConnected = false;
        this.targetDevice = 'rpi3pc';
        this.numLockActive = true;
        this.clickSoundEnabled = true;
        this.keyRepeatEnabled = true;
        this.repeatDelay = 500;
        
        this.ws = null;
        this.inputBuffer = '';
        this.keyPressCount = 0;
        this.commandsSent = 0;
        this.startTime = Date.now();
        this.lastActivity = null;
        
        this.repeatTimeouts = new Map();
        
        this.init();
        this.setupEventListeners();
        this.setupWebSocket();
        this.startStatsUpdate();
    }

    init() {
        this.updateStatus('Initializing...');
        this.updateNumLockState();
        this.logEvent('HMI Virtual Numpad initialized');
    }

    setupEventListeners() {
        // Numpad key buttons
        document.querySelectorAll('.key').forEach(key => {
            const keyValue = key.dataset.key;
            const keyCode = key.dataset.code;
            
            key.addEventListener('mousedown', (e) => {
                this.handleKeyPress(keyValue, keyCode, key);
            });
            
            key.addEventListener('mouseup', (e) => {
                this.handleKeyRelease(keyValue, key);
            });
            
            key.addEventListener('mouseleave', (e) => {
                this.handleKeyRelease(keyValue, key);
            });
        });

        // Settings controls
        document.getElementById('click-sound').addEventListener('change', (e) => {
            this.clickSoundEnabled = e.target.checked;
            this.logEvent(`Click sound ${e.target.checked ? 'enabled' : 'disabled'}`);
        });

        document.getElementById('key-repeat').addEventListener('change', (e) => {
            this.keyRepeatEnabled = e.target.checked;
            this.logEvent(`Key repeat ${e.target.checked ? 'enabled' : 'disabled'}`);
        });

        document.getElementById('repeat-delay').addEventListener('input', (e) => {
            this.repeatDelay = parseInt(e.target.value);
            document.getElementById('repeat-delay-value').textContent = `${this.repeatDelay}ms`;
        });

        document.getElementById('target-device').addEventListener('change', (e) => {
            this.targetDevice = e.target.value;
            this.logEvent(`Target device changed to: ${e.target.value}`);
            this.updateTargetStatus();
        });

        // Control buttons
        document.getElementById('reconnect-btn').addEventListener('click', () => {
            this.reconnect();
        });

        document.getElementById('clear-input').addEventListener('click', () => {
            this.clearInput();
        });

        document.getElementById('send-input').addEventListener('click', () => {
            this.sendInput();
        });

        document.getElementById('toggle-log').addEventListener('click', () => {
            this.toggleLog();
        });

        document.getElementById('clear-log').addEventListener('click', () => {
            this.clearLog();
        });

        document.getElementById('export-log').addEventListener('click', () => {
            this.exportLog();
        });

        // Physical keyboard events
        document.addEventListener('keydown', (e) => {
            if (this.isNumpadKey(e.code)) {
                e.preventDefault();
                const key = this.getKeyFromCode(e.code);
                if (key) {
                    this.handlePhysicalKeyPress(e.code, key);
                }
            }
        });

        document.addEventListener('keyup', (e) => {
            if (this.isNumpadKey(e.code)) {
                e.preventDefault();
                const key = this.getKeyFromCode(e.code);
                if (key) {
                    this.handlePhysicalKeyRelease(e.code, key);
                }
            }
        });
    }

    setupWebSocket() {
        try {
            this.ws = new WebSocket('ws://localhost:5560');
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateStatus('Connected to Numpad Backend');
                this.updateBackendStatus('connected');
                this.logEvent('WebSocket connection established');
            };
            
            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateStatus('Disconnected');
                this.updateBackendStatus('error');
                this.logEvent('WebSocket connection closed');
                // Attempt to reconnect
                setTimeout(() => this.setupWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Connection Error');
                this.updateBackendStatus('error');
                this.logEvent('WebSocket connection error');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateStatus('Connection Failed');
            this.updateBackendStatus('error');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status_update':
                this.handleStatusUpdate(data);
                break;
            case 'key_acknowledged':
                this.handleKeyAcknowledged(data);
                break;
            case 'target_status':
                this.handleTargetStatus(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleKeyPress(key, code, element) {
        if (!element) return;
        
        // Visual feedback
        element.classList.add('pressed', 'animate');
        
        // Sound feedback
        if (this.clickSoundEnabled) {
            this.playClickSound();
            element.classList.add('sound-effect');
            setTimeout(() => element.classList.remove('sound-effect'), 600);
        }
        
        // Handle special keys
        if (key === 'NumLock') {
            this.toggleNumLock();
            return;
        }
        
        if (key === 'Backspace') {
            this.handleBackspace();
        } else if (key === 'Enter') {
            this.handleEnter();
        } else {
            this.addToInput(key);
        }
        
        // Send to backend
        this.sendKeyToBackend(key, code, 'keydown');
        
        // Key repeat
        if (this.keyRepeatEnabled && this.isRepeatableKey(key)) {
            this.startKeyRepeat(key, code, element);
        }
        
        this.updateActivity();
        this.keyPressCount++;
        
        this.logEvent(`Key pressed: ${key} (${code || 'no code'})`);
    }

    handleKeyRelease(key, element) {
        if (!element) return;
        
        element.classList.remove('pressed', 'animate');
        
        // Stop key repeat
        this.stopKeyRepeat(key);
        
        // Send release to backend
        this.sendKeyToBackend(key, element.dataset.code, 'keyup');
    }

    handlePhysicalKeyPress(code, element) {
        const key = element.dataset.key;
        this.handleKeyPress(key, element.dataset.code, element);
    }

    handlePhysicalKeyRelease(code, element) {
        const key = element.dataset.key;
        this.handleKeyRelease(key, element);
    }

    startKeyRepeat(key, code, element) {
        this.stopKeyRepeat(key); // Clear any existing repeat
        
        const repeatInterval = setInterval(() => {
            this.sendKeyToBackend(key, code, 'keydown');
            this.addToInput(key);
            this.keyPressCount++;
            this.logEvent(`Key repeated: ${key}`);
        }, this.repeatDelay);
        
        this.repeatTimeouts.set(key, repeatInterval);
    }

    stopKeyRepeat(key) {
        const timeout = this.repeatTimeouts.get(key);
        if (timeout) {
            clearInterval(timeout);
            this.repeatTimeouts.delete(key);
        }
    }

    toggleNumLock() {
        this.numLockActive = !this.numLockActive;
        this.updateNumLockState();
        this.logEvent(`NumLock ${this.numLockActive ? 'activated' : 'deactivated'}`);
    }

    updateNumLockState() {
        const numLockKey = document.querySelector('[data-key="NumLock"]');
        if (numLockKey) {
            numLockKey.classList.toggle('active', this.numLockActive);
        }
    }

    handleBackspace() {
        if (this.inputBuffer.length > 0) {
            this.inputBuffer = this.inputBuffer.slice(0, -1);
            this.updateInputDisplay();
        }
    }

    handleEnter() {
        this.sendInput();
    }

    addToInput(key) {
        // Only add printable characters
        if (this.isPrintableKey(key)) {
            this.inputBuffer += key;
            this.updateInputDisplay();
        }
    }

    updateInputDisplay() {
        document.getElementById('input-preview').value = this.inputBuffer;
    }

    clearInput() {
        this.inputBuffer = '';
        this.updateInputDisplay();
        this.logEvent('Input buffer cleared');
    }

    sendInput() {
        if (this.inputBuffer.length > 0) {
            this.sendKeyToBackend('input_string', null, 'input', this.inputBuffer);
            this.commandsSent++;
            this.logEvent(`Input sent to ${this.targetDevice}: "${this.inputBuffer}"`);
            this.clearInput();
        }
    }

    sendKeyToBackend(key, code, action, data = null) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'key_event',
                key: key,
                code: code,
                action: action,
                target: this.targetDevice,
                numlock: this.numLockActive,
                timestamp: Date.now(),
                data: data
            };
            
            this.ws.send(JSON.stringify(message));
        }
    }

    playClickSound() {
        // Create audio context for click sound
        if (typeof(AudioContext) !== 'undefined' || typeof(webkitAudioContext) !== 'undefined') {
            try {
                const audioContext = new (AudioContext || webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.1);
            } catch (e) {
                console.log('Audio not supported:', e);
            }
        }
    }

    isNumpadKey(code) {
        return code.startsWith('Numpad') || 
               code === 'NumLock' || 
               ['Slash', 'Asterisk', 'Minus', 'Plus', 'Enter', 'Period'].includes(code);
    }

    getKeyFromCode(code) {
        const keyMap = {
            'NumLock': document.querySelector('[data-key="NumLock"]'),
            'NumpadDivide': document.querySelector('[data-key="/"]'),
            'NumpadMultiply': document.querySelector('[data-key="*"]'),
            'NumpadSubtract': document.querySelector('[data-key="-"]'),
            'NumpadAdd': document.querySelector('[data-key="+"]'),
            'NumpadEnter': document.querySelector('[data-key="Enter"]'),
            'NumpadDecimal': document.querySelector('[data-key="."]'),
            'Numpad0': document.querySelector('[data-key="0"]'),
            'Numpad1': document.querySelector('[data-key="1"]'),
            'Numpad2': document.querySelector('[data-key="2"]'),
            'Numpad3': document.querySelector('[data-key="3"]'),
            'Numpad4': document.querySelector('[data-key="4"]'),
            'Numpad5': document.querySelector('[data-key="5"]'),
            'Numpad6': document.querySelector('[data-key="6"]'),
            'Numpad7': document.querySelector('[data-key="7"]'),
            'Numpad8': document.querySelector('[data-key="8"]'),
            'Numpad9': document.querySelector('[data-key="9"]'),
            'Backspace': document.querySelector('[data-key="Backspace"]')
        };
        
        return keyMap[code];
    }

    isPrintableKey(key) {
        return /^[0-9\.\+\-\*\/]$/.test(key);
    }

    isRepeatableKey(key) {
        return key !== 'NumLock' && key !== 'Enter' && this.isPrintableKey(key);
    }

    handleStatusUpdate(data) {
        if (data.mqtt_status) {
            this.updateMqttStatus(data.mqtt_status);
        }
        if (data.target_status) {
            this.updateTargetStatus(data.target_status);
        }
    }

    handleKeyAcknowledged(data) {
        this.logEvent(`Key acknowledged by ${data.target}: ${data.key}`);
    }

    handleTargetStatus(data) {
        this.updateTargetStatus(data.status);
    }

    updateStatus(message) {
        document.getElementById('status').textContent = message;
        const led = document.getElementById('status-led');
        
        if (this.isConnected) {
            led.classList.add('connected');
        } else {
            led.classList.remove('connected');
        }
    }

    updateBackendStatus(status) {
        const element = document.getElementById('backend-status');
        element.textContent = status === 'connected' ? 'Connected' : 
                             status === 'error' ? 'Error' : 'Disconnected';
        element.className = `status-value ${status === 'connected' ? 'connected' : 
                                           status === 'error' ? 'error' : ''}`;
    }

    updateMqttStatus(status) {
        const element = document.getElementById('mqtt-status');
        element.textContent = status === 'connected' ? 'Connected' : 
                             status === 'error' ? 'Error' : 'Disconnected';
        element.className = `status-value ${status === 'connected' ? 'connected' : 
                                           status === 'error' ? 'error' : ''}`;
    }

    updateTargetStatus(status = null) {
        const element = document.getElementById('target-status');
        if (status) {
            element.textContent = status;
            element.className = `status-value ${status === 'online' ? 'connected' : 
                                               status === 'offline' ? 'error' : ''}`;
        } else {
            element.textContent = this.targetDevice;
            element.className = 'status-value';
        }
    }

    updateActivity() {
        this.lastActivity = new Date();
    }

    startStatsUpdate() {
        setInterval(() => {
            this.updateStats();
        }, 1000);
    }

    updateStats() {
        // Update uptime
        const uptime = Date.now() - this.startTime;
        const hours = Math.floor(uptime / 3600000);
        const minutes = Math.floor((uptime % 3600000) / 60000);
        const seconds = Math.floor((uptime % 60000) / 1000);
        document.getElementById('uptime').textContent = 
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update statistics
        document.getElementById('keys-pressed').textContent = this.keyPressCount;
        document.getElementById('commands-sent').textContent = this.commandsSent;
        
        // Update last activity
        if (this.lastActivity) {
            const timeSince = Date.now() - this.lastActivity.getTime();
            if (timeSince < 60000) {
                document.getElementById('last-activity').textContent = `${Math.floor(timeSince / 1000)}s ago`;
            } else if (timeSince < 3600000) {
                document.getElementById('last-activity').textContent = `${Math.floor(timeSince / 60000)}m ago`;
            } else {
                document.getElementById('last-activity').textContent = `${Math.floor(timeSince / 3600000)}h ago`;
            }
        }
    }

    reconnect() {
        this.logEvent('Attempting to reconnect...');
        if (this.ws) {
            this.ws.close();
        }
        setTimeout(() => this.setupWebSocket(), 1000);
    }

    toggleLog() {
        const log = document.getElementById('event-log');
        log.style.display = log.style.display === 'none' ? 'block' : 'none';
    }

    clearLog() {
        document.getElementById('event-log').innerHTML = '';
        this.logEvent('Event log cleared');
    }

    exportLog() {
        const log = document.getElementById('event-log').textContent;
        const blob = new Blob([log], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hmi-numpad-log-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        this.logEvent('Event log exported');
    }

    logEvent(message) {
        const log = document.getElementById('event-log');
        const timestamp = new Date().toLocaleTimeString();
        log.innerHTML += `[${timestamp}] ${message}\n`;
        log.scrollTop = log.scrollHeight;
    }
}

// Initialize HMI Virtual Numpad when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.hmiNumpad = new HMIVirtualNumpad();
});
