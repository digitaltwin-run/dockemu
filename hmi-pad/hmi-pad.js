class HMITouchPad {
    constructor() {
        this.canvas = document.getElementById('touchpad');
        this.ctx = this.canvas.getContext('2d');
        this.isConnected = false;
        this.currentTouches = new Map();
        this.sensitivity = 1.0;
        this.multiTouchEnabled = true;
        this.pressureSensitive = true;
        
        this.init();
        this.setupEventListeners();
        this.setupWebSocket();
    }

    init() {
        // Initialize canvas
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Initialize UI elements
        this.updateStatus('Initializing...');
        this.setupControls();
    }

    setupEventListeners() {
        // Touch events
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse events (for desktop testing)
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.handleMouseUp.bind(this));
        
        // Gesture buttons
        document.getElementById('tap').addEventListener('click', () => this.simulateGesture('tap'));
        document.getElementById('double-tap').addEventListener('click', () => this.simulateGesture('double-tap'));
        document.getElementById('long-press').addEventListener('click', () => this.simulateGesture('long-press'));
        document.getElementById('swipe-left').addEventListener('click', () => this.simulateGesture('swipe-left'));
        document.getElementById('swipe-right').addEventListener('click', () => this.simulateGesture('swipe-right'));
        document.getElementById('swipe-up').addEventListener('click', () => this.simulateGesture('swipe-up'));
        document.getElementById('swipe-down').addEventListener('click', () => this.simulateGesture('swipe-down'));
        document.getElementById('pinch').addEventListener('click', () => this.simulateGesture('pinch'));
        document.getElementById('zoom').addEventListener('click', () => this.simulateGesture('zoom'));
        
        // Settings
        const sensitivitySlider = document.getElementById('sensitivity');
        sensitivitySlider.addEventListener('input', (e) => {
            this.sensitivity = parseFloat(e.target.value);
            document.getElementById('sensitivity-value').textContent = this.sensitivity.toFixed(1);
        });
        
        document.getElementById('multi-touch').addEventListener('change', (e) => {
            this.multiTouchEnabled = e.target.checked;
        });
        
        document.getElementById('pressure-sensitive').addEventListener('change', (e) => {
            this.pressureSensitive = e.target.checked;
        });
        
        // Clear log
        document.getElementById('clear-log').addEventListener('click', () => {
            document.getElementById('event-log').innerHTML = '';
        });
    }

    setupWebSocket() {
        // Connect to RPI emulator for sending touch events
        try {
            this.ws = new WebSocket('ws://localhost:4000/ws/touch');
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateStatus('Connected to RPI');
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateStatus('Disconnected');
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

    handleTouchStart(e) {
        e.preventDefault();
        const touches = e.changedTouches;
        
        for (let i = 0; i < touches.length; i++) {
            const touch = touches[i];
            const rect = this.canvas.getBoundingClientRect();
            const x = (touch.clientX - rect.left) * this.sensitivity;
            const y = (touch.clientY - rect.top) * this.sensitivity;
            const pressure = this.pressureSensitive ? (touch.force || 0.5) : 0.5;
            
            this.currentTouches.set(touch.identifier, { x, y, pressure, startTime: Date.now() });
            this.drawTouchPoint(x, y, pressure);
            this.updateCoordinates(x, y, pressure);
            this.sendTouchEvent('touch_start', x, y, pressure, touch.identifier);
            this.logEvent(`Touch Start: (${x.toFixed(0)}, ${y.toFixed(0)}) P:${pressure.toFixed(2)}`);
        }
    }

    handleTouchMove(e) {
        e.preventDefault();
        const touches = e.changedTouches;
        
        for (let i = 0; i < touches.length; i++) {
            const touch = touches[i];
            if (this.currentTouches.has(touch.identifier)) {
                const rect = this.canvas.getBoundingClientRect();
                const x = (touch.clientX - rect.left) * this.sensitivity;
                const y = (touch.clientY - rect.top) * this.sensitivity;
                const pressure = this.pressureSensitive ? (touch.force || 0.5) : 0.5;
                
                this.currentTouches.set(touch.identifier, { x, y, pressure, startTime: this.currentTouches.get(touch.identifier).startTime });
                this.drawTouchPoint(x, y, pressure);
                this.updateCoordinates(x, y, pressure);
                this.sendTouchEvent('touch_move', x, y, pressure, touch.identifier);
            }
        }
    }

    handleTouchEnd(e) {
        e.preventDefault();
        const touches = e.changedTouches;
        
        for (let i = 0; i < touches.length; i++) {
            const touch = touches[i];
            if (this.currentTouches.has(touch.identifier)) {
                const touchData = this.currentTouches.get(touch.identifier);
                const duration = Date.now() - touchData.startTime;
                
                this.sendTouchEvent('touch_end', touchData.x, touchData.y, touchData.pressure, touch.identifier);
                this.logEvent(`Touch End: (${touchData.x.toFixed(0)}, ${touchData.y.toFixed(0)}) Duration:${duration}ms`);
                this.currentTouches.delete(touch.identifier);
            }
        }
        
        if (this.currentTouches.size === 0) {
            this.clearCanvas();
            this.updateCoordinates(0, 0, 0);
        }
    }

    // Mouse events for desktop testing
    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * this.sensitivity;
        const y = (e.clientY - rect.top) * this.sensitivity;
        const pressure = 0.8;
        
        this.currentTouches.set('mouse', { x, y, pressure, startTime: Date.now() });
        this.drawTouchPoint(x, y, pressure);
        this.updateCoordinates(x, y, pressure);
        this.sendTouchEvent('touch_start', x, y, pressure, 'mouse');
        this.logEvent(`Mouse Down: (${x.toFixed(0)}, ${y.toFixed(0)})`);
    }

    handleMouseMove(e) {
        if (this.currentTouches.has('mouse')) {
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) * this.sensitivity;
            const y = (e.clientY - rect.top) * this.sensitivity;
            const pressure = 0.8;
            
            this.currentTouches.set('mouse', { x, y, pressure, startTime: this.currentTouches.get('mouse').startTime });
            this.drawTouchPoint(x, y, pressure);
            this.updateCoordinates(x, y, pressure);
            this.sendTouchEvent('touch_move', x, y, pressure, 'mouse');
        }
    }

    handleMouseUp(e) {
        if (this.currentTouches.has('mouse')) {
            const touchData = this.currentTouches.get('mouse');
            const duration = Date.now() - touchData.startTime;
            
            this.sendTouchEvent('touch_end', touchData.x, touchData.y, touchData.pressure, 'mouse');
            this.logEvent(`Mouse Up: (${touchData.x.toFixed(0)}, ${touchData.y.toFixed(0)}) Duration:${duration}ms`);
            this.currentTouches.delete('mouse');
            this.clearCanvas();
            this.updateCoordinates(0, 0, 0);
        }
    }

    drawTouchPoint(x, y, pressure) {
        this.clearCanvas();
        
        // Draw touch point
        const radius = 10 + (pressure * 20);
        const opacity = 0.3 + (pressure * 0.7);
        
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.fillStyle = `rgba(52, 152, 219, ${opacity})`;
        this.ctx.fill();
        
        // Draw crosshair
        this.ctx.strokeStyle = '#2980b9';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(x - 15, y);
        this.ctx.lineTo(x + 15, y);
        this.ctx.moveTo(x, y - 15);
        this.ctx.lineTo(x, y + 15);
        this.ctx.stroke();
    }

    clearCanvas() {
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    updateCoordinates(x, y, pressure) {
        document.getElementById('coord-x').textContent = Math.round(x);
        document.getElementById('coord-y').textContent = Math.round(y);
        document.getElementById('pressure').textContent = pressure.toFixed(2);
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

    sendTouchEvent(type, x, y, pressure, touchId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const event = {
                type: type,
                x: Math.round(x),
                y: Math.round(y),
                pressure: pressure,
                touchId: touchId,
                timestamp: Date.now(),
                device: 'hmi-pad'
            };
            
            this.ws.send(JSON.stringify(event));
        }
    }

    simulateGesture(gesture) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        switch (gesture) {
            case 'tap':
                this.simulateTap(centerX, centerY);
                break;
            case 'double-tap':
                this.simulateDoubleTap(centerX, centerY);
                break;
            case 'long-press':
                this.simulateLongPress(centerX, centerY);
                break;
            case 'swipe-left':
                this.simulateSwipe(centerX + 100, centerY, centerX - 100, centerY);
                break;
            case 'swipe-right':
                this.simulateSwipe(centerX - 100, centerY, centerX + 100, centerY);
                break;
            case 'swipe-up':
                this.simulateSwipe(centerX, centerY + 100, centerX, centerY - 100);
                break;
            case 'swipe-down':
                this.simulateSwipe(centerX, centerY - 100, centerX, centerY + 100);
                break;
            case 'pinch':
                this.simulatePinch();
                break;
            case 'zoom':
                this.simulateZoom();
                break;
        }
    }

    simulateTap(x, y) {
        this.drawTouchPoint(x, y, 0.8);
        this.sendTouchEvent('touch_start', x, y, 0.8, 'sim');
        setTimeout(() => {
            this.sendTouchEvent('touch_end', x, y, 0.8, 'sim');
            this.clearCanvas();
        }, 100);
        this.logEvent(`Simulated Tap: (${x}, ${y})`);
    }

    simulateDoubleTap(x, y) {
        this.simulateTap(x, y);
        setTimeout(() => this.simulateTap(x, y), 200);
        this.logEvent(`Simulated Double Tap: (${x}, ${y})`);
    }

    simulateLongPress(x, y) {
        this.drawTouchPoint(x, y, 0.8);
        this.sendTouchEvent('touch_start', x, y, 0.8, 'sim');
        setTimeout(() => {
            this.sendTouchEvent('touch_end', x, y, 0.8, 'sim');
            this.clearCanvas();
        }, 1000);
        this.logEvent(`Simulated Long Press: (${x}, ${y})`);
    }

    simulateSwipe(startX, startY, endX, endY) {
        const steps = 20;
        const stepX = (endX - startX) / steps;
        const stepY = (endY - startY) / steps;
        
        this.sendTouchEvent('touch_start', startX, startY, 0.8, 'sim');
        
        let currentStep = 0;
        const animate = () => {
            if (currentStep < steps) {
                const x = startX + (stepX * currentStep);
                const y = startY + (stepY * currentStep);
                this.drawTouchPoint(x, y, 0.8);
                this.sendTouchEvent('touch_move', x, y, 0.8, 'sim');
                currentStep++;
                setTimeout(animate, 30);
            } else {
                this.sendTouchEvent('touch_end', endX, endY, 0.8, 'sim');
                this.clearCanvas();
            }
        };
        
        animate();
        this.logEvent(`Simulated Swipe: (${startX}, ${startY}) -> (${endX}, ${endY})`);
    }

    simulatePinch() {
        // Simulate two-finger pinch gesture
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        this.sendTouchEvent('touch_start', centerX - 50, centerY, 0.8, 'sim1');
        this.sendTouchEvent('touch_start', centerX + 50, centerY, 0.8, 'sim2');
        
        setTimeout(() => {
            this.sendTouchEvent('touch_move', centerX - 20, centerY, 0.8, 'sim1');
            this.sendTouchEvent('touch_move', centerX + 20, centerY, 0.8, 'sim2');
        }, 100);
        
        setTimeout(() => {
            this.sendTouchEvent('touch_end', centerX - 20, centerY, 0.8, 'sim1');
            this.sendTouchEvent('touch_end', centerX + 20, centerY, 0.8, 'sim2');
        }, 300);
        
        this.logEvent('Simulated Pinch Gesture');
    }

    simulateZoom() {
        // Simulate two-finger zoom gesture
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        this.sendTouchEvent('touch_start', centerX - 20, centerY, 0.8, 'sim1');
        this.sendTouchEvent('touch_start', centerX + 20, centerY, 0.8, 'sim2');
        
        setTimeout(() => {
            this.sendTouchEvent('touch_move', centerX - 80, centerY, 0.8, 'sim1');
            this.sendTouchEvent('touch_move', centerX + 80, centerY, 0.8, 'sim2');
        }, 100);
        
        setTimeout(() => {
            this.sendTouchEvent('touch_end', centerX - 80, centerY, 0.8, 'sim1');
            this.sendTouchEvent('touch_end', centerX + 80, centerY, 0.8, 'sim2');
        }, 300);
        
        this.logEvent('Simulated Zoom Gesture');
    }

    logEvent(message) {
        const log = document.getElementById('event-log');
        const timestamp = new Date().toLocaleTimeString();
        log.innerHTML += `[${timestamp}] ${message}\n`;
        log.scrollTop = log.scrollHeight;
    }

    setupControls() {
        // Initialize control values
        document.getElementById('sensitivity-value').textContent = this.sensitivity.toFixed(1);
    }
}

// Initialize HMI Touch Pad when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.hmiTouchPad = new HMITouchPad();
});
