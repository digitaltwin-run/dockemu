document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const config = {
        apiUrl: 'http://modbus-io-8ch:8083',
        updateInterval: 1000, // 1 second
        registerCounts: {
            coils: 8,
            inputs: 8,
            holding: 8,
            inputStatus: 8
        }
    };

    // State
    let lastUpdate = new Date();
    let isConnected = false;

    // DOM Elements
    const statusElement = document.getElementById('status');
    const lastUpdatedElement = document.getElementById('last-updated');
    const coilsContainer = document.getElementById('coils');
    const inputsContainer = document.getElementById('input-registers');
    const holdingsContainer = document.getElementById('holding-registers');
    const inputStatusContainer = document.getElementById('input-status');

    // Initialize the UI
    function initUI() {
        // Create register elements
        createRegisterElements('coil', config.registerCounts.coils, coilsContainer);
        createRegisterElements('input', config.registerCounts.inputs, inputsContainer);
        createRegisterElements('holding', config.registerCounts.holding, holdingsContainer);
        createRegisterElements('status', config.registerCounts.inputStatus, inputStatusContainer);

        // Start polling
        pollModbusData();
        setInterval(pollModbusData, config.updateInterval);
    }

    // Create register elements
    function createRegisterElements(type, count, container) {
        container.innerHTML = '';
        for (let i = 0; i < count; i++) {
            const register = document.createElement('div');
            register.className = `register ${type}`;
            register.innerHTML = `
                <div class="register-label">${type.toUpperCase()} ${i}</div>
                <div class="register-value" id="${type}-${i}">0</div>
                <div class="register-address">Addr: ${i}</div>
            `;
            container.appendChild(register);
        }
    }

    // Poll Modbus data from the API
    async function pollModbusData() {
        try {
            const response = await fetch(`${config.apiUrl}/registers`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            updateUI(data);
            updateConnectionStatus(true);
        } catch (error) {
            console.error('Error fetching Modbus data:', error);
            updateConnectionStatus(false);
        }
    }

    // Update the UI with new data
    function updateUI(data) {
        // Update coils
        if (data.coils) {
            data.coils.forEach((value, index) => {
                const element = document.getElementById(`coil-${index}`);
                if (element) {
                    element.textContent = value ? '1' : '0';
                    element.style.color = value ? '#2e7d32' : '#c62828';
                }
            });
        }

        // Update input registers
        if (data.inputRegisters) {
            data.inputRegisters.forEach((value, index) => {
                const element = document.getElementById(`input-${index}`);
                if (element) {
                    element.textContent = value;
                }
            });
        }

        // Update holding registers
        if (data.holdingRegisters) {
            data.holdingRegisters.forEach((value, index) => {
                const element = document.getElementById(`holding-${index}`);
                if (element) {
                    element.textContent = value;
                }
            });
        }

        // Update input status
        if (data.inputStatus) {
            data.inputStatus.forEach((value, index) => {
                const element = document.getElementById(`status-${index}`);
                if (element) {
                    element.textContent = value ? '1' : '0';
                    element.style.color = value ? '#2e7d32' : '#c62828';
                }
            });
        }

        // Update last updated time
        lastUpdate = new Date();
        lastUpdatedElement.textContent = `Last updated: ${lastUpdate.toLocaleTimeString()}`;
    }

    // Update connection status
    function updateConnectionStatus(connected) {
        if (connected !== isConnected) {
            isConnected = connected;
            statusElement.textContent = connected ? 'CONNECTED' : 'DISCONNECTED';
            statusElement.className = `status ${connected ? 'connected' : 'disconnected'}`;
        }
    }

    // Initialize the application
    initUI();
});
