<?php
/**
 * Config Generator - Reads .env file and generates JavaScript configuration
 * This script parses the .env file and creates a JS file with all environment variables
 */

class ConfigGenerator {
    private $envPath;
    private $outputPath;
    private $configData;
    
    public function __construct($envPath = '../.env', $outputPath = './js/config.js') {
        $this->envPath = $envPath;
        $this->outputPath = $outputPath;
        $this->configData = [];
    }
    
    /**
     * Parse .env file and extract key-value pairs
     */
    public function parseEnvFile() {
        if (!file_exists($this->envPath)) {
            throw new Exception("Environment file not found: " . $this->envPath);
        }
        
        $lines = file($this->envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        
        foreach ($lines as $line) {
            // Skip comments and empty lines
            if (strpos(trim($line), '#') === 0 || empty(trim($line))) {
                continue;
            }
            
            // Parse KEY=VALUE format
            if (strpos($line, '=') !== false) {
                list($key, $value) = explode('=', $line, 2);
                $key = trim($key);
                $value = trim($value);
                
                // Remove quotes if present
                $value = trim($value, '"\'');
                
                $this->configData[$key] = $value;
            }
        }
        
        return $this;
    }
    
    /**
     * Build service configuration based on .env variables
     */
    public function buildServiceConfig() {
        $hostDomain = $this->configData['HOST_DOMAIN'] ?? 'localhost';
        
        $services = [
            'lcd_display' => [
                'name' => 'LCD Display',
                'url' => "http://{$hostDomain}:" . ($this->configData['LCD_DISPLAY_PORT'] ?? '8089'),
                'icon' => 'fas fa-desktop',
                'description' => '7.9" HDMI Display Simulator'
            ],
            'hui_keyboard' => [
                'name' => 'HUI Keyboard Panel',
                'url' => "http://{$hostDomain}:" . ($this->configData['HUI_KEYBOARD_PORT'] ?? '8087'),
                'icon' => 'fas fa-keyboard',
                'description' => 'Interactive Keyboard Interface'
            ],
            'modbus_visualizer' => [
                'name' => 'Modbus I/O Visualizer',
                'url' => "http://{$hostDomain}:" . ($this->configData['MODBUS_VISUALIZER_PORT'] ?? '8084'),
                'icon' => 'fas fa-network-wired',
                'description' => 'Real-time Modbus Data Visualization'
            ],
            'modbus_io_api' => [
                'name' => 'Modbus IO API',
                'url' => "http://{$hostDomain}:" . ($this->configData['MODBUS_IO_API_PORT'] ?? '8085'),
                'icon' => 'fas fa-api',
                'description' => 'Modbus RTU IO 8CH API'
            ],
            'rpi_api' => [
                'name' => 'RPi Emulator API',
                'url' => "http://{$hostDomain}:" . ($this->configData['RPI_API_PORT'] ?? '4000'),
                'icon' => 'fas fa-microchip',
                'description' => 'Raspberry Pi Hardware Emulator'
            ],
            'hmi_pad' => [
                'name' => 'HMI Virtual Touchpad',
                'url' => "http://{$hostDomain}:" . ($this->configData['HMI_PAD_PORT'] ?? '8070'),
                'icon' => 'fas fa-hand-pointer',
                'description' => 'Virtual Touchpad Interface for RPi Control'
            ],
            'hmi_keyboard' => [
                'name' => 'HMI Virtual Keyboard',
                'url' => "http://{$hostDomain}:" . ($this->configData['HMI_KEYBOARD_PORT'] ?? '8071'),
                'icon' => 'fas fa-keyboard',
                'description' => 'Virtual Keyboard Interface for RPi Input'
            ],
            'hmi_monitor' => [
                'name' => 'HMI Monitor',
                'url' => "http://{$hostDomain}:" . ($this->configData['HMI_MONITOR_PORT'] ?? '8072'),
                'icon' => 'fas fa-desktop',
                'description' => 'HMI Monitor Interface'
            ],
            'hmi_numpad' => [
                'name' => 'HMI Virtual Numpad',
                'url' => "http://{$hostDomain}:" . ($this->configData['HMI_NUMPAD_PORT'] ?? '8073'),
                'icon' => 'fas fa-calculator',
                'description' => 'Virtual Numpad Interface'
            ]
        ];
        
        return $services;
    }
    
    /**
     * Generate JavaScript configuration file
     */
    public function generateJSConfig() {
        $services = $this->buildServiceConfig();
        
        $jsConfig = [
            'app' => [
                'name' => 'C20 Hardware Simulator',
                'version' => '1.0',
                'title' => 'C20 Digital Twin Dashboard'
            ],
            'env' => $this->configData,
            'services' => $services,
            'network' => [
                'host' => $this->configData['HOST_DOMAIN'] ?? 'localhost',
                'apiHost' => $this->configData['API_HOST'] ?? 'localhost',
                'mqttHost' => $this->configData['MQTT_HOST'] ?? 'localhost',
                'wsHost' => $this->configData['WS_HOST'] ?? 'localhost',
                'mqttPort' => $this->configData['MQTT_PORT'] ?? '1883',
                'mqttWebSocketPort' => $this->configData['MQTT_WEBSOCKET_PORT'] ?? '9001'
            ],
            'ports' => [
                'frontend' => $this->configData['FRONTEND_PORT'] ?? '8088',
                'lcdDisplay' => $this->configData['LCD_DISPLAY_PORT'] ?? '8089',
                'huiKeyboard' => $this->configData['HUI_KEYBOARD_PORT'] ?? '8087',
                'modbusTcp' => $this->configData['MODBUS_IO_TCP_PORT'] ?? '5020',
                'modbusApi' => $this->configData['MODBUS_IO_API_PORT'] ?? '8085',
                'rpiApi' => $this->configData['RPI_API_PORT'] ?? '4000',
                'rpiVnc' => $this->configData['RPI_VNC_PORT'] ?? '5901'
            ]
        ];
        
        // Create js directory if it doesn't exist
        $jsDir = dirname($this->outputPath);
        if (!is_dir($jsDir)) {
            mkdir($jsDir, 0755, true);
        }
        
        // Generate JavaScript file content
        $jsContent = "// Auto-generated configuration from .env file\n";
        $jsContent .= "// Generated on: " . date('Y-m-d H:i:s') . "\n\n";
        $jsContent .= "window.CONFIG = " . json_encode($jsConfig, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . ";\n\n";
        $jsContent .= "// Convenient access to configuration sections\n";
        $jsContent .= "window.APP_CONFIG = window.CONFIG.app;\n";
        $jsContent .= "window.ENV_CONFIG = window.CONFIG.env;\n";
        $jsContent .= "window.SERVICES_CONFIG = window.CONFIG.services;\n";
        $jsContent .= "window.NETWORK_CONFIG = window.CONFIG.network;\n";
        $jsContent .= "window.PORTS_CONFIG = window.CONFIG.ports;\n\n";
        $jsContent .= "console.log('Configuration loaded:', window.CONFIG);\n";
        
        // Write to file
        if (file_put_contents($this->outputPath, $jsContent) === false) {
            throw new Exception("Failed to write configuration file: " . $this->outputPath);
        }
        
        return $this;
    }
    
    /**
     * Main execution method
     */
    public function generate() {
        try {
            $this->parseEnvFile()
                 ->generateJSConfig();
            
            echo "Configuration generated successfully!\n";
            echo "Generated file: {$this->outputPath}\n";
            echo "Total environment variables: " . count($this->configData) . "\n";
            
            return true;
        } catch (Exception $e) {
            echo "Error: " . $e->getMessage() . "\n";
            return false;
        }
    }
}

// Run the generator if called directly
if (basename($_SERVER['PHP_SELF']) === 'generate-config.php') {
    $generator = new ConfigGenerator();
    $success = $generator->generate();
    exit($success ? 0 : 1);
}
?>
