class HMIVirtualMonitor {
    constructor() {
        this.isConnected = false;
        this.isPowered = true;
        this.currentResolution = { width: 1920, height: 1080 };
        this.refreshRate = 60;
        this.inputSource = 'hdmi1';
        this.brightness = 80;
        this.contrast = 75;
        this.saturation = 50;
        this.hue = 0;
        this.colorTemp = 5500;
        this.aspectRatio = '16:9';
        this.scaling = 'fit';
        this.rotation = 0;
        
        this.isCapturing = false;
        this.isFullscreen = false;
        this.streamQuality = 'medium';
        this.frameRate = 30;
        this.ws = null;
        this.vncWs = null;
        
        this.canvas = null;
        this.ctx = null;
        this.frameStats = {
            received: 0,
            actualFps: 0,
            latency: 0,
            dataRate: 0
        };
        
        this.lastFrameTime = 0;
        this.frameBuffer = [];
        
        this.init();
        this.setupEventListeners();
        this.setupWebSocket();
        this.startFrameStatsUpdate();
    }

    init() {
        this.canvas = document.getElementById('display-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.updateStatus('Initializing...');
        this.setupCanvas();
        this.updateDisplayInfo();
        this.showNoSignalPattern();
    }

    setupCanvas() {
        // Set canvas size based on current resolution
        this.canvas.width = this.currentResolution.width;
        this.canvas.height = this.currentResolution.height;
        
        // Apply display settings
        this.applyDisplaySettings();
    }

    setupEventListeners() {
        // Monitor control buttons
        document.getElementById('power-btn').addEventListener('click', () => {
            this.togglePower();
        });

        document.getElementById('menu-btn').addEventListener('click', () => {
            this.showMonitorMenu();
        });

        document.getElementById('source-btn').addEventListener('click', () => {
            this.cycleInputSource();
        });

        // Resolution and display controls
        document.getElementById('resolution-select').addEventListener('change', (e) => {
            this.changeResolution(e.target.value);
        });

        document.getElementById('refresh-rate').addEventListener('change', (e) => {
            this.changeRefreshRate(parseInt(e.target.value));
        });

        document.getElementById('input-source').addEventListener('change', (e) => {
            this.changeInputSource(e.target.value);
        });

        // Display settings sliders
        const sliders = ['brightness', 'contrast', 'saturation', 'hue'];
        sliders.forEach(setting => {
            const slider = document.getElementById(setting);
            const valueSpan = document.getElementById(`${setting}-value`);
            
            slider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                this[setting] = value;
                
                if (setting === 'hue') {
                    valueSpan.textContent = `${value}°`;
                } else {
                    valueSpan.textContent = `${value}%`;
                }
                
                this.applyDisplaySettings();
                this.logEvent(`${setting.charAt(0).toUpperCase() + setting.slice(1)} changed to: ${value}`);
            });
        });

        // Other display settings
        document.getElementById('color-temp').addEventListener('change', (e) => {
            this.colorTemp = parseInt(e.target.value);
            this.applyDisplaySettings();
            this.logEvent(`Color temperature changed to: ${e.target.value}K`);
        });

        document.getElementById('aspect-ratio').addEventListener('change', (e) => {
            this.aspectRatio = e.target.value;
            this.applyDisplaySettings();
            this.logEvent(`Aspect ratio changed to: ${e.target.value}`);
        });

        document.getElementById('scaling').addEventListener('change', (e) => {
            this.scaling = e.target.value;
            this.applyDisplaySettings();
            this.logEvent(`Scaling changed to: ${e.target.value}`);
        });

        document.getElementById('rotation').addEventListener('change', (e) => {
            this.rotation = parseInt(e.target.value);
            this.applyDisplaySettings();
            this.logEvent(`Rotation changed to: ${e.target.value}°`);
        });

        // Stream settings
        document.getElementById('stream-quality').addEventListener('change', (e) => {
            this.streamQuality = e.target.value;
            this.logEvent(`Stream quality changed to: ${e.target.value}`);
        });

        document.getElementById('frame-rate').addEventListener('change', (e) => {
            this.frameRate = parseInt(e.target.value);
            this.logEvent(`Frame rate changed to: ${e.target.value} FPS`);
        });

        // Stream control buttons
        document.getElementById('start-capture').addEventListener('click', () => {
            this.startCapture();
        });

        document.getElementById('stop-capture').addEventListener('click', () => {
            this.stopCapture();
        });

        document.getElementById('take-screenshot').addEventListener('click', () => {
            this.takeScreenshot();
        });

