class C20Display {
    constructor() {
        this.ws = null;
        this.currentScreen = 'boot';
        this.menuIndex = 0;
        this.pressureData = {
            hp: [],
            mp: [],
            lp: []
        };

        this.init();
    }

    init() {
        // Połączenie WebSocket z emulatorem RPi
        this.connectWebSocket();

        // Symulacja bootowania
        this.simulateBoot();

        // Nasłuchiwanie na komunikaty z klawiatury
        window.addEventListener('message', (e) => {
            if (e.data.type === 'keypress') {
                this.handleKeyPress(e.data.key);
            }
        });
    }

    connectWebSocket() {
        this.ws = new WebSocket('ws://localhost:9001');

        this.ws.onopen = () => {
            console.log('Connected to C20 system');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleSystemData(data);
        };
    }

    simulateBoot() {
        const bootProgress = document.getElementById('bootProgress');
        const bootStatus = document.getElementById('bootStatus');
        const steps = [
            'Inicjalizacja systemu...',
            'Sprawdzanie czujników ciśnienia...',
            'Kalibracja PCB OUT 12...',
            'Ładowanie procedur testowych...',
            'System gotowy!'
        ];

        let progress = 0;
        let stepIndex = 0;

        const bootInterval = setInterval(() => {
            progress += 2;
            bootProgress.style.width = progress + '%';

            if (progress % 20 === 0 && stepIndex < steps.length) {
                bootStatus.textContent = steps[stepIndex++];
            }

            if (progress >= 100) {
                clearInterval(bootInterval);
                setTimeout(() => {
                    this.showMainMenu();
                }, 1000);
            }
        }, 50);
    }

    showMainMenu() {
        document.getElementById('bootScreen').style.display = 'none';
        document.getElementById('mainMenu').style.display = 'block';
        this.currentScreen = 'menu';

        // Start aktualizacji danych z czujników
        this.startSensorUpdates();
    }

    startSensorUpdates() {
        setInterval(() => {
            // Symulacja odczytów z czujników
            this.updatePressureDisplay({
                hp: Math.random() * 400,  // 0-400 bar
                mp: Math.random() * 25,   // 0-25 bar
                lp: (Math.random() - 0.5) * 120  // -60 to +60 mbar
            });
        }, 100);
    }

    updatePressureDisplay(pressures) {
        document.getElementById('pressureHP').textContent = `HP: ${pressures.hp.toFixed(1)} bar`;
        document.getElementById('pressureMP').textContent = `MP: ${pressures.mp.toFixed(1)} bar`;
        document.getElementById('pressureLP').textContent = `LP: ${pressures.lp.toFixed(1)} mbar`;

        // Zapisz dane dla wykresu
        this.pressureData.hp.push(pressures.hp);
        this.pressureData.mp.push(pressures.mp);
        this.pressureData.lp.push(pressures.lp);

        // Ogranicz historię do 100 próbek
        Object.keys(this.pressureData).forEach(key => {
            if (this.pressureData[key].length > 100) {
                this.pressureData[key].shift();
            }
        });
    }

    handleKeyPress(key) {
        if (this.currentScreen === 'menu') {
            const menuItems = document.querySelectorAll('.menu-item');

            switch(key) {
                case 'ArrowUp':
                    menuItems[this.menuIndex].classList.remove('active');
                    this.menuIndex = (this.menuIndex - 1 + menuItems.length) % menuItems.length;
                    menuItems[this.menuIndex].classList.add('active');
                    break;

                case 'ArrowDown':
                    menuItems[this.menuIndex].classList.remove('active');
                    this.menuIndex = (this.menuIndex + 1) % menuItems.length;
                    menuItems[this.menuIndex].classList.add('active');
                    break;

                case 'Enter':
                    const action = menuItems[this.menuIndex].dataset.action;
                    this.executeAction(action);
                    break;
            }
        }
    }

    executeAction(action) {
        switch(action) {
            case 'test':
                this.startTest();
                break;
            case 'autodiag':
                this.runDiagnostics();
                break;
            // Dodaj więcej akcji
        }
    }

    startTest() {
        document.getElementById('mainMenu').style.display = 'none';
        document.getElementById('testScreen').style.display = 'block';
        this.currentScreen = 'test';

        // Wyślij komendę do systemu
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                command: 'START_TEST',
                parameters: {
                    type: 'BLS_MASK_TEST',
                    duration: 120
                }
            }));
        }
    }
}

// Uruchom aplikację
const display = new C20Display();