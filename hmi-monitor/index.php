<?php
// Load environment variables
$env_vars = [];
if (file_exists('.env')) {
    $lines = file('.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos($line, '=') !== false && !str_starts_with($line, '#')) {
            list($key, $value) = explode('=', $line, 2);
            $env_vars[trim($key)] = trim($value);
        }
    }
}

// Include RPI3 viewer
require_once 'rpi3-viewer.php';
$rpi3_viewer = new RPI3Viewer();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMI Virtual Monitor</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="rpi3-styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>HMI Virtual Monitor</h1>
            <div class="status">
                <span id="status">Disconnected</span>
                <div class="led" id="status-led"></div>
            </div>
        </header>

        <!-- Tab Navigation -->
        <div class="tab-navigation">
            <button class="tab-button active" onclick="openTab(event, 'monitor-tab')">🖥️ Virtual Monitor</button>
            <button class="tab-button" onclick="openTab(event, 'rpi3-tab')">🔌 RPI3 System</button>
            <button class="tab-button" onclick="openTab(event, 'diagnostics-tab')">🔧 Diagnostics</button>
        </div>

        <!-- Virtual Monitor Tab -->
        <div id="monitor-tab" class="tab-content active">
            <div class="monitor-container">
                <div class="display-wrapper">
                    <div class="monitor-bezel">
                        <div class="screen-area">
                            <canvas id="display-canvas" width="1920" height="1080"></canvas>
                            <div class="overlay-controls" id="overlay-controls">
                                <div class="control-button" id="power-btn" title="Power">⏻</div>
                                <div class="control-button" id="menu-btn" title="Menu">☰</div>
                                <div class="control-button" id="source-btn" title="Input Source">📺</div>
                            </div>
                        </div>
                        
                        <div class="monitor-info">
                            <div class="brand">HMI Display</div>
                            <div class="model">HD-7.9-HDMI</div>
                            <div class="power-led" id="power-led"></div>
                        </div>
                    </div>
                </div>

                <div class="display-controls">
                    <div class="resolution-controls">
                        <label for="resolution-select">Resolution:</label>
                        <select id="resolution-select">
                            <option value="1920x1080">1920x1080 (Full HD)</option>
                            <option value="1680x1050">1680x1050 (WSXGA+)</option>
                            <option value="1440x900">1440x900 (WXGA+)</option>
                            <option value="1366x768">1366x768 (HD)</option>
                            <option value="1280x720">1280x720 (HD 720p)</option>
                            <option value="1024x768">1024x768 (XGA)</option>
                            <option value="800x600">800x600 (SVGA)</option>
                        </select>
                    </div>

                    <div class="refresh-controls">
                        <label for="refresh-rate">Refresh Rate:</label>
                        <select id="refresh-rate">
                            <option value="60">60 Hz</option>
                            <option value="75">75 Hz</option>
                            <option value="120">120 Hz</option>
                            <option value="144">144 Hz</option>
                        </select>
                    </div>

                    <div class="input-source">
                        <label for="input-source">Input Source:</label>
                        <select id="input-source">
                            <option value="hdmi1">HDMI 1 (RPi)</option>
                            <option value="hdmi2">HDMI 2</option>
                            <option value="vga">VGA</option>
                            <option value="dvi">DVI</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="monitor-settings">
                <div class="settings-panel">
                    <h3>Display Settings</h3>
                    
                    <div class="setting-group">
                        <div class="setting">
                            <label for="brightness">Brightness:</label>
                            <input type="range" id="brightness" min="0" max="100" value="80">
                            <span id="brightness-value">80%</span>
                        </div>
                        
                        <div class="setting">
                            <label for="contrast">Contrast:</label>
                            <input type="range" id="contrast" min="0" max="100" value="75">
                            <span id="contrast-value">75%</span>
                        </div>
                        
                        <div class="setting">
                            <label for="saturation">Saturation:</label>
                            <input type="range" id="saturation" min="0" max="100" value="50">
                            <span id="saturation-value">50%</span>
                        </div>
                        
                        <div class="setting">
                            <label for="hue">Hue:</label>
                            <input type="range" id="hue" min="-180" max="180" value="0">
                            <span id="hue-value">0°</span>
                        </div>
                    </div>
                </div>

                <div class="stream-panel">
                    <h3>Stream Settings</h3>
                    
                    <div class="setting-group">
                        <div class="setting">
                            <label for="stream-quality">Quality:</label>
                            <select id="stream-quality">
                                <option value="low">Low (480p)</option>
                                <option value="medium" selected>Medium (720p)</option>
                                <option value="high">High (1080p)</option>
                                <option value="ultra">Ultra (4K)</option>
                            </select>
                        </div>
                        
                        <div class="setting">
                            <label for="frame-rate">Frame Rate:</label>
                            <select id="frame-rate">
                                <option value="15">15 fps</option>
                                <option value="30" selected>30 fps</option>
                                <option value="60">60 fps</option>
                            </select>
                        </div>
                        
                        <div class="setting">
                            <button id="fullscreen-btn">🔍 Fullscreen</button>
                            <button id="capture-btn">📸 Capture</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="connection-info">
                <div class="info-panel">
                    <h3>Connection Info</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="label">WebSocket URL:</span>
                            <span class="value" id="ws-url">ws://localhost:<?php echo $env_vars['HMI_MONITOR_WS_PORT'] ?? '5570'; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="label">VNC Port:</span>
                            <span class="value"><?php echo $env_vars['HMI_MONITOR_VNC_PORT'] ?? '5571'; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="label">Frame Rate:</span>
                            <span class="value" id="actual-fps">0 fps</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Latency:</span>
                            <span class="value" id="latency">0 ms</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Data Rate:</span>
                            <span class="value" id="data-rate">0 KB/s</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Frames Received:</span>
                            <span class="value" id="frames-received">0</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- RPI3 System Tab -->
        <div id="rpi3-tab" class="tab-content">
            <?php $rpi3_viewer->renderRPI3Monitor(); ?>
        </div>

        <!-- Diagnostics Tab -->
        <div id="diagnostics-tab" class="tab-content">
            <div class="diagnostics-container">
                <h3>🔧 System Diagnostics</h3>
                
                <div class="diagnostics-grid">
                    <div class="diag-section">
                        <h4>Environment Variables</h4>
                        <div class="env-table">
                            <table>
                                <tr><th>Variable</th><th>Value</th></tr>
                                <?php foreach ($env_vars as $key => $value): ?>
                                    <?php if (strpos($key, 'PORT') !== false): ?>
                                        <tr>
                                            <td><?php echo htmlspecialchars($key); ?></td>
                                            <td><?php echo htmlspecialchars($value); ?></td>
                                        </tr>
                                    <?php endif; ?>
                                <?php endforeach; ?>
                            </table>
                        </div>
                    </div>
                    
                    <div class="diag-section">
                        <h4>Service Status</h4>
                        <div class="service-status" id="service-status">
                            <!-- Will be populated by JavaScript -->
                        </div>
                    </div>
                    
                    <div class="diag-section">
                        <h4>Hardware Interfaces</h4>
                        <div class="hardware-status">
                            <div class="hw-item">
                                <span class="hw-type">I2C Bus</span>
                                <span class="hw-status">Scanning...</span>
                            </div>
                            <div class="hw-item">
                                <span class="hw-type">Serial Ports</span>
                                <span class="hw-status">Detecting...</span>
                            </div>
                            <div class="hw-item">
                                <span class="hw-type">USB Devices</span>
                                <span class="hw-status">Enumerating...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="hmi-monitor.js"></script>
    <script>
        // Tab functionality
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            
            // Hide all tab content
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].classList.remove("active");
            }
            
            // Remove active class from all tab buttons
            tablinks = document.getElementsByClassName("tab-button");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].classList.remove("active");
            }
            
            // Show the specific tab content and add active class to the button
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
        }

        // Initialize diagnostics
        function updateServiceStatus() {
            const services = [
                { name: 'Dashboard', port: <?php echo $env_vars['DASHBOARD_PORT'] ?? '8060'; ?> },
                { name: 'HMI Monitor', port: <?php echo $env_vars['HMI_MONITOR_PORT'] ?? '8072'; ?> },
                { name: 'RPI3 QEMU', port: <?php echo $env_vars['QEMU_API_PORT'] ?? '4001'; ?> },
                { name: 'MQTT', port: <?php echo $env_vars['MQTT_PORT'] ?? '1883'; ?> }
            ];
            
            const statusContainer = document.getElementById('service-status');
            statusContainer.innerHTML = '';
            
            services.forEach(service => {
                const div = document.createElement('div');
                div.className = 'service-item';
                div.innerHTML = `
                    <span class="service-name">${service.name}</span>
                    <span class="service-port">:${service.port}</span>
                    <span class="service-indicator" id="status-${service.port}">Checking...</span>
                `;
                statusContainer.appendChild(div);
                
                // Check service status
                checkServiceStatus(service.port);
            });
        }
        
        function checkServiceStatus(port) {
            fetch(`http://localhost:${port}`)
                .then(response => {
                    const indicator = document.getElementById(`status-${port}`);
                    if (response.ok) {
                        indicator.textContent = '✅ Online';
                        indicator.className = 'service-indicator online';
                    } else {
                        indicator.textContent = '⚠️ Error';
                        indicator.className = 'service-indicator error';
                    }
                })
                .catch(error => {
                    const indicator = document.getElementById(`status-${port}`);
                    indicator.textContent = '❌ Offline';
                    indicator.className = 'service-indicator offline';
                });
        }
        
        // Initialize diagnostics when diagnostics tab is opened
        document.addEventListener('DOMContentLoaded', function() {
            // Update service status when diagnostics tab is clicked
            const diagTab = document.querySelector('[onclick*="diagnostics-tab"]');
            diagTab.addEventListener('click', function() {
                setTimeout(updateServiceStatus, 100);
            });
        });
    </script>
</body>
</html>
