/**
 * Configuration management for Modbus Visualizer
 * Loads configuration from config.json and environment variables
 */

class ModbusVisualizerConfig {
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
            console.log('Modbus Visualizer configuration loaded successfully:', this.config);
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
                name: "Modbus RTU IO 8CH Monitor",
                version: "1.0",
                title: "Modbus RTU IO 8CH - Real-time Monitor"
            },
            api: {
                modbus_url: "http://localhost:8020/api",
                timeout: 5000,
                retry_attempts: 3,
                retry_delay: 1000
            },
            ui: {
                update_interval: 1000,
                history_length: 100,
                enable_debug: false,
                theme: "dark",
                auto_refresh: true
            },
            modbus: {
                default_config: {
                    baudrate: 9600,
                    parity: "N",
                    stopbits: 1,
                    databits: 8,
                    device: "/dev/ttyUSB0"
                }
            }
        };
    }

    /**
     * Get API configuration
     */
    getAPI() {
        if (!this.loaded || !this.config) {
            return this.getDefaultConfig().api;
        }
        return this.config.api;
    }

    /**
     * Get API URL
     */
    getAPIUrl() {
        const api = this.getAPI();
        return api.modbus_url;
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
     * Get app configuration
     */
    getApp() {
        if (!this.loaded || !this.config) {
            return this.getDefaultConfig().app;
        }
        return this.config.app;
    }

    /**
     * Get Modbus configuration
     */
    getModbus() {
        if (!this.loaded || !this.config) {
            return this.getDefaultConfig().modbus;
        }
        return this.config.modbus;
    }

    /**
     * Update page title and other DOM elements with configuration
     */
    updateDOMElements() {
        if (!this.loaded) {
            console.warn('Configuration not loaded yet');
            return;
        }

        const app = this.getApp();
        if (app.title) {
            document.title = app.title;
        }

        // Update any elements with config data attributes
        const configElements = document.querySelectorAll('[data-config]');
        configElements.forEach(element => {
            const configPath = element.getAttribute('data-config');
            const value = this.getConfigValue(configPath);
            if (value !== undefined) {
                if (element.tagName === 'INPUT') {
                    element.value = value;
                } else {
                    element.textContent = value;
                }
            }
        });

        console.log('DOM elements updated from configuration');
    }

    /**
     * Get configuration value by dot notation path
     */
    getConfigValue(path) {
        if (!this.config) return undefined;
        
        return path.split('.').reduce((obj, key) => {
            return obj && obj[key] !== undefined ? obj[key] : undefined;
        }, this.config);
    }

    /**
     * Initialize configuration and update DOM
     */
    async init() {
        await this.loadConfig();
        this.updateDOMElements();
        
        // Set up periodic refresh if configured
        const ui = this.getUI();
        if (ui.auto_refresh && ui.update_interval > 0) {
            console.log(`Auto-refresh enabled with interval: ${ui.update_interval}ms`);
        }
    }
}

// Global configuration manager instance
window.modbusConfig = new ModbusVisualizerConfig();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.modbusConfig.init();
});

// Helper functions for compatibility with existing code
function getAPIUrl() {
    return window.modbusConfig.getAPIUrl();
}

function getUpdateInterval() {
    return window.modbusConfig.getUI().update_interval;
}

function getHistoryLength() {
    return window.modbusConfig.getUI().history_length;
}
