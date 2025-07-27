/**
 * Standardized Logging System for C20 Hardware Simulator
 * Provides structured logging with different levels and formatting
 */

class Logger {
    constructor(name = 'C20Simulator') {
        this.name = name;
        this.levels = {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3
        };
        
        // Set default log level from environment or default to DEBUG for enhanced logging
        this.currentLevel = this.levels.DEBUG;
        
        // Try to get log level from config or URL params
        this.initializeLogLevel();
        
        // Initialize enhanced log storage
        this.logs = [];
        this.maxStoredLogs = 2000; // Increased capacity
        this.sessionId = this.generateSessionId();
        this.persistentStorageKey = 'c20_simulator_logs';
        
        // Performance and monitoring
        this.timers = new Map();
        this.networkRequests = [];
        this.performanceMetrics = [];
        
        // Auto-save configuration
        this.autoSaveEnabled = true;
        this.autoSaveInterval = 30000; // 30 seconds
        this.logRotationSize = 5000;
        
        // Initialize persistent storage and monitoring
        this.initializePersistentStorage();
        this.setupNetworkMonitoring();
        this.setupPerformanceMonitoring();
        this.startAutoSave();
        
        this.info('Enhanced Logger initialized', { 
            name: this.name,
            sessionId: this.sessionId,
            persistentStorage: this.autoSaveEnabled, 
            level: this.getLevelName(this.currentLevel),
            timestamp: new Date().toISOString()
        });
    }
    
    initializeLogLevel() {
        try {
            // Check URL parameters for log level
            const urlParams = new URLSearchParams(window.location.search);
            const logLevel = urlParams.get('logLevel') || urlParams.get('debug');
            
            if (logLevel) {
                this.setLevel(logLevel.toUpperCase());
                return;
            }
            
            // Check if config exists and has debug mode
            if (typeof window.CONFIG !== 'undefined' && window.CONFIG.env) {
                const debugMode = window.CONFIG.env.DEBUG_MODE || window.CONFIG.env.NODE_ENV;
                if (debugMode === 'development' || debugMode === 'debug') {
                    this.setLevel('DEBUG');
                    return;
                }
            }
            
            // Default to INFO level
            this.setLevel('INFO');
        } catch (error) {
            console.warn('Failed to initialize log level:', error);
            this.setLevel('INFO');
        }
    }
    
    setLevel(levelName) {
        const level = this.levels[levelName.toUpperCase()];
        if (level !== undefined) {
            this.currentLevel = level;
        }
    }
    
    getLevelName(level) {
        return Object.keys(this.levels).find(key => this.levels[key] === level) || 'UNKNOWN';
    }
    
    shouldLog(level) {
        return level >= this.currentLevel;
    }
    
    formatMessage(level, message, context = {}) {
        const timestamp = new Date().toISOString();
        const levelName = this.getLevelName(level);
        
        return {
            timestamp,
            level: levelName,
            logger: this.name,
            message,
            context,
            url: window.location.href,
            userAgent: navigator.userAgent.substring(0, 100) // Truncated for brevity
        };
    }
    
    log(level, message, context = {}) {
        if (!this.shouldLog(level)) return;
        
        const logEntry = this.formatMessage(level, message, context);
        
        // Store log entry
        this.logs.push(logEntry);
        if (this.logs.length > this.maxStoredLogs) {
            this.logs.shift(); // Remove oldest log
        }
        
        // Output to console with appropriate method
        const consoleMethod = this.getConsoleMethod(level);
        const consoleMessage = `[${logEntry.timestamp}] [${logEntry.level}] [${this.name}] ${message}`;
        
        if (Object.keys(context).length > 0) {
            consoleMethod(consoleMessage, context);
        } else {
            consoleMethod(consoleMessage);
        }
        
        // Send to external logging service if configured
        this.sendToExternalLogger(logEntry);
    }
    
