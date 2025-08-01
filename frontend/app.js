// C20 Hardware Simulator Dashboard JavaScript
class DashboardController {
    constructor() {
        // Initialize component logging
        this.logger = window.Logger;
        this.logger.componentStart('DashboardController', {
            timestamp: new Date().toISOString()
        });
        
        // Wait for configuration to load
        if (typeof window.SERVICES_CONFIG === 'undefined') {
            this.logger.error('Configuration not loaded! Make sure config.js is included before app.js', {
                availableGlobals: Object.keys(window).filter(key => key.includes('CONFIG')),
                scripts: Array.from(document.scripts).map(s => s.src)
            });
            return;
        }
        
        // Build services from generated configuration
        this.services = {
            lcd: { 
                url: window.SERVICES_CONFIG.lcd_display.url, 
                active: true, 
                name: window.SERVICES_CONFIG.lcd_display.name,
                icon: window.SERVICES_CONFIG.lcd_display.icon,
                description: window.SERVICES_CONFIG.lcd_display.description
            },
            keyboard: { 
                url: window.SERVICES_CONFIG.hui_keyboard.url, 
                active: true, 
                name: window.SERVICES_CONFIG.hui_keyboard.name,
                icon: window.SERVICES_CONFIG.hui_keyboard.icon,
                description: window.SERVICES_CONFIG.hui_keyboard.description
            },
            modbus: { 
                url: window.SERVICES_CONFIG.modbus_visualizer.url, 
                active: true, 
                name: window.SERVICES_CONFIG.modbus_visualizer.name,
                icon: window.SERVICES_CONFIG.modbus_visualizer.icon,
                description: window.SERVICES_CONFIG.modbus_visualizer.description
            },
            'hmi-pad': {
                url: window.SERVICES_CONFIG.hmi_pad.url,
                active: true,
                name: window.SERVICES_CONFIG.hmi_pad.name,
                icon: window.SERVICES_CONFIG.hmi_pad.icon,
                description: window.SERVICES_CONFIG.hmi_pad.description
            },
            'hmi-keyboard': {
                url: window.SERVICES_CONFIG.hmi_keyboard.url,
                active: true,
                name: window.SERVICES_CONFIG.hmi_keyboard.name,
                icon: window.SERVICES_CONFIG.hmi_keyboard.icon,
                description: window.SERVICES_CONFIG.hmi_keyboard.description
            },
            'hmi-numpad': {
                url: window.SERVICES_CONFIG.hmi_numpad.url,
                active: true,
                name: window.SERVICES_CONFIG.hmi_numpad.name,
                icon: window.SERVICES_CONFIG.hmi_numpad.icon,
                description: window.SERVICES_CONFIG.hmi_numpad.description
            }
        };
        this.currentLayout = 'grid';
        this.focusedService = null;
        this.init();
    }

    init() {
        this.logger.info('Initializing Dashboard Controller', {
            services: Object.keys(this.services),
            currentLayout: this.currentLayout
        });
        
        this.logger.time('dashboard_initialization');
        
        try {
            this.logger.debug('Setting up event listeners');
            this.setupEventListeners();
            
            this.logger.debug('Updating initial time display');
            this.updateTime();
            
            this.logger.debug('Checking initial service status');
            this.checkServiceStatus();
            
            this.logger.debug('Hiding loading overlay');
            this.hideLoadingOverlay();
            
            this.logger.debug('Updating system information');
            this.updateSystemInfo();
            
            // Auto-refresh intervals
            this.logger.debug('Setting up auto-refresh intervals');
            this.timeUpdateInterval = setInterval(() => this.updateTime(), 1000);
            this.statusCheckInterval = setInterval(() => this.checkServiceStatus(), 30000);
            this.systemInfoInterval = setInterval(() => this.updateSystemInfo(), 10000);
            
            this.logger.componentEnd('DashboardController');
            this.logger.timeEnd('dashboard_initialization');
            
            this.logger.info('Dashboard Controller initialized successfully', {
                totalServices: Object.keys(this.services).length,
                activeServices: Object.values(this.services).filter(s => s.active).length
            });
        } catch (error) {
            this.logger.error('Failed to initialize Dashboard Controller', {
                error: error.message,
                stack: error.stack
            });
            throw error;
        }
    }

