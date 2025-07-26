/**
 * Configuration management for C20 Dashboard
 * Loads configuration from config.json and environment variables
 */

class ConfigManager {
    constructor() {
        this.config = null;
        this.loaded = false;
    }

    /**
     * Load configuration from config.json
     */
    async loadConfig() {
        try {
            const response = await fetch('./config.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.config = await response.json();
            this.loaded = true;
            console.log('Configuration loaded successfully:', this.config);
            return this.config;
        } catch (error) {
            console.error('Failed to load configuration:', error);
            // Fallback to default configuration
            this.config = this.getDefaultConfig();
            this.loaded = true;
            return this.config;
        }
    }

    /**
     * Get default configuration as fallback
     */
    getDefaultConfig() {
        return {
            app: {
                name: "C20 Hardware Simulator",
                version: "1.0",
                title: "C20 Digital Twin Dashboard"
            },
            services: {
                lcd_display: {
                    name: "LCD Display",
                    url: "http://localhost:8089",
                    icon: "fas fa-desktop"
                },
                hui_keyboard: {
                    name: "HUI Keyboard Panel", 
                    url: "http://localhost:8087",
                    icon: "fas fa-keyboard"
                },
                modbus_visualizer: {
                    name: "Modbus I/O Visualizer",
                    url: "http://localhost:8084", 
                    icon: "fas fa-network-wired"
                }
            },
            ui: {
                refresh_interval: 5000,
                enable_debug: false,
                theme: "default"
            }
        };
    }

    /**
     * Get service URL by service key
     */
    getServiceUrl(serviceKey) {
        if (!this.loaded || !this.config) {
            console.warn('Configuration not loaded, using fallback');
            return this.getDefaultConfig().services[serviceKey]?.url || '#';
        }
        return this.config.services[serviceKey]?.url || '#';
    }

    /**
     * Get service configuration by key
     */
    getService(serviceKey) {
        if (!this.loaded || !this.config) {
            return this.getDefaultConfig().services[serviceKey] || {};
        }
        return this.config.services[serviceKey] || {};
    }

    /**
     * Get app configuration
     */
    getApp() {
        if (!this.loaded || !this.config) {
            return this.getDefaultConfig().app;
        }
        return this.config.app;
    }

    /**
     * Get UI configuration
     */
    getUI() {
        if (!this.loaded || !this.config) {
            return this.getDefaultConfig().ui;
        }
        return this.config.ui;
    }

    /**
     * Update service URLs in DOM elements
     */
    updateServiceUrls() {
        if (!this.loaded) {
            console.warn('Configuration not loaded yet');
            return;
        }

        // Update iframe sources and buttons based on data-service attributes
        const elementsWithService = document.querySelectorAll('[data-service]');
        elementsWithService.forEach(element => {
            const serviceKey = element.getAttribute('data-service');
            const service = this.getService(serviceKey);
            
            if (service.url) {
                // Update iframe src
                if (element.tagName === 'IFRAME') {
                    element.src = service.url;
                }
                
                // Update button onclick for "New Window" buttons
                if (element.tagName === 'BUTTON' && element.getAttribute('onclick')) {
                    const currentOnclick = element.getAttribute('onclick');
                    const placeholder = `#${serviceKey.replace('_', '-')}-url`;
                    const newOnclick = currentOnclick.replace(placeholder, service.url);
                    element.setAttribute('onclick', newOnclick);
                }
            }
        });
        
        // Also update any remaining placeholder URLs in src attributes
        const iframes = document.querySelectorAll('iframe[src*="#"]');
        iframes.forEach(iframe => {
            const serviceKey = iframe.getAttribute('data-service');
            if (serviceKey) {
                const service = this.getService(serviceKey);
                if (service.url) {
                    iframe.src = service.url;
                }
            }
        });

        // Update app title
        const app = this.getApp();
        if (app.title) {
            document.title = app.title;
            const titleElement = document.querySelector('h1');
            if (titleElement) {
                titleElement.textContent = app.title;
            }
        }

        console.log('Service URLs updated from configuration');
    }

    /**
     * Initialize configuration and update DOM
     */
    async init() {
        await this.loadConfig();
        this.updateServiceUrls();
        
        // Set up periodic refresh if configured
        const ui = this.getUI();
        if (ui.refresh_interval && ui.refresh_interval > 0) {
            setInterval(() => {
                this.refreshFrames();
            }, ui.refresh_interval);
        }
    }

    /**
     * Refresh all iframe frames
     */
    refreshFrames() {
        const iframes = document.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            if (iframe.src && iframe.src !== 'about:blank') {
                iframe.src = iframe.src;
            }
        });
    }
}

// Global configuration manager instance
window.configManager = new ConfigManager();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.configManager.init();
});

// Helper functions for compatibility
function getServiceUrl(serviceKey) {
    return window.configManager.getServiceUrl(serviceKey);
}

function refreshAllFrames() {
    window.configManager.refreshFrames();
}
