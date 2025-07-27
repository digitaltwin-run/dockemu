<?php
/**
 * Simplified C20 Dashboard - Unified System Monitoring
 * Port: 8060 (DASHBOARD_PORT)
 */

// Load environment configuration
function loadEnvConfig($envFile = '/var/www/html/.env') {
    $config = [];
    if (file_exists($envFile)) {
        $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            if (strpos(trim($line), '#') === 0) continue;
            if (strpos($line, '=') === false) continue; // Skip lines without =
            list($key, $value) = array_map('trim', explode('=', $line, 2));
            $config[$key] = $value;
        }
    }
    return $config;
}

$config = loadEnvConfig();

class C20Dashboard {
    private $config;
    private $services;
    
    public function __construct($config) {
        $this->config = $config;
        $this->initServices();
    }
    
    private function initServices() {
        $this->services = [
            'dashboard' => [
                'name' => 'Main Dashboard',
                'port' => $this->config['DASHBOARD_PORT'] ?? '8060',
                'status' => 'running',
                'icon' => '🏠'
            ],
            'hmi_monitor' => [
                'name' => 'HMI Monitor',
                'port' => $this->config['HMI_MONITOR_PORT'] ?? '8072',
                'status' => 'unknown',
                'icon' => '🖥️'
            ],
            'rpi3_qemu' => [
                'name' => 'RPI3 QEMU',
                'port' => $this->config['QEMU_API_PORT'] ?? '4001',
                'status' => 'unknown',
                'icon' => '🔌'
            ],
            'mqtt' => [
                'name' => 'MQTT Broker',
                'port' => $this->config['MQTT_PORT'] ?? '1883',
                'status' => 'unknown',
                'icon' => '📡'
            ]
        ];
    }
    
    public function checkServiceStatus($port) {
        // Clean and reliable container-to-container status check
        $container_mappings = [
            '8060' => 'localhost:80',                // Dashboard (same container)
            '8072' => 'c20-hmi-monitor-clean:80',    // HMI Monitor
            '1883' => 'c20-mqtt-clean:1883',         // MQTT
            '4001' => 'c20-rpi-qemu-clean:4000',     // RPI3 API
            '2222' => 'c20-rpi-qemu-clean:2222',     // SSH
            '5901' => 'c20-rpi-qemu-clean:5901'      // VNC
        ];
        
        if (isset($container_mappings[$port])) {
            $target = $container_mappings[$port];
            list($host, $target_port) = explode(':', $target);
            
            // Use reliable fsockopen with proper timeout
            $connection = @fsockopen($host, (int)$target_port, $errno, $errstr, 3);
            if ($connection) {
                fclose($connection);
                return 'online';
            }
            return 'offline';
        }
        
        // Fallback for unmapped ports
        $connection = @fsockopen('localhost', $port, $errno, $errstr, 2);
        if ($connection) {
            fclose($connection);
            return 'online';
        }
        return 'offline';
    }
    
    public function getRPI3Status() {
        $qemu_port = $this->config['QEMU_API_PORT'] ?? '4001';
        $vnc_port = $this->config['QEMU_VNC_PORT'] ?? '5901';
        $ssh_port = $this->config['QEMU_SSH_PORT'] ?? '2222';
        
        return [
            'qemu_api' => $this->checkServiceStatus($qemu_port),
            'vnc' => $this->checkServiceStatus($vnc_port),
            'ssh' => $this->checkServiceStatus($ssh_port),
            'ports' => [
                'api' => $qemu_port,
                'vnc' => $vnc_port,
                'ssh' => $ssh_port
            ]
        ];
    }
    
    public function getSystemStatus() {
        foreach ($this->services as $key => &$service) {
            $service['status'] = $this->checkServiceStatus($service['port']);
        }
        
        return [
            'services' => $this->services,
            'rpi3' => $this->getRPI3Status(),
            'environment_vars' => count($this->config),
            'timestamp' => date('Y-m-d H:i:s')
        ];
    }
    
    public function renderDashboard() {
        $status = $this->getSystemStatus();
        ?>
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>C20 System Dashboard</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                    color: #fff;
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                
                .header h1 {
                    font-size: 2.5em;
                    color: #00ff00;
                    margin-bottom: 10px;
                    text-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
                }
                
                .header .subtitle {
                    font-size: 1.2em;
                    color: #ccc;
                    margin-bottom: 20px;
                }
                
                .status-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }
                
                .service-card {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 25px;
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    transition: all 0.3s ease;
                }
                
                .service-card:hover {
                    border-color: #00ccff;
                    box-shadow: 0 0 20px rgba(0, 204, 255, 0.3);
                }
                
                .service-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .service-name {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 1.2em;
                    font-weight: bold;
                }
                
                .service-icon {
                    font-size: 1.5em;
                }
                
                .status-indicator {
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: bold;
                    text-transform: uppercase;
                }
                