    setupEventListeners() {
        // Layout controls
        document.querySelectorAll('.layout-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const layout = e.currentTarget.dataset.layout;
                this.switchLayout(layout);
            });
        });

        // Service toggles
        document.querySelectorAll('.service-toggle').forEach(toggle => {
            const switchEl = toggle.querySelector('.toggle-switch');
            switchEl.addEventListener('click', (e) => {
                const service = toggle.dataset.service;
                this.toggleService(service);
            });
        });

        // Quick actions
        document.getElementById('refresh-all').addEventListener('click', () => this.refreshAllFrames());
        document.getElementById('fullscreen-toggle').addEventListener('click', () => this.toggleDashboardFullscreen());
        document.getElementById('emergency-stop').addEventListener('click', () => this.emergencyStop());

        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const target = e.currentTarget.dataset.target;
                this.switchTab(target);
            });
        });

        // Modal controls
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeModal();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.switchLayout('grid');
                        break;
                    case '2':
                        e.preventDefault();
                        this.switchLayout('tabs');
                        break;
                    case '3':
                        e.preventDefault();
                        this.switchLayout('focus');
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshAllFrames();
                        break;
                    case 'f':
                        e.preventDefault();
                        this.toggleDashboardFullscreen();
                        break;
                }
            }
            if (e.key === 'Escape') {
                this.closeModal();
                this.exitFullscreen();
            }
        });

        // Window resize handler
        window.addEventListener('resize', () => {
            this.adjustLayout();
        });
    }

    switchLayout(layout) {
        this.currentLayout = layout;
        
        // Update button states
        document.querySelectorAll('.layout-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.layout === layout);
        });

        // Show/hide containers
        const gridContainer = document.getElementById('grid-container');
        const tabNav = document.getElementById('tab-nav');
        const focusContainer = document.getElementById('focus-container');

        switch(layout) {
            case 'grid':
                gridContainer.style.display = 'grid';
                tabNav.style.display = 'none';
                focusContainer.style.display = 'none';
                gridContainer.classList.add('active');
                break;
            case 'tabs':
                gridContainer.style.display = 'none';
                tabNav.style.display = 'flex';
                focusContainer.style.display = 'none';
                this.initTabView();
                break;
            case 'focus':
                gridContainer.style.display = 'none';
                tabNav.style.display = 'none';
                focusContainer.style.display = 'block';
                this.initFocusView();
                break;
        }
    }

    initTabView() {
        // Show first active service by default
        const firstActiveTab = document.querySelector('.tab-btn[data-target]');
        if (firstActiveTab) {
            this.switchTab(firstActiveTab.dataset.target);
        }
    }

    switchTab(target) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.target === target);
        });

        // Show corresponding frame content in focus mode
        const iframe = document.getElementById('focus-iframe');
        const serviceKey = target.replace('-frame', '');
        if (this.services[serviceKey]) {
            iframe.src = this.services[serviceKey].url;
        }
        
        document.getElementById('focus-container').style.display = 'block';
    }

    initFocusView() {
        // Focus on first active service
        const firstActive = Object.keys(this.services).find(key => this.services[key].active);
        if (firstActive) {
            const iframe = document.getElementById('focus-iframe');
            iframe.src = this.services[firstActive].url;
            this.focusedService = firstActive;
        }
    }

    toggleService(service) {
        const serviceConfig = this.services[service];
        if (!serviceConfig) return;

        serviceConfig.active = !serviceConfig.active;
        
        // Update toggle visual state
        const toggle = document.querySelector(`[data-service="${service}"] .toggle-switch`);
        toggle.classList.toggle('active', serviceConfig.active);

        // Update frame visibility
        const frame = document.querySelector(`[data-service="${service}"]`);
        if (frame) {
            frame.classList.toggle('hidden', !serviceConfig.active);
        }

        this.adjustLayout();
        this.updateServiceCount();
    }

    adjustLayout() {
        const activeServices = Object.values(this.services).filter(s => s.active).length;
        const gridContainer = document.getElementById('grid-container');
        
        if (activeServices <= 2) {
            gridContainer.classList.add('single-column');
        } else {
            gridContainer.classList.remove('single-column');
        }
    }

    refreshAllFrames() {
        this.showLoadingOverlay();
        
        Object.keys(this.services).forEach(service => {
            const frame = document.getElementById(`${service}-frame`);
            if (frame && this.services[service].active) {
                const currentSrc = frame.src;
                frame.src = '';
                setTimeout(() => {
                    frame.src = currentSrc;
                }, 100);
            }
        });

        setTimeout(() => {
            this.hideLoadingOverlay();
        }, 2000);
    }

    refreshFrame(frameId) {
        const frame = document.getElementById(frameId);
        if (frame) {
            const currentSrc = frame.src;
            frame.src = '';
            setTimeout(() => {
                frame.src = currentSrc;
            }, 100);
        }
    }

    toggleFrameFullscreen(frameId) {
        const frame = document.getElementById(frameId);
        const container = frame.closest('.simulator-frame');
        
        if (container.classList.contains('fullscreen')) {
            container.classList.remove('fullscreen');
        } else {
            container.classList.add('fullscreen');
        }
    }

    openInNewWindow(url) {
        window.open(url, '_blank', 'width=1200,height=800,toolbar=no,menubar=no,scrollbars=yes,resizable=yes');
    }

    toggleDashboardFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            document.documentElement.requestFullscreen();
        }
    }

    emergencyStop() {
        if (confirm('Are you sure you want to perform an emergency stop? This will stop all running services.')) {
            this.showLoadingOverlay();
            
            // Simulate emergency stop
            Object.keys(this.services).forEach(service => {
                this.services[service].active = false;
                const toggle = document.querySelector(`[data-service="${service}"] .toggle-switch`);
                toggle.classList.remove('active');
                
                const frame = document.querySelector(`[data-service="${service}"]`);
                if (frame) {
                    frame.classList.add('hidden');
                }
            });

            this.updateConnectionStatus('disconnected', 'Emergency Stop Active');
            this.updateServiceCount();
            
            setTimeout(() => {
                this.hideLoadingOverlay();
                alert('Emergency stop completed. All services have been stopped.');
            }, 3000);
        }
    }

    checkServiceStatus() {
        // Simulate service health checks
        Object.keys(this.services).forEach(service => {
            const serviceConfig = this.services[service];
            if (serviceConfig.active) {
                // In a real implementation, you would make actual HTTP requests
                // For demo purposes, we'll simulate random connectivity
                const isHealthy = Math.random() > 0.1; // 90% success rate
                
                if (!isHealthy) {
                    this.logger.warn(`Service ${service} appears to be unhealthy`, {
                        url: serviceConfig.url,
                        name: serviceConfig.name,
                        error: 'Simulated error'
                    });
                }
            }
        });

        // Update overall connection status
        const activeServices = Object.values(this.services).filter(s => s.active);
        if (activeServices.length > 0) {
            this.updateConnectionStatus('connected', 'All Services Running');
        } else {
            this.updateConnectionStatus('disconnected', 'No Active Services');
        }
    }

    updateConnectionStatus(status, text) {
        const statusIcon = document.getElementById('status-icon');
        const statusText = document.getElementById('status-text');
        
        statusIcon.className = `fas fa-circle ${status}`;
        statusText.textContent = text;
    }

    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { hour12: false });
        document.getElementById('current-time').textContent = timeString;
        document.getElementById('last-update').textContent = now.toLocaleString();
    }

    updateServiceCount() {
        const activeCount = Object.values(this.services).filter(s => s.active).length;
        document.getElementById('services-count').textContent = activeCount;
    }

    updateSystemInfo() {
        // Simulate system metrics
        const cpuUsage = (Math.random() * 30 + 10).toFixed(1) + '%';
        const memoryUsage = (Math.random() * 40 + 30).toFixed(1) + '%';
        const containerCount = Object.values(this.services).filter(s => s.active).length;

        document.getElementById('cpu-usage').textContent = cpuUsage;
        document.getElementById('memory-usage').textContent = memoryUsage;
        document.getElementById('container-count').textContent = containerCount;
    }

    showLoadingOverlay() {
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoadingOverlay() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showModal(modalId) {
        document.getElementById('modal-overlay').classList.add('show');
        if (modalId) {
            document.getElementById(modalId).style.display = 'block';
        }
    }

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('show');
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }

    exitFullscreen() {
        document.querySelectorAll('.simulator-frame.fullscreen').forEach(frame => {
            frame.classList.remove('fullscreen');
        });
    }
}