    getConsoleMethod(level) {
        switch (level) {
            case this.levels.DEBUG:
                return console.debug || console.log;
            case this.levels.INFO:
                return console.info || console.log;
            case this.levels.WARN:
                return console.warn;
            case this.levels.ERROR:
                return console.error;
            default:
                return console.log;
        }
    }
    
    debug(message, context = {}) {
        this.log(this.levels.DEBUG, message, context);
    }
    
    info(message, context = {}) {
        this.log(this.levels.INFO, message, context);
    }
    
    warn(message, context = {}) {
        this.log(this.levels.WARN, message, context);
    }
    
    error(message, context = {}) {
        this.log(this.levels.ERROR, message, context);
    }
    
    // Page lifecycle tracking
    pageStart(context = {}) {
        this.info('Page started', {
            ...context,
            pageStartTime: performance.now(),
            timestamp: new Date().toISOString()
        });
    }
    
    // Component lifecycle tracking
    componentStart(componentName, context = {}) {
        this.info(`Component started: ${componentName}`, {
            component: componentName,
            ...context,
            startTime: performance.now(),
            timestamp: new Date().toISOString()
        });
    }
    
    componentEnd(componentName, context = {}) {
        this.info(`Component ended: ${componentName}`, {
            component: componentName,
            ...context,
            endTime: performance.now(),
            timestamp: new Date().toISOString()
        });
    }

    // Performance and lifecycle tracking
    time(label) {
        this.timers.set(label, performance.now());
        this.debug(`Timer started: ${label}`);
    }
    
    timeEnd(label) {
        const startTime = this.timers.get(label);
        if (startTime !== undefined) {
            const duration = performance.now() - startTime;
            this.timers.delete(label);
            this.info(`Timer ${label}`, { duration: `${duration.toFixed(2)}ms` });
            return duration;
        } else {
            this.warn(`Timer ${label} not found`);
            return null;
        }
    }
    
    // Log service/component lifecycle events
    componentStart(componentName, context = {}) {
        this.info(`Starting component: ${componentName}`, context);
        this.time(`component_${componentName}`);
    }
    
    componentEnd(componentName, context = {}) {
        this.info(`Component ready: ${componentName}`, context);
        this.timeEnd(`component_${componentName}`);
    }
    
    // Log API/service calls
    apiCall(method, url, context = {}) {
        this.debug(`API Call: ${method} ${url}`, context);
    }
    
    apiResponse(method, url, status, duration, context = {}) {
        const logContext = { 
            method, 
            url, 
            status, 
            duration: `${duration}ms`,
            ...context 
        };
        
        if (status >= 200 && status < 300) {
            this.info(`API Success: ${method} ${url}`, logContext);
        } else if (status >= 400) {
            this.warn(`API Error: ${method} ${url}`, logContext);
        } else {
            this.debug(`API Response: ${method} ${url}`, logContext);
        }
    }
    
    // Configuration and environment logging
    logConfig(config) {
        this.info('Configuration loaded', {
            services: Object.keys(config.services || {}).length,
            environment: config.env ? Object.keys(config.env).length : 0,
            network: config.network || 'not configured'
        });
        this.debug('Full configuration', config);
    }
    
    logEnvironment(env) {
        this.info('Environment variables loaded', {
            totalVars: Object.keys(env).length,
            host: env.HOST_DOMAIN || 'localhost',
            mode: env.NODE_ENV || env.DEBUG_MODE || 'production'
        });
        this.debug('Environment details', env);
    }
    
    // Get stored logs for debugging
    getLogs(level = null) {
        if (level === null) {
            return this.logs;
        }
        const levelValue = this.levels[level.toUpperCase()];
        return this.logs.filter(log => this.levels[log.level] >= levelValue);
    }
    