                .status-online {
                    background: rgba(0, 255, 0, 0.2);
                    color: #00ff00;
                    border: 1px solid #00ff00;
                }
                
                .status-offline {
                    background: rgba(255, 0, 0, 0.2);
                    color: #ff6666;
                    border: 1px solid #ff6666;
                }
                
                .service-details {
                    color: #ccc;
                    line-height: 1.6;
                }
                
                .port-info {
                    font-family: 'Courier New', monospace;
                    background: rgba(0, 0, 0, 0.3);
                    padding: 8px;
                    border-radius: 5px;
                    margin-top: 10px;
                }
                
                .rpi3-section {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 30px;
                    border: 2px solid rgba(0, 255, 0, 0.3);
                }
                
                .rpi3-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }
                
                .rpi3-title {
                    font-size: 1.5em;
                    color: #00ff00;
                }
                
                .rpi3-connections {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }
                
                .connection-item {
                    background: rgba(0, 0, 0, 0.3);
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }
                
                .connection-type {
                    font-weight: bold;
                    color: #00ccff;
                    margin-bottom: 8px;
                }
                
                .connection-url {
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                    color: #ffff00;
                    word-break: break-all;
                }
                
                .quick-actions {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                    justify-content: center;
                    margin-top: 30px;
                }
                
                .action-btn {
                    background: linear-gradient(45deg, #007acc, #0099ff);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 1em;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-block;
                }
                
                .action-btn:hover {
                    background: linear-gradient(45deg, #005a99, #0077cc);
                    box-shadow: 0 0 15px rgba(0, 153, 255, 0.5);
                }
                
                .environment-info {
                    background: rgba(0, 0, 0, 0.2);
                    border-radius: 10px;
                    padding: 20px;
                    margin-top: 20px;
                    text-align: center;
                }
                
                .auto-refresh {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: rgba(0, 0, 0, 0.7);
                    padding: 10px 15px;
                    border-radius: 8px;
                    font-size: 0.9em;
                }
                
                .refresh-indicator {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    background: #00ff00;
                    border-radius: 50%;
                    margin-right: 8px;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.3; }
                }
            </style>
        </head>
        <body>
            <div class="auto-refresh">
                <span class="refresh-indicator"></span>
                Auto-refresh: 10s
            </div>
            
            <div class="container">
                <div class="header">
                    <h1>🏭 C20 Digital Twin System</h1>
                    <div class="subtitle">Unified Hardware Simulator Dashboard</div>
                    <div>Last updated: <?php echo $status['timestamp']; ?></div>
                </div>
                
                <!-- RPI3 Status Section -->
                <div class="rpi3-section">
                    <div class="rpi3-header">
                        <div class="rpi3-title">🔌 Raspberry Pi 3 System Status</div>
                        <div class="status-indicator <?php echo $status['rpi3']['qemu_api'] === 'online' ? 'status-online' : 'status-offline'; ?>">
                            <?php echo $status['rpi3']['qemu_api'] === 'online' ? 'Running' : 'Stopped'; ?>
                        </div>
                    </div>
                    
                    <div class="rpi3-connections">
                        <div class="connection-item">
                            <div class="connection-type">SSH Access</div>
                            <div class="connection-url">ssh pi@localhost -p <?php echo $status['rpi3']['ports']['ssh']; ?></div>
                            <div style="margin-top: 5px; color: <?php echo $status['rpi3']['ssh'] === 'online' ? '#00ff00' : '#ff6666'; ?>;">
                                <?php echo $status['rpi3']['ssh'] === 'online' ? '✅ Available' : '❌ Offline'; ?>
                            </div>
                        </div>
                        
                        <div class="connection-item">
                            <div class="connection-type">VNC Display</div>
                            <div class="connection-url">localhost:<?php echo $status['rpi3']['ports']['vnc']; ?></div>
                            <div style="margin-top: 5px; color: <?php echo $status['rpi3']['vnc'] === 'online' ? '#00ff00' : '#ff6666'; ?>;">
                                <?php echo $status['rpi3']['vnc'] === 'online' ? '✅ Available' : '❌ Offline'; ?>
                            </div>
                        </div>
                        
                        <div class="connection-item">
                            <div class="connection-type">API Endpoint</div>
                            <div class="connection-url">http://localhost:<?php echo $status['rpi3']['ports']['api']; ?></div>
                            <div style="margin-top: 5px; color: <?php echo $status['rpi3']['qemu_api'] === 'online' ? '#00ff00' : '#ff6666'; ?>;">
                                <?php echo $status['rpi3']['qemu_api'] === 'online' ? '✅ Running' : '❌ Stopped'; ?>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Services Status Grid -->
                <div class="status-grid">
                    <?php foreach ($status['services'] as $service): ?>
                        <div class="service-card">
                            <div class="service-header">
                                <div class="service-name">
                                    <span class="service-icon"><?php echo $service['icon']; ?></span>
                                    <?php echo $service['name']; ?>
                                </div>
                                <div class="status-indicator <?php echo $service['status'] === 'online' ? 'status-online' : 'status-offline'; ?>">
                                    <?php echo $service['status']; ?>
                                </div>
                            </div>
                            <div class="service-details">
                                <div class="port-info">
                                    Port: <?php echo $service['port']; ?><br>
                                    URL: <a href="http://localhost:<?php echo $service['port']; ?>" target="_blank" style="color: #00ccff;">
                                        http://localhost:<?php echo $service['port']; ?>
                                    </a>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
                
                <!-- Quick Actions -->
                <div class="quick-actions">
                    <a href="http://localhost:<?php echo $this->config['HMI_MONITOR_PORT'] ?? '8072'; ?>" 
                       class="action-btn" target="_blank">
                        🖥️ Open HMI Monitor
                    </a>
                    <button class="action-btn" onclick="refreshStatus()">
                        🔄 Refresh Status
                    </button>
                    <button class="action-btn" onclick="showDiagnostics()">
                        🔧 System Diagnostics
                    </button>
                    <button class="action-btn" onclick="exportConfig()">
                        💾 Export Configuration
                    </button>
                </div>
                
                <!-- Environment Info -->
                <div class="environment-info">
                    <h3>📋 System Information</h3>
                    <p>Environment Variables: <?php echo $status['environment_vars']; ?></p>
                    <p>Active Services: <?php echo count(array_filter($status['services'], function($s) { return $s['status'] === 'online'; })); ?>/<?php echo count($status['services']); ?></p>
                    <p>Dashboard Port: <?php echo $this->config['DASHBOARD_PORT'] ?? '8060'; ?></p>
                </div>
            </div>
            
            <script>
                // Auto-refresh every 10 seconds
                setInterval(function() {
                    if (document.visibilityState === 'visible') {
                        refreshStatus();
                    }
                }, 10000);
                
                function refreshStatus() {
                    location.reload();
                }
                
                function showDiagnostics() {
                    const diagnosticsWindow = window.open('', '_blank', 'width=800,height=600');
                    diagnosticsWindow.document.write(`
                        <html>
                        <head><title>System Diagnostics</title></head>
                        <body style="font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px;">
                            <h2>🔧 C20 System Diagnostics</h2>
                            <pre id="diagnostics-output">Loading...</pre>
                        </body>
                        </html>
                    `);
                    
                    // Simulate diagnostic output
                    setTimeout(() => {
                        const output = `=== C20 System Status ===
Services Running: ${<?php echo count(array_filter($status['services'], function($s) { return $s['status'] === 'online'; })); ?>}
RPI3 QEMU: <?php echo $status['rpi3']['qemu_api'] === 'online' ? 'RUNNING' : 'STOPPED'; ?>
VNC Server: <?php echo $status['rpi3']['vnc'] === 'online' ? 'ACTIVE' : 'INACTIVE'; ?>
SSH Server: <?php echo $status['rpi3']['ssh'] === 'online' ? 'ACTIVE' : 'INACTIVE'; ?>

=== Port Status ===
<?php foreach ($status['services'] as $service): ?>
Port <?php echo $service['port']; ?> (<?php echo $service['name']; ?>): <?php echo strtoupper($service['status']); ?>
<?php endforeach; ?>

=== Environment ===
Total Variables: <?php echo $status['environment_vars']; ?>
Dashboard Port: <?php echo $this->config['DASHBOARD_PORT'] ?? '8060'; ?>
Last Check: <?php echo $status['timestamp']; ?>`;
                        
                        diagnosticsWindow.document.getElementById('diagnostics-output').textContent = output;
                    }, 1000);
                }
                
                function exportConfig() {
                    const config = {
                        timestamp: '<?php echo $status['timestamp']; ?>',
                        services: <?php echo json_encode($status['services']); ?>,
                        rpi3_status: <?php echo json_encode($status['rpi3']); ?>,
                        environment_vars: <?php echo $status['environment_vars']; ?>
                    };
                    
                    const dataStr = JSON.stringify(config, null, 2);
                    const dataBlob = new Blob([dataStr], {type: 'application/json'});
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = 'c20-config-export.json';
                    link.click();
                    URL.revokeObjectURL(url);
                }
            </script>
        </body>
        </html>
        <?php
    }
}

// Handle AJAX requests for status updates
if (isset($_GET['ajax']) && $_GET['ajax'] === 'status') {
    header('Content-Type: application/json');
    $dashboard = new C20Dashboard($config);
    echo json_encode($dashboard->getSystemStatus());
    exit;
}

// Render main dashboard
$dashboard = new C20Dashboard($config);
$dashboard->renderDashboard();
?>