// Global functions for iframe controls
function refreshFrame(frameId) {
    dashboard.refreshFrame(frameId);
}

function toggleFrameFullscreen(frameId) {
    dashboard.toggleFrameFullscreen(frameId);
}

function openInNewWindow(url) {
    dashboard.openInNewWindow(url);
}

function showHelp() {
    dashboard.showModal('help-modal');
}

function showLogs() {
    // In a real implementation, this would fetch and display actual logs
    alert('Logs functionality would be implemented here.\n\nThis would typically show:\n- Container logs\n- System events\n- Error messages\n- Performance metrics');
}

function showSettings() {
    // In a real implementation, this would show a settings modal
    alert('Settings functionality would be implemented here.\n\nThis would typically include:\n- Service configuration\n- Display preferences\n- Network settings\n- User preferences');
}

function closeModal() {
    dashboard.closeModal();
}

// Utility function to hide loading overlay
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        if (window.Logger) {
            window.Logger.debug('Loading overlay hidden manually', {
                overlayElement: overlay.id,
                timestamp: new Date().toISOString()
            });
        }
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    // Initialize global logging for page initialization
    if (window.Logger) {
        window.Logger.pageStart({
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        });
        window.Logger.info('DOM loaded, initializing dashboard', {
            readyState: document.readyState,
            timestamp: new Date().toISOString()
        });
    }
    
    // Always hide loading overlay first
    hideLoadingOverlay();
    
    // Wait for configuration to be available
    const initDashboard = () => {
        if (typeof window.SERVICES_CONFIG !== 'undefined') {
            if (window.Logger) {
                window.Logger.info('Configuration available, creating DashboardController', {
                    configKeys: Object.keys(window.SERVICES_CONFIG || {}),
                    totalServices: Object.keys(window.SERVICES_CONFIG || {}).length
                });
            }
            dashboard = new DashboardController();
        } else {
            if (window.Logger) {
                window.Logger.debug('Configuration not yet available, retrying in 100ms', {
                    attempt: Date.now(),
                    availableGlobals: Object.keys(window).filter(key => key.includes('CONFIG'))
                });
            }
            setTimeout(initDashboard, 100);
        }
    };
    
    // Start initialization
    initDashboard();
    
    // Add some initial loading delay for dramatic effect
    setTimeout(() => {
        dashboard.updateConnectionStatus('connected', 'All Services Running');
    }, 2000);
});

// Handle iframe load errors
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('iframe').forEach(iframe => {
        iframe.addEventListener('error', (e) => {
            console.warn(`Failed to load iframe: ${iframe.src}`);
            const container = iframe.closest('.simulator-frame');
            const header = container.querySelector('.frame-header h3');
            header.innerHTML = header.innerHTML + ' <span style="color: #ff4444;">(Offline)</span>';
        });
        
        iframe.addEventListener('load', (e) => {
            console.log(`Successfully loaded iframe: ${iframe.src}`);
        });
    });
});