        document.getElementById('fullscreen').addEventListener('click', () => {
            this.toggleFullscreen();
        });

        document.getElementById('clear-log').addEventListener('click', () => {
            document.getElementById('event-log').innerHTML = '';
        });

        // Fullscreen escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isFullscreen) {
                this.toggleFullscreen();
            }
        });

        // Canvas click for interaction
        this.canvas.addEventListener('click', (e) => {
            if (this.isConnected) {
                this.handleCanvasClick(e);
            }
        });
    }

    setupWebSocket() {
        try {
            // Connect to monitor backend for control
            this.ws = new WebSocket(`ws://localhost:5558`);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateStatus('Connected to Monitor Backend');
                this.connectToVNC();
            };
            
            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateStatus('Disconnected');
                this.showNoSignalPattern();
                // Attempt to reconnect
                setTimeout(() => this.setupWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Connection Error');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateStatus('Connection Failed');
        }
    }

    connectToVNC() {
        try {
            // Connect to RPi VNC stream
            const vncUrl = this.inputSource === 'hdmi1' ? 
                'ws://localhost:5901' : 'ws://localhost:5559';
            
            this.vncWs = new WebSocket(vncUrl);
            
            this.vncWs.onopen = () => {
                this.logEvent('VNC stream connected');
                document.getElementById('vnc-stream').textContent = 'Active';
                document.getElementById('vnc-stream').className = 'value active';
                document.getElementById('signal-status').textContent = 'Signal Detected';
                document.getElementById('signal-status').className = 'value connected';
            };
            
            this.vncWs.onmessage = (event) => {
                this.handleVNCFrame(event.data);
            };
            
            this.vncWs.onclose = () => {
                this.logEvent('VNC stream disconnected');
                document.getElementById('vnc-stream').textContent = 'Inactive';
                document.getElementById('vnc-stream').className = 'value';
                document.getElementById('signal-status').textContent = 'No Signal';
                document.getElementById('signal-status').className = 'value error';
                this.showNoSignalPattern();
            };
            
        } catch (error) {
            console.error('VNC connection failed:', error);
            this.logEvent('VNC connection failed');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'monitor_status':
                this.updateMonitorStatus(data);
                break;
            case 'resolution_changed':
                this.handleResolutionChange(data);
                break;
            case 'input_switched':
                this.handleInputSwitch(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleVNCFrame(frameData) {
        try {
            // Convert frame data to image
            const blob = new Blob([frameData], { type: 'image/jpeg' });
            const img = new Image();
            
            img.onload = () => {
                if (this.isPowered) {
                    // Clear canvas
                    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                    
                    // Apply scaling and positioning
                    this.drawScaledImage(img);
                    
                    // Update frame stats
                    this.updateFrameStats();
                }
            };
            
            img.src = URL.createObjectURL(blob);
            
        } catch (error) {
            console.error('Error processing VNC frame:', error);
        }
    }

    drawScaledImage(img) {
        const canvasWidth = this.canvas.width;
        const canvasHeight = this.canvas.height;
        
        let drawWidth, drawHeight, drawX, drawY;
        
        switch (this.scaling) {
            case 'fit':
                const scale = Math.min(canvasWidth / img.width, canvasHeight / img.height);
                drawWidth = img.width * scale;
                drawHeight = img.height * scale;
                drawX = (canvasWidth - drawWidth) / 2;
                drawY = (canvasHeight - drawHeight) / 2;
                break;
                
            case 'fill':
                const fillScale = Math.max(canvasWidth / img.width, canvasHeight / img.height);
                drawWidth = img.width * fillScale;
                drawHeight = img.height * fillScale;
                drawX = (canvasWidth - drawWidth) / 2;
                drawY = (canvasHeight - drawHeight) / 2;
                break;
                
            case 'stretch':
                drawWidth = canvasWidth;
                drawHeight = canvasHeight;
                drawX = 0;
                drawY = 0;
                break;
                
            default: // none
                drawWidth = img.width;
                drawHeight = img.height;
                drawX = (canvasWidth - drawWidth) / 2;
                drawY = (canvasHeight - drawHeight) / 2;
        }
        
        // Apply rotation if needed
        if (this.rotation !== 0) {
            this.ctx.save();
            this.ctx.translate(canvasWidth / 2, canvasHeight / 2);
            this.ctx.rotate(this.rotation * Math.PI / 180);
            this.ctx.translate(-canvasWidth / 2, -canvasHeight / 2);
        }
        
        // Draw the image
        this.ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
        
        if (this.rotation !== 0) {
            this.ctx.restore();
        }
    }

    applyDisplaySettings() {
        if (!this.canvas) return;
        
        // Apply CSS filters for display settings
        const filters = [
            `brightness(${this.brightness}%)`,
            `contrast(${this.contrast}%)`,
            `saturate(${this.saturation}%)`,
            `hue-rotate(${this.hue}deg)`
        ];
        
        // Add color temperature filter
        const tempFilter = this.getColorTempFilter(this.colorTemp);
        if (tempFilter) filters.push(tempFilter);
        
        this.canvas.style.filter = filters.join(' ');
        
        // Apply rotation
        this.canvas.style.transform = `rotate(${this.rotation}deg)`;
    }

    getColorTempFilter(temp) {
        // Convert color temperature to filter
        if (temp >= 6500) return 'sepia(0%) saturate(100%) hue-rotate(0deg)';
        if (temp >= 5500) return 'sepia(10%) saturate(90%) hue-rotate(-10deg)';
        if (temp >= 4500) return 'sepia(20%) saturate(80%) hue-rotate(-20deg)';
        return 'sepia(30%) saturate(70%) hue-rotate(-30deg)';
    }

    showNoSignalPattern() {
        if (!this.isPowered) return;
        
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Create static noise pattern
        const imageData = this.ctx.createImageData(this.canvas.width, this.canvas.height);
        const data = imageData.data;
        
        for (let i = 0; i < data.length; i += 4) {
            const noise = Math.random() * 50;
            data[i] = noise;     // Red
            data[i + 1] = noise; // Green
            data[i + 2] = noise; // Blue
            data[i + 3] = 255;   // Alpha
        }
        
        this.ctx.putImageData(imageData, 0, 0);
        
        // Add "No Signal" text
        this.ctx.fillStyle = '#00d4ff';
        this.ctx.font = '48px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('No Signal', this.canvas.width / 2, this.canvas.height / 2);
        
        this.ctx.font = '24px Arial';
        this.ctx.fillText(`Input: ${this.inputSource.toUpperCase()}`, this.canvas.width / 2, this.canvas.height / 2 + 60);
    }

    togglePower() {
        this.isPowered = !this.isPowered;
        const powerLed = document.getElementById('power-led');
        const monitorBezel = document.querySelector('.monitor-bezel');
        
        if (this.isPowered) {
            powerLed.classList.add('on');
            monitorBezel.classList.remove('powered-off');
            this.logEvent('Monitor powered ON');
            if (this.isConnected) {
                this.connectToVNC();
            } else {
                this.showNoSignalPattern();
            }
        } else {
            powerLed.classList.remove('on');
            monitorBezel.classList.add('powered-off');
            this.ctx.fillStyle = '#000';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.logEvent('Monitor powered OFF');
        }
    }

    changeResolution(resolution) {
        const [width, height] = resolution.split('x').map(Number);
        this.currentResolution = { width, height };
        
        this.canvas.width = width;
        this.canvas.height = height;
        this.setupCanvas();
        
        document.getElementById('current-resolution').textContent = resolution;
        this.logEvent(`Resolution changed to: ${resolution}`);
        
        // Notify backend
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'change_resolution',
                resolution: { width, height }
            }));
        }
    }

    changeRefreshRate(rate) {
        this.refreshRate = rate;
        document.getElementById('current-refresh').textContent = `${rate} Hz`;
        this.logEvent(`Refresh rate changed to: ${rate} Hz`);
    }

    changeInputSource(source) {
        this.inputSource = source;
        document.getElementById('current-input').textContent = source.toUpperCase();
        this.logEvent(`Input source changed to: ${source.toUpperCase()}`);
        
        // Reconnect VNC for new source
        if (this.vncWs) {
            this.vncWs.close();
        }
        if (this.isConnected && this.isPowered) {
            setTimeout(() => this.connectToVNC(), 500);
        }
    }

    cycleInputSource() {
        const sources = ['hdmi1', 'hdmi2', 'vga', 'dvi'];
        const currentIndex = sources.indexOf(this.inputSource);
        const nextIndex = (currentIndex + 1) % sources.length;
        
        this.changeInputSource(sources[nextIndex]);
        document.getElementById('input-source').value = sources[nextIndex];
    }

    startCapture() {
        this.isCapturing = true;
        this.logEvent('Screen capture started');
        
        // Start capture backend process
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'start_capture',
                quality: this.streamQuality,
                frameRate: this.frameRate
            }));
        }
    }

    stopCapture() {
        this.isCapturing = false;
        this.logEvent('Screen capture stopped');
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'stop_capture'
            }));
        }
    }

    takeScreenshot() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `screenshot-${timestamp}.png`;
        
        // Create download link
        const link = document.createElement('a');
        link.download = filename;
        link.href = this.canvas.toDataURL('image/png');
        link.click();
        
        this.logEvent(`Screenshot saved: ${filename}`);
    }

    toggleFullscreen() {
        const container = document.querySelector('.container');
        
        if (!this.isFullscreen) {
            container.classList.add('fullscreen');
            this.isFullscreen = true;
            this.logEvent('Entered fullscreen mode');
        } else {
            container.classList.remove('fullscreen');
            this.isFullscreen = false;
            this.logEvent('Exited fullscreen mode');
        }
    }

    handleCanvasClick(event) {
        // Send click coordinates to RPi
        const rect = this.canvas.getBoundingClientRect();
        const x = (event.clientX - rect.left) * (this.canvas.width / rect.width);
        const y = (event.clientY - rect.top) * (this.canvas.height / rect.height);
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'canvas_click',
                x: Math.round(x),
                y: Math.round(y)
            }));
        }
        
        this.logEvent(`Canvas clicked at: (${Math.round(x)}, ${Math.round(y)})`);
    }

    updateFrameStats() {
        const now = Date.now();
        this.frameStats.received++;
        
        if (this.lastFrameTime > 0) {
            const frameTime = now - this.lastFrameTime;
            this.frameStats.latency = frameTime;
        }
        
        this.lastFrameTime = now;
    }

    startFrameStatsUpdate() {
        setInterval(() => {
            // Calculate actual FPS
            const framesInInterval = this.frameStats.received - (this.lastFrameCount || 0);
            this.frameStats.actualFps = framesInInterval;
            this.lastFrameCount = this.frameStats.received;
            
            // Update UI
            document.getElementById('frames-received').textContent = this.frameStats.received;
            document.getElementById('actual-fps').textContent = `${this.frameStats.actualFps} FPS`;
            document.getElementById('latency').textContent = `${this.frameStats.latency} ms`;
            document.getElementById('data-rate').textContent = `${Math.round(this.frameStats.actualFps * 50)} KB/s`;
        }, 1000);
    }

    updateStatus(message) {
        document.getElementById('status').textContent = message;
        const led = document.getElementById('status-led');
        const rpiConnection = document.getElementById('rpi-connection');
        
        if (this.isConnected) {
            led.classList.add('connected');
            rpiConnection.textContent = 'Connected';
            rpiConnection.className = 'value connected';
        } else {
            led.classList.remove('connected');
            rpiConnection.textContent = 'Disconnected';
            rpiConnection.className = 'value error';
        }
    }

    updateDisplayInfo() {
        document.getElementById('current-resolution').textContent = 
            `${this.currentResolution.width}x${this.currentResolution.height}`;
        document.getElementById('current-refresh').textContent = `${this.refreshRate} Hz`;
        document.getElementById('current-input').textContent = this.inputSource.toUpperCase();
    }

    showMonitorMenu() {
        // Simple menu simulation
        this.logEvent('Monitor OSD menu opened');
        
        // Create temporary overlay
        const overlay = document.createElement('div');
        overlay.style.position = 'absolute';
        overlay.style.top = '50px';
        overlay.style.left = '50px';
        overlay.style.background = 'rgba(0, 0, 0, 0.8)';
        overlay.style.color = '#00d4ff';
        overlay.style.padding = '20px';
        overlay.style.borderRadius = '8px';
        overlay.style.zIndex = '1000';
        overlay.innerHTML = `
            <div>MONITOR MENU</div>
            <div>Brightness: ${this.brightness}%</div>
            <div>Contrast: ${this.contrast}%</div>
            <div>Input: ${this.inputSource.toUpperCase()}</div>
        `;
        
        this.canvas.parentElement.appendChild(overlay);
        
        setTimeout(() => {
            overlay.remove();
        }, 3000);
    }

    logEvent(message) {
        const log = document.getElementById('event-log');
        const timestamp = new Date().toLocaleTimeString();
        log.innerHTML += `[${timestamp}] ${message}\n`;
        log.scrollTop = log.scrollHeight;
    }
}

// Initialize HMI Virtual Monitor when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.hmiMonitor = new HMIVirtualMonitor();
});
