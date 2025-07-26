class HMIVirtualKeyboard {
    constructor() {
        this.isConnected = false;
        this.inputText = '';
        this.cursorPosition = 0;
        this.isShiftPressed = false;
        this.isCapsLockOn = false;
        this.isNumLockOn = true;
        this.isScrollLockOn = false;
        this.isCtrlPressed = false;
        this.isAltPressed = false;
        this.isMetaPressed = false;
        this.keyRepeatEnabled = true;
        this.clickSoundEnabled = true;
        this.currentLayout = 'qwerty';
        this.pressedKeys = new Set();
        this.ws = null;
        
        this.keyLayouts = {
            qwerty: {
                '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
                '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
                ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
                '`': '~'
            },
            qwertz: {
                'y': 'z', 'z': 'y', '-': '_', '=': '+',
                // Add more QWERTZ specific mappings
            },
            azerty: {
                'q': 'a', 'w': 'z', 'a': 'q', 'z': 'w',
                // Add more AZERTY specific mappings
            }
        };
        
        this.init();
        this.setupEventListeners();
        this.setupWebSocket();
    }

    init() {
        this.updateStatus('Initializing...');
        this.updateIndicators();
        this.setupControls();
        
        // Initialize cursor blinking
        setInterval(() => {
            const cursor = document.getElementById('cursor');
            cursor.style.opacity = cursor.style.opacity === '0' ? '1' : '0';
        }, 500);
    }

    setupEventListeners() {
        // Virtual keyboard keys
        document.querySelectorAll('.key').forEach(key => {
            key.addEventListener('mousedown', this.handleKeyPress.bind(this));
            key.addEventListener('mouseup', this.handleKeyRelease.bind(this));
            key.addEventListener('mouseleave', this.handleKeyRelease.bind(this));
        });

        // Physical keyboard events
        document.addEventListener('keydown', this.handlePhysicalKeyDown.bind(this));
        document.addEventListener('keyup', this.handlePhysicalKeyUp.bind(this));

        // Control buttons
        document.getElementById('clear-display').addEventListener('click', () => {
            this.clearDisplay();
        });

        document.getElementById('send-ctrl-c').addEventListener('click', () => {
            this.sendKeyCombo(['ControlLeft', 'c']);
        });

        document.getElementById('send-ctrl-z').addEventListener('click', () => {
            this.sendKeyCombo(['ControlLeft', 'z']);
        });

        document.getElementById('send-alt-tab').addEventListener('click', () => {
            this.sendKeyCombo(['AltLeft', 'Tab']);
        });

        document.getElementById('toggle-numpad').addEventListener('click', () => {
            this.toggleNumpad();
        });

        // Settings
        document.getElementById('key-repeat').addEventListener('change', (e) => {
            this.keyRepeatEnabled = e.target.checked;
        });

        document.getElementById('click-sound').addEventListener('change', (e) => {
            this.clickSoundEnabled = e.target.checked;
        });

        document.getElementById('layout-select').addEventListener('change', (e) => {
            this.currentLayout = e.target.value;
            this.logEvent(`Layout changed to: ${e.target.value.toUpperCase()}`);
        });

        document.getElementById('clear-log').addEventListener('click', () => {
            document.getElementById('event-log').innerHTML = '';
        });

        // Prevent context menu on keys
        document.querySelectorAll('.key').forEach(key => {
            key.addEventListener('contextmenu', (e) => e.preventDefault());
        });
    }

    setupWebSocket() {
        try {
            // Connect to RPi emulator for sending keyboard events
            this.ws = new WebSocket('ws://localhost:4000/ws/keyboard');
            
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

    handleKeyPress(event) {
        const key = event.currentTarget;
        const keyCode = key.dataset.key;
        
        if (this.pressedKeys.has(keyCode)) return; // Prevent key repeat
        
        this.pressedKeys.add(keyCode);
        key.classList.add('pressed');
        
        this.processKeyPress(keyCode, key);
        this.playClickSound();
        this.createKeyPressEffect(event.currentTarget);
    }

    handleKeyRelease(event) {
        const key = event.currentTarget;
        const keyCode = key.dataset.key;
        
        this.pressedKeys.delete(keyCode);
        key.classList.remove('pressed');
        
        this.processKeyRelease(keyCode);
    }

    handlePhysicalKeyDown(event) {
        // Prevent default browser shortcuts
        if (event.ctrlKey && ['a', 's', 'r', 'f', 'p'].includes(event.key.toLowerCase())) {
            event.preventDefault();
        }
        
        this.highlightVirtualKey(event.code, true);
        this.processKeyPress(event.code);
    }

    handlePhysicalKeyUp(event) {
        this.highlightVirtualKey(event.code, false);
        this.processKeyRelease(event.code);
    }

    processKeyPress(keyCode, keyElement = null) {
        // Handle modifier keys
        if (this.isModifierKey(keyCode)) {
            this.handleModifierKey(keyCode, true);
            return;
        }

        // Handle special keys
        if (this.isSpecialKey(keyCode)) {
            this.handleSpecialKey(keyCode);
            return;
        }

        // Handle character input
        this.handleCharacterInput(keyCode, keyElement);
        
        // Send to RPi
        this.sendKeyEvent('keydown', keyCode);
        
        this.logEvent(`Key pressed: ${keyCode}`);
    }

    processKeyRelease(keyCode) {
        // Handle modifier key release
        if (this.isModifierKey(keyCode)) {
            this.handleModifierKey(keyCode, false);
        }
        
        // Send to RPi
        this.sendKeyEvent('keyup', keyCode);
    }

    isModifierKey(keyCode) {
        return ['ShiftLeft', 'ShiftRight', 'ControlLeft', 'ControlRight', 
                'AltLeft', 'AltRight', 'MetaLeft', 'MetaRight'].includes(keyCode);
    }

    isSpecialKey(keyCode) {
        return ['Enter', 'Backspace', 'Tab', 'CapsLock', 'NumLock', 
                'ScrollLock', 'Escape', 'Delete', 'Insert', 'Home', 'End',
                'PageUp', 'PageDown', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(keyCode);
    }

    handleModifierKey(keyCode, isPressed) {
        switch (keyCode) {
            case 'ShiftLeft':
            case 'ShiftRight':
                this.isShiftPressed = isPressed;
                break;
            case 'ControlLeft':
            case 'ControlRight':
                this.isCtrlPressed = isPressed;
                break;
            case 'AltLeft':
            case 'AltRight':
                this.isAltPressed = isPressed;
                break;
            case 'MetaLeft':
            case 'MetaRight':
                this.isMetaPressed = isPressed;
                break;
        }
        
        // Update visual feedback for modifier keys
        this.updateModifierKeyVisuals();
    }

    handleSpecialKey(keyCode) {
        switch (keyCode) {
            case 'Enter':
                this.inputText = this.inputText.slice(0, this.cursorPosition) + '\n' + 
                                this.inputText.slice(this.cursorPosition);
                this.cursorPosition++;
                break;
                
            case 'Backspace':
                if (this.cursorPosition > 0) {
                    this.inputText = this.inputText.slice(0, this.cursorPosition - 1) + 
                                    this.inputText.slice(this.cursorPosition);
                    this.cursorPosition--;
                }
                break;
                
            case 'Delete':
                if (this.cursorPosition < this.inputText.length) {
                    this.inputText = this.inputText.slice(0, this.cursorPosition) + 
                                    this.inputText.slice(this.cursorPosition + 1);
                }
                break;
                
            case 'Tab':
                this.inputText = this.inputText.slice(0, this.cursorPosition) + '\t' + 
                                this.inputText.slice(this.cursorPosition);
                this.cursorPosition++;
                break;
                
            case 'CapsLock':
                this.isCapsLockOn = !this.isCapsLockOn;
                break;
                
            case 'NumLock':
                this.isNumLockOn = !this.isNumLockOn;
                break;
                
            case 'ScrollLock':
                this.isScrollLockOn = !this.isScrollLockOn;
                break;
                
            case 'ArrowLeft':
                if (this.cursorPosition > 0) this.cursorPosition--;
                break;
                
            case 'ArrowRight':
                if (this.cursorPosition < this.inputText.length) this.cursorPosition++;
                break;
                
            case 'Home':
                this.cursorPosition = 0;
                break;
                
            case 'End':
                this.cursorPosition = this.inputText.length;
                break;
        }
        
        this.updateDisplay();
        this.updateIndicators();
    }

    handleCharacterInput(keyCode, keyElement) {
        let char = '';
        
        if (keyElement && keyElement.dataset.key) {
            char = keyElement.dataset.key;
            
            // Handle shift/caps for letters
            if (char.match(/[a-z]/)) {
                if (this.isShiftPressed !== this.isCapsLockOn) {
                    char = char.toUpperCase();
                }
            }
            // Handle shift for symbols
            else if (this.isShiftPressed && keyElement.dataset.shift) {
                char = keyElement.dataset.shift;
            }
            // Handle space
            else if (char === ' ') {
                char = ' ';
            }
        } else {
            // Handle numpad keys
            if (keyCode.startsWith('Numpad') && this.isNumLockOn) {
                const numpadMap = {
                    'Numpad0': '0', 'Numpad1': '1', 'Numpad2': '2', 'Numpad3': '3',
                    'Numpad4': '4', 'Numpad5': '5', 'Numpad6': '6', 'Numpad7': '7',
                    'Numpad8': '8', 'Numpad9': '9', 'NumpadDecimal': '.',
                    'NumpadAdd': '+', 'NumpadSubtract': '-', 'NumpadMultiply': '*',
                    'NumpadDivide': '/'
                };
                char = numpadMap[keyCode] || '';
            }
        }
        
        if (char && char !== keyCode) {
            this.inputText = this.inputText.slice(0, this.cursorPosition) + char + 
                            this.inputText.slice(this.cursorPosition);
            this.cursorPosition++;
            this.updateDisplay();
        }
    }

    sendKeyEvent(type, keyCode) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const event = {
                type: type,
                key: keyCode,
                modifiers: {
                    shift: this.isShiftPressed,
                    ctrl: this.isCtrlPressed,
                    alt: this.isAltPressed,
                    meta: this.isMetaPressed
                },
                timestamp: Date.now(),
                device: 'hmi-keyboard'
            };
            
            this.ws.send(JSON.stringify(event));
        }
    }

    sendKeyCombo(keys) {
        keys.forEach((key, index) => {
            setTimeout(() => {
                this.sendKeyEvent('keydown', key);
            }, index * 50);
        });
        
        setTimeout(() => {
            keys.reverse().forEach((key, index) => {
                setTimeout(() => {
                    this.sendKeyEvent('keyup', key);
                }, index * 50);
            });
        }, keys.length * 50 + 100);
        
        this.logEvent(`Key combo sent: ${keys.join('+')}`);
    }

    highlightVirtualKey(keyCode, isPressed) {
        const keyElement = document.querySelector(`[data-key="${keyCode}"]`);
        if (keyElement) {
            if (isPressed) {
                keyElement.classList.add('pressed');
            } else {
                keyElement.classList.remove('pressed');
            }
        }
    }

    updateDisplay() {
        const displayText = this.inputText.slice(0, this.cursorPosition) + 
                           '|' + this.inputText.slice(this.cursorPosition);
        document.getElementById('input-text').textContent = this.inputText;
        
        // Update cursor position visually
        this.updateCursorPosition();
    }

    updateCursorPosition() {
        // This would need more sophisticated implementation for proper cursor positioning
        // For now, we just show the cursor at the end
        const cursor = document.getElementById('cursor');
        cursor.style.display = 'inline';
    }

    updateIndicators() {
        const capsIndicator = document.getElementById('caps-lock');
        const numIndicator = document.getElementById('num-lock');
        const scrollIndicator = document.getElementById('scroll-lock');
        
        capsIndicator.classList.toggle('active', this.isCapsLockOn);
        numIndicator.classList.toggle('active', this.isNumLockOn);
        scrollIndicator.classList.toggle('active', this.isScrollLockOn);
    }

    updateModifierKeyVisuals() {
        // Update visual feedback for pressed modifier keys
        document.querySelectorAll('[data-key^="Shift"]').forEach(key => {
            key.classList.toggle('pressed', this.isShiftPressed);
        });
        
        document.querySelectorAll('[data-key^="Control"]').forEach(key => {
            key.classList.toggle('pressed', this.isCtrlPressed);
        });
        
        document.querySelectorAll('[data-key^="Alt"]').forEach(key => {
            key.classList.toggle('pressed', this.isAltPressed);
        });
        
        document.querySelectorAll('[data-key^="Meta"]').forEach(key => {
            key.classList.toggle('pressed', this.isMetaPressed);
        });
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

    clearDisplay() {
        this.inputText = '';
        this.cursorPosition = 0;
        this.updateDisplay();
        this.logEvent('Display cleared');
    }

    toggleNumpad() {
        const numpad = document.getElementById('numpad');
        numpad.classList.toggle('hidden');
        this.logEvent('Numpad toggled');
    }

    playClickSound() {
        if (this.clickSoundEnabled) {
            // Create a simple click sound using Web Audio API
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.1);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.1);
            } catch (error) {
                // Ignore audio errors
            }
        }
    }

    createKeyPressEffect(keyElement) {
        const rect = keyElement.getBoundingClientRect();
        const effect = document.createElement('div');
        effect.className = 'key-press-effect';
        effect.style.position = 'fixed';
        effect.style.left = (rect.left + rect.width / 2) + 'px';
        effect.style.top = (rect.top + rect.height / 2) + 'px';
        effect.style.pointerEvents = 'none';
        effect.style.zIndex = '1000';
        
        document.body.appendChild(effect);
        
        setTimeout(() => {
            document.body.removeChild(effect);
        }, 400);
    }

    logEvent(message) {
        const log = document.getElementById('event-log');
        const timestamp = new Date().toLocaleTimeString();
        log.innerHTML += `[${timestamp}] ${message}\n`;
        log.scrollTop = log.scrollHeight;
    }

    setupControls() {
        // Initialize control values
        document.getElementById('key-repeat').checked = this.keyRepeatEnabled;
        document.getElementById('click-sound').checked = this.clickSoundEnabled;
        document.getElementById('layout-select').value = this.currentLayout;
    }
}

// Initialize HMI Virtual Keyboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.hmiKeyboard = new HMIVirtualKeyboard();
});