    // Export enhanced logs as JSON for debugging
    exportLogs() {
        const data = {
            sessionId: this.sessionId,
            exportTimestamp: new Date().toISOString(),
            logs: this.logs,
            networkRequests: this.networkRequests || [],
            performanceMetrics: this.performanceMetrics || [],
            systemInfo: {
                userAgent: navigator.userAgent,
                url: window.location.href,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            }
        };
        
        const logsJson = JSON.stringify(data, null, 2);
        const blob = new Blob([logsJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.name.toLowerCase()}_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.info('Enhanced logs exported', { 
            logCount: this.logs.length,
            networkRequests: this.networkRequests ? this.networkRequests.length : 0,
            performanceMetrics: this.performanceMetrics ? this.performanceMetrics.length : 0
        });
    }
    
    // Send logs to external service (can be configured)
    sendToExternalLogger(logEntry) {
        try {
            if (window.CONFIG && window.CONFIG.logging && window.CONFIG.logging.endpoint) {
                // Example: send to logging endpoint
                fetch(window.CONFIG.logging.endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(logEntry)
                }).catch(err => console.warn('Failed to send log to external service:', err));
            }
        } catch (error) {
            // Silently fail to avoid logging loops
        }
    }
    
    // Generate unique session ID
    generateSessionId() {
        return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Initialize persistent storage
    initializePersistentStorage() {
        try {
            const savedLogs = localStorage.getItem(this.persistentStorageKey);
            if (savedLogs) {
                const parsed = JSON.parse(savedLogs);
                if (Array.isArray(parsed.logs)) {
                    this.logs = parsed.logs.slice(-this.maxStoredLogs);
                    this.debug('Loaded logs from persistent storage', {
                        count: this.logs.length,
                        lastSession: parsed.sessionId
                    });
                }
            }
        } catch (error) {
            this.error('Failed to load logs from persistent storage', { error: error.message });
        }
    }
    
    // Setup network monitoring
    setupNetworkMonitoring() {
        const originalFetch = window.fetch;
        const logger = this;
        
        window.fetch = function(...args) {
            const startTime = performance.now();
            const url = args[0];
            const options = args[1] || {};
            
            logger.debug('Network request started', {
                url: typeof url === 'string' ? url : url.url,
                method: options.method || 'GET',
                timestamp: new Date().toISOString()
            });
            
            return originalFetch.apply(this, args)
                .then(response => {
                    const duration = performance.now() - startTime;
                    logger.info('Network request completed', {
                        url: typeof url === 'string' ? url : url.url,
                        method: options.method || 'GET',
                        status: response.status,
                        duration: `${duration.toFixed(2)}ms`,
                        ok: response.ok
                    });
                    
                    if (!logger.networkRequests) logger.networkRequests = [];
                    logger.networkRequests.push({
                        url: typeof url === 'string' ? url : url.url,
                        method: options.method || 'GET',
                        status: response.status,
                        duration,
                        timestamp: new Date().toISOString()
                    });
                    
                    return response;
                })
                .catch(error => {
                    const duration = performance.now() - startTime;
                    logger.error('Network request failed', {
                        url: typeof url === 'string' ? url : url.url,
                        method: options.method || 'GET',
                        error: error.message,
                        duration: `${duration.toFixed(2)}ms`
                    });
                    throw error;
                });
        };
    }
    
    // Setup performance monitoring
    setupPerformanceMonitoring() {
        if (window.PerformanceObserver) {
            const observer = new PerformanceObserver((list) => {
                list.getEntries().forEach(entry => {
                    this.debug('Performance entry', {
                        name: entry.name,
                        type: entry.entryType,
                        duration: entry.duration,
                        startTime: entry.startTime
                    });
                    
                    if (!this.performanceMetrics) this.performanceMetrics = [];
                    this.performanceMetrics.push({
                        name: entry.name,
                        type: entry.entryType,
                        duration: entry.duration,
                        startTime: entry.startTime,
                        timestamp: new Date().toISOString()
                    });
                });
            });
            
            try {
                observer.observe({ entryTypes: ['navigation', 'resource', 'measure', 'mark'] });
                this.debug('Performance monitoring enabled');
            } catch (error) {
                this.warn('Performance monitoring setup failed', { error: error.message });
            }
        }
        
        // Monitor memory usage periodically
        if (window.performance && window.performance.memory) {
            setInterval(() => {
                const memory = window.performance.memory;
                this.debug('Memory usage', {
                    used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`,
                    total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)}MB`,
                    limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)}MB`
                });
            }, 60000); // Every minute
        }
    }
    
    // Start auto-save functionality
    startAutoSave() {
        if (this.autoSaveEnabled) {
            setInterval(() => {
                this.saveToPersistentStorage();
            }, this.autoSaveInterval);
            
            // Save on page unload
            window.addEventListener('beforeunload', () => {
                this.saveToPersistentStorage();
            });
            
            this.debug('Auto-save enabled', {
                interval: `${this.autoSaveInterval / 1000}s`,
                rotationSize: this.logRotationSize
            });
        }
    }
    
    // Save logs to persistent storage
    saveToPersistentStorage() {
        try {
            if (this.logs.length > this.logRotationSize) {
                this.logs = this.logs.slice(-this.maxStoredLogs);
                this.info('Log rotation performed', {
                    newCount: this.logs.length,
                    rotationSize: this.logRotationSize
                });
            }
            
            const data = {
                sessionId: this.sessionId,
                timestamp: new Date().toISOString(),
                logs: this.logs,
                networkRequests: (this.networkRequests || []).slice(-100),
                performanceMetrics: (this.performanceMetrics || []).slice(-50)
            };
            
            localStorage.setItem(this.persistentStorageKey, JSON.stringify(data));
            this.debug('Logs saved to persistent storage', {
                logCount: this.logs.length,
                networkRequests: this.networkRequests ? this.networkRequests.length : 0,
                performanceMetrics: this.performanceMetrics ? this.performanceMetrics.length : 0
            });
        } catch (error) {
            this.error('Failed to save logs to persistent storage', { error: error.message });
        }
    }

    // Clear stored logs
    clearLogs() {
        const count = this.logs.length;
        this.logs = [];
        if (this.networkRequests) this.networkRequests = [];
        if (this.performanceMetrics) this.performanceMetrics = [];
        
        // Clear persistent storage
        try {
            localStorage.removeItem(this.persistentStorageKey);
        } catch (error) {
            this.warn('Failed to clear persistent storage', { error: error.message });
        }
        
        this.info('All logs and metrics cleared', { 
            previousLogCount: count,
            timestamp: new Date().toISOString()
        });
    }
}

// Create global logger instance
window.Logger = new Logger('C20Simulator');

// Create convenient global logging functions
window.log = {
    debug: (message, context) => window.Logger.debug(message, context),
    info: (message, context) => window.Logger.info(message, context),
    warn: (message, context) => window.Logger.warn(message, context),
    error: (message, context) => window.Logger.error(message, context),
    time: (label) => window.Logger.time(label),
    timeEnd: (label) => window.Logger.timeEnd(label),
    exportLogs: () => window.Logger.exportLogs(),
    clearLogs: () => window.Logger.clearLogs(),
    getLogs: (level) => window.Logger.getLogs(level)
};

// Add global error handler
window.addEventListener('error', (event) => {
    window.Logger.error('Global JavaScript error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error ? event.error.stack : 'No stack trace available'
    });
});

// Add unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
    window.Logger.error('Unhandled promise rejection', {
        reason: event.reason,
        promise: event.promise
    });
});

console.log('%c🚀 C20 Hardware Simulator - Enhanced Logging Initialized', 
    'background: #1e3a8a; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;');
console.log('%cAvailable logging functions: log.debug(), log.info(), log.warn(), log.error()', 
    'color: #3b82f6; font-weight: bold;');
console.log('%cDebug functions: log.exportLogs(), log.clearLogs(), log.getLogs()', 
    'color: #059669; font-weight: bold;');
