// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables for tracking
    let startTime = new Date();
    let motionCount = 0;
    let chartInstance = null;
    
    // Initialize UI elements
    initializeClock();
    initializeSidebar();
    
    // Connect to WebSocket for real-time updates
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateDeviceStatus(data);
        updateDashboardSummary(data);
        
        // Track motion events
        if (data['motion-1'] && data['motion-1'].motion_detected) {
            motionCount++;
            document.getElementById('motion-count').textContent = motionCount;
        }
    };
    
    ws.onopen = function() {
        console.log('WebSocket connection established');
        document.querySelector('.status-indicator').classList.add('online');
        document.querySelector('.status-indicator').classList.remove('offline');
    };
    
    ws.onclose = function() {
        console.log('WebSocket connection closed');
        document.querySelector('.status-indicator').classList.remove('online');
        document.querySelector('.status-indicator').classList.add('offline');
    };
    
    // Toggle switch using checkbox
    document.getElementById('switch-toggle').addEventListener('change', function() {
        const isOn = this.checked;
        
        fetch(`/api/devices/switch-1/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: isOn ? 'turn_on' : 'turn_off'
            })
        });
    });
    
    // Set brightness with enhanced slider
    const brightnessSlider = document.getElementById('brightness-slider');
    const brightnessValue = document.getElementById('brightness-value');
    
    brightnessSlider.addEventListener('input', function() {
        brightnessValue.textContent = this.value;
    });
    
    brightnessSlider.addEventListener('change', function() {
        fetch(`/api/devices/switch-1/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'set_brightness',
                brightness: parseInt(this.value)
            })
        });
    });
    
    // Simulate motion with enhanced UI feedback
    document.getElementById('simulate-motion').addEventListener('click', function() {
        const button = this;
        const location = document.getElementById('location-select').value;
        
        // Disable button during operation
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Simulating...';
        
        fetch(`/api/devices/motion-1/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'set_location',
                location: location
            })
        }).then(() => {
            // Force motion detection
            return fetch(`/api/devices/motion-1/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'simulate_motion'
                })
            });
        }).then(() => {
            // Show success feedback
            button.classList.remove('btn-primary');
            button.classList.add('btn-success');
            button.innerHTML = '<i class="fas fa-check"></i> Motion Detected!';
            
            // Animate motion badge
            const motionBadge = document.getElementById('motion-badge');
            motionBadge.textContent = 'Motion Detected!';
            motionBadge.classList.add('active');
            
            // Reset button after delay
            setTimeout(() => {
                button.disabled = false;
                button.classList.remove('btn-success');
                button.classList.add('btn-primary');
                button.innerHTML = '<i class="fas fa-walking"></i> Simulate Motion';
            }, 2000);
        }).catch(error => {
            console.error('Error:', error);
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
            setTimeout(() => {
                button.innerHTML = '<i class="fas fa-walking"></i> Simulate Motion';
            }, 2000);
        });
    });
    
    // Run analytics with enhanced visualization
    document.getElementById('run-analytics').addEventListener('click', function() {
        const button = this;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        
        fetch('/api/analytics/energy')
            .then(response => response.json())
            .then(data => {
                // Format the JSON output
                const formattedJson = JSON.stringify(data, null, 2);
                document.getElementById('analytics-results').innerHTML = `<pre>${formattedJson}</pre>`;
                
                // Update recommendations
                const recommendationsList = document.getElementById('recommendations-list');
                recommendationsList.innerHTML = '';
                
                if (data.recommendations && data.recommendations.length > 0) {
                    data.recommendations.forEach(recommendation => {
                        const li = document.createElement('li');
                        li.textContent = recommendation;
                        recommendationsList.appendChild(li);
                    });
                } else {
                    recommendationsList.innerHTML = '<li>No recommendations available</li>';
                }
                
                // Create or update chart if Chart.js is available
                if (window.Chart && data.per_device) {
                    createEnergyChart(data);
                }
                
                // Reset button
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-sync"></i> Run Analysis';
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('analytics-results').innerHTML = 
                    `<div class="alert alert-danger">Error loading analytics data</div>`;
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-sync"></i> Run Analysis';
            });
    });
    
    // Update device status display with enhanced UI
    function updateDeviceStatus(data) {
        if (data['switch-1']) {
            const switchData = data['switch-1'];
            
            // Update switch status display
            document.getElementById('switch-status').innerHTML = `
                <div class="status-item">
                    <span class="status-label">Power</span>
                    <span class="status-value">${switchData.is_on ? 'ON' : 'OFF'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Brightness</span>
                    <span class="status-value">${switchData.brightness}%</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Power Consumption</span>
                    <span class="status-value">${switchData.power_consumption} W</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Mode</span>
                    <span class="status-value">${switchData.mode}</span>
                </div>
            `;
            
            // Update switch toggle
            document.getElementById('switch-toggle').checked = switchData.is_on;
            
            // Update card appearance based on state
            const switchCard = document.getElementById('switch-card');
            if (switchData.is_on) {
                switchCard.classList.add('active-device');
            } else {
                switchCard.classList.remove('active-device');
            }
            
            // Update brightness slider
            document.getElementById('brightness-slider').value = switchData.brightness;
            document.getElementById('brightness-value').textContent = switchData.brightness;
            
            // Update power meter
            const powerPercentage = Math.min(100, (switchData.power_consumption / 100) * 100);
            document.getElementById('power-fill').style.width = `${powerPercentage}%`;
            document.getElementById('power-value').textContent = switchData.power_consumption;
            
            // Update total power in summary
            document.getElementById('total-power').textContent = switchData.power_consumption;
        }
        
        if (data['motion-1']) {
            const motionData = data['motion-1'];
            
            // Update motion status display
            document.getElementById('motion-status').innerHTML = `
                <div class="status-item">
                    <span class="status-label">Motion</span>
                    <span class="status-value">${motionData.motion_detected ? 'DETECTED' : 'NONE'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Location</span>
                    <span class="status-value">${motionData.location}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Sensitivity</span>
                    <span class="status-value">${motionData.sensitivity}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Time Since Motion</span>
                    <span class="status-value">${motionData.time_since_motion || 'N/A'}</span>
                </div>
            `;
            
            // Update motion badge
            const motionBadge = document.getElementById('motion-badge');
            if (motionData.motion_detected) {
                motionBadge.textContent = 'Motion Detected!';
                motionBadge.classList.add('active');
            } else {
                motionBadge.textContent = 'No Motion';
                motionBadge.classList.remove('active');
            }
            
            // Update location select
            const locationSelect = document.getElementById('location-select');
            if (locationSelect.value !== motionData.location && motionData.location !== 'unknown') {
                for (let i = 0; i < locationSelect.options.length; i++) {
                    if (locationSelect.options[i].value === motionData.location) {
                        locationSelect.selectedIndex = i;
                        break;
                    }
                }
            }
        }
    }
    
    // Update dashboard summary
    function updateDashboardSummary(data) {
        // Update uptime
        const currentTime = new Date();
        const uptimeMinutes = Math.floor((currentTime - startTime) / 60000);
        const uptimeHours = Math.floor(uptimeMinutes / 60);
        const remainingMinutes = uptimeMinutes % 60;
        document.getElementById('uptime').textContent = `${uptimeHours}:${remainingMinutes.toString().padStart(2, '0')}`;
    }
    
    // Create energy consumption chart
    function createEnergyChart(data) {
        const ctx = document.getElementById('energy-chart');
        
        // If chart container doesn't exist, create it
        if (!ctx) {
            const container = document.createElement('div');
            container.className = 'chart-container mt-4';
            container.style.height = '300px';
            
            const canvas = document.createElement('canvas');
            canvas.id = 'energy-chart';
            container.appendChild(canvas);
            
            document.getElementById('analytics-results').insertAdjacentElement('afterend', container);
        }
        
        // Prepare chart data
        const labels = Object.keys(data.per_device);
        const powerData = labels.map(device => data.per_device[device].power_usage);
        const backgroundColors = [
            'rgba(76, 201, 240, 0.6)',
            'rgba(247, 37, 133, 0.6)',
            'rgba(67, 97, 238, 0.6)',
            'rgba(58, 12, 163, 0.6)',
            'rgba(114, 9, 183, 0.6)'
        ];
        
        // Destroy previous chart instance if it exists
        if (chartInstance) {
            chartInstance.destroy();
        }
        
        // Create new chart
        chartInstance = new Chart(
            document.getElementById('energy-chart'),
            {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Power Usage (W)',
                        data: powerData,
                        backgroundColor: backgroundColors.slice(0, labels.length),
                        borderColor: backgroundColors.map(color => color.replace('0.6', '1')),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Device Energy Consumption',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Power (Watts)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Devices'
                            }
                        }
                    }
                }
            }
        );
    }
    
    // Initialize clock
    function initializeClock() {
        function updateClock() {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            document.getElementById('current-time').textContent = timeString;
        }
        
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    // Initialize sidebar toggle
    function initializeSidebar() {
        document.getElementById('sidebar-toggle').addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('active');
        });
    }
    
    // Initial device status load
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            updateDeviceStatus(data);
        })
        .catch(error => {
            console.error('Error loading device data:', error);
        });
});