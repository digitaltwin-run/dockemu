<?php
// Generate configuration before loading the page
require_once 'generate-config.php';
$generator = new ConfigGenerator();
$generator->generate();

// Parse environment variables for server-side use
$envVars = [];
if (file_exists('../.env')) {
    $lines = file('../.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0 || empty(trim($line))) continue;
        if (strpos($line, '=') !== false) {
            list($key, $value) = explode('=', $line, 2);
            $envVars[trim($key)] = trim($value, '"\'');
        }
    }
}

// Helper function to get environment variable with default
function env($key, $default = '') {
    global $envVars;
    return isset($envVars[$key]) ? $envVars[$key] : $default;
}

$hostDomain = env('HOST_DOMAIN', 'localhost');
$frontendPort = env('FRONTEND_PORT', '8088');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo env('COMPOSE_PROJECT_NAME', 'C20 Hardware Simulator'); ?> - Unified Dashboard</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <!-- Load standardized logging system -->
    <script src="js/logger.js"></script>
    
    <!-- Load generated configuration -->
    <script src="js/config.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <header class="dashboard-header">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-microchip"></i>
                    <h1>C20 Hardware Simulator</h1>
                </div>
                <div class="status-indicators">
                    <div class="status-item" id="connection-status">
                        <i class="fas fa-circle" id="status-icon"></i>
                        <span id="status-text">Connecting...</span>
                    </div>
                    <div class="time-display" id="current-time">
                        --:--:--
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="dashboard-main">
            <!-- Control Panel -->
            <aside class="control-panel">
                <h2><i class="fas fa-sliders-h"></i> Control Panel</h2>
                
                <div class="control-section">
                    <h3>Services</h3>
                    <div class="service-toggles">
                        <div class="service-toggle" data-service="lcd">
                            <i class="fas fa-tv"></i>
                            <span>LCD Display</span>
                            <div class="toggle-switch active" id="toggle-lcd">
                                <div class="toggle-slider"></div>
                            </div>
                        </div>
                        <div class="service-toggle" data-service="keyboard">
                            <i class="fas fa-keyboard"></i>
                            <span>HUI Keyboard</span>
                            <div class="toggle-switch active" id="toggle-keyboard">
                                <div class="toggle-slider"></div>
                            </div>
                        </div>
                        <div class="service-toggle" data-service="modbus">
                            <i class="fas fa-network-wired"></i>
                            <span>Modbus I/O</span>
                            <div class="toggle-switch active" id="toggle-modbus">
                                <div class="toggle-slider"></div>
                            </div>
                        </div>
                        <div class="service-toggle" data-service="hmi-pad">
                            <i class="fas fa-hand-pointer"></i>
                            <span>HMI Touchpad</span>
                            <div class="toggle-switch active" id="toggle-hmi-pad">
                                <div class="toggle-slider"></div>
                            </div>
                        </div>
                        <div class="service-toggle" data-service="hmi-keyboard">
                            <i class="fas fa-keyboard"></i>
                            <span>HMI Keyboard</span>
                            <div class="toggle-switch active" id="toggle-hmi-keyboard">
                                <div class="toggle-slider"></div>
                            </div>
                        </div>
                        <div class="service-toggle" data-service="hmi-numpad">
                            <i class="fas fa-calculator"></i>
                            <span>HMI Numpad</span>
                            <div class="toggle-switch active" id="toggle-hmi-numpad">
                                <div class="toggle-slider"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="control-section">
                    <h3>Layout</h3>
                    <div class="layout-controls">
                        <button class="layout-btn active" data-layout="grid">
                            <i class="fas fa-th"></i> Grid View
                        </button>
                        <button class="layout-btn" data-layout="focus">
                            <i class="fas fa-expand"></i> Focus View
                        </button>
                        <button class="layout-btn" data-layout="tabs">
                            <i class="fas fa-window-restore"></i> Tabbed
                        </button>
                    </div>
                </div>

                <div class="control-section">
                    <h3>Quick Actions</h3>
                    <div class="quick-actions">
                        <button class="action-btn" id="refresh-all">
                            <i class="fas fa-sync-alt"></i> Refresh All
                        </button>
                        <button class="action-btn" id="fullscreen-toggle">
                            <i class="fas fa-expand-arrows-alt"></i> Fullscreen
                        </button>
                        <button class="action-btn emergency" id="emergency-stop">
                            <i class="fas fa-stop"></i> Emergency Stop
                        </button>
                    </div>
                </div>

                <div class="control-section">
                    <h3>System Info</h3>
                    <div class="system-info">
                        <div class="info-item">
                            <span class="info-label">Host:</span>
                            <span class="info-value"><?php echo $hostDomain; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Frontend Port:</span>
                            <span class="info-value"><?php echo $frontendPort; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">CPU:</span>
                            <span class="info-value" id="cpu-usage">--</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Memory:</span>
                            <span class="info-value" id="memory-usage">--</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Uptime:</span>
                            <span class="info-value" id="system-uptime">--</span>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Simulator Views -->
            <section class="simulator-views" id="simulator-container">
                <!-- Tab Navigation -->
                <div class="tab-navigation" id="tab-nav" style="display: none;">
                    <button class="tab-btn active" data-target="lcd-frame">
                        <i class="fas fa-tv"></i> LCD Display
                    </button>
                    <button class="tab-btn" data-target="keyboard-frame">
                        <i class="fas fa-keyboard"></i> HUI Keyboard
                    </button>
                    <button class="tab-btn" data-target="modbus-frame">
                        <i class="fas fa-network-wired"></i> Modbus I/O
                    </button>
                    <button class="tab-btn" data-target="hmi-pad-frame">
                        <i class="fas fa-hand-pointer"></i> HMI Touchpad
                    </button>
                    <button class="tab-btn" data-target="hmi-keyboard-frame">
                        <i class="fas fa-keyboard"></i> HMI Keyboard
                    </button>
                    <button class="tab-btn" data-target="hmi-numpad-frame">
                        <i class="fas fa-calculator"></i> HMI Numpad
                    </button>
                </div>

                <!-- Grid Layout -->
                <div class="grid-layout active" id="grid-container">
                    <div class="simulator-frame" data-service="lcd">
                        <div class="frame-header">
                            <h3><i class="fas fa-tv"></i> LCD Display (7.9" HDMI)</h3>
                            <div class="frame-controls">
                                <button class="frame-btn" title="Refresh" onclick="refreshFrame('lcd-frame')">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="frame-btn" title="Fullscreen" onclick="toggleFrameFullscreen('lcd-frame')">
                                    <i class="fas fa-expand"></i>
                                </button>
                                <button class="frame-btn" title="New Window" onclick="openInNewWindow(SERVICES_CONFIG.lcd_display.url)">
                                    <i class="fas fa-external-link-alt"></i>
                                </button>
                            </div>
                        </div>
                        <div class="frame-content">
                            <iframe id="lcd-frame" src="" frameborder="0"></iframe>
                        </div>
                    </div>

                    <div class="simulator-frame" data-service="keyboard">
                        <div class="frame-header">
                            <h3><i class="fas fa-keyboard"></i> HUI Keyboard Panel</h3>
                            <div class="frame-controls">
                                <button class="frame-btn" title="Refresh" onclick="refreshFrame('keyboard-frame')">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="frame-btn" title="Fullscreen" onclick="toggleFrameFullscreen('keyboard-frame')">
                                    <i class="fas fa-expand"></i>
                                </button>
                                <button class="frame-btn" title="New Window" onclick="openInNewWindow(SERVICES_CONFIG.hui_keyboard.url)">
                                    <i class="fas fa-external-link-alt"></i>
                                </button>
                            </div>
                        </div>
                        <div class="frame-content">
                            <iframe id="keyboard-frame" src="" frameborder="0"></iframe>
                        </div>
                    </div>

                    <div class="simulator-frame" data-service="modbus">
                        <div class="frame-header">
                            <h3><i class="fas fa-network-wired"></i> Modbus I/O Visualizer</h3>
                            <div class="frame-controls">
                                <button class="frame-btn" title="Refresh" onclick="refreshFrame('modbus-frame')">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="frame-btn" title="Fullscreen" onclick="toggleFrameFullscreen('modbus-frame')">
                                    <i class="fas fa-expand"></i>
                                </button>
                                <button class="frame-btn" title="New Window" onclick="openInNewWindow(SERVICES_CONFIG.modbus_visualizer.url)">
                                    <i class="fas fa-external-link-alt"></i>
                                </button>
                            </div>
                        </div>
                        <div class="frame-content">
                            <iframe id="modbus-frame" src="" frameborder="0"></iframe>
                        </div>
                    </div>

                    <div class="simulator-frame" data-service="hmi-pad">
                        <div class="frame-header">
                            <h3><i class="fas fa-hand-pointer"></i> HMI Virtual Touchpad</h3>
                            <div class="frame-controls">
                                <button class="frame-btn" title="Refresh" onclick="refreshFrame('hmi-pad-frame')">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="frame-btn" title="Fullscreen" onclick="toggleFrameFullscreen('hmi-pad-frame')">
                                    <i class="fas fa-expand"></i>
                                </button>
                                <button class="frame-btn" title="New Window" onclick="openInNewWindow(SERVICES_CONFIG.hmi_pad.url)">
                                    <i class="fas fa-external-link-alt"></i>
                                </button>
                            </div>
                        </div>
                        <div class="frame-content">
                            <iframe id="hmi-pad-frame" src="" frameborder="0"></iframe>
                        </div>
                    </div>

                    <div class="simulator-frame" data-service="hmi-keyboard">
                        <div class="frame-header">
                            <h3><i class="fas fa-keyboard"></i> HMI Virtual Keyboard</h3>
                            <div class="frame-controls">
                                <button class="frame-btn" title="Refresh" onclick="refreshFrame('hmi-keyboard-frame')">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="frame-btn" title="Fullscreen" onclick="toggleFrameFullscreen('hmi-keyboard-frame')">
                                    <i class="fas fa-expand"></i>
                                </button>
                                <button class="frame-btn" title="New Window" onclick="openInNewWindow(SERVICES_CONFIG.hmi_keyboard.url)">
                                    <i class="fas fa-external-link-alt"></i>
                                </button>
                            </div>
                        </div>
                        <div class="frame-content">
                            <iframe id="hmi-keyboard-frame" src="" frameborder="0"></iframe>
                        </div>
                    </div>

                    <div class="simulator-frame" data-service="hmi-numpad">
                        <div class="frame-header">
                            <h3><i class="fas fa-calculator"></i> HMI Virtual Numpad</h3>
                            <div class="frame-controls">
                                <button class="frame-btn" title="Refresh" onclick="refreshFrame('hmi-numpad-frame')">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="frame-btn" title="Fullscreen" onclick="toggleFrameFullscreen('hmi-numpad-frame')">
                                    <i class="fas fa-expand"></i>
                                </button>
                                <button class="frame-btn" title="New Window" onclick="openInNewWindow(SERVICES_CONFIG.hmi_numpad.url)">
                                    <i class="fas fa-external-link-alt"></i>
                                </button>
                            </div>
                        </div>
                        <div class="frame-content">
                            <iframe id="hmi-numpad-frame" src="" frameborder="0"></iframe>
                        </div>
                    </div>
                </div>

                <!-- Focus Layout -->
                <div class="focus-layout" id="focus-container" style="display: none;">
                    <div class="focus-frame">
                        <iframe id="focus-iframe" src="" frameborder="0"></iframe>
                    </div>
                </div>

                <!-- Tab Layout -->
                <div class="tab-layout" id="tab-container" style="display: none;">
                    <div class="tab-content">
                        <iframe id="tab-iframe" src="" frameborder="0"></iframe>
                    </div>
                </div>
            </section>
        </main>

        <!-- Footer -->
        <footer class="dashboard-footer">
            <div class="footer-content">
                <div class="footer-left">
                    <span>C20 Hardware Simulator</span>
                    <span class="separator">|</span>
                    <span>Digital Twin Dashboard</span>
                </div>
                <div class="footer-right">
                    <button class="footer-btn" onclick="showHelp()">
                        <i class="fas fa-question-circle"></i> Help
                    </button>
                    <button class="footer-btn" onclick="showLogs()">
                        <i class="fas fa-terminal"></i> Logs
                    </button>
                    <button class="footer-btn" onclick="showSettings()">
                        <i class="fas fa-cog"></i> Settings
                    </button>
                </div>
            </div>
        </footer>
    </div>

    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loading-overlay">
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading Hardware Simulator...</p>
        </div>
    </div>

    <!-- Modal -->
    <div class="modal-overlay" id="modal-overlay" style="display: none;">
        <div class="modal">
            <div class="modal-header">
                <h3 id="modal-title">Modal Title</h3>
                <button class="modal-close" onclick="closeModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-content" id="modal-content">
                <!-- Modal content will be inserted here -->
            </div>
        </div>
    </div>

    <!-- Environment Configuration Display -->
    <script>
        // Display environment configuration info
        console.log('Environment Variables Loaded:', {
            host: '<?php echo $hostDomain; ?>',
            frontendPort: '<?php echo $frontendPort; ?>',
            project: '<?php echo env('COMPOSE_PROJECT_NAME', 'c20-simulator'); ?>',
            totalEnvVars: <?php echo count($envVars); ?>
        });
    </script>

    <!-- Main Application Script -->
    <script src="app.js"></script>
</body>
</html>
