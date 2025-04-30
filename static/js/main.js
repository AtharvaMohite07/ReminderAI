document.addEventListener('DOMContentLoaded', function() {
    const recordButton = document.getElementById('recordButton');
    const continuousListenButton = document.getElementById('continuousListenButton');
    const statusDiv = document.getElementById('status');
    const speechTextDiv = document.getElementById('speechText');
    const responseTextDiv = document.getElementById('responseText');
    const locationSelect = document.getElementById('locationSelect');
    const showRemindersBtn = document.getElementById('showRemindersBtn');
    const remindersList = document.getElementById('remindersList');
    const soundWaves = document.getElementById('soundWaves');
    
    let recognition;
    let isListening = false;
    let isContinuousMode = false;
    
    // Initialize speech recognition
    function initSpeechRecognition() {
        window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!window.SpeechRecognition) {
            statusDiv.innerHTML = "<i class='fas fa-exclamation-circle'></i> Speech recognition not supported in this browser.";
            recordButton.disabled = true;
            if (continuousListenButton) continuousListenButton.disabled = true;
            return;
        }
        
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            statusDiv.innerHTML = "<i class='fas fa-microphone-alt'></i> Listening...";
            isListening = true;
            if (isContinuousMode) {
                continuousListenButton.innerHTML = "<i class='fas fa-stop-circle'></i> Disable Assistant";
                continuousListenButton.classList.add('active');
                if (soundWaves) soundWaves.classList.add('active');
            }
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            speechTextDiv.textContent = transcript;
            
            // Show loading indicator
            showLoadingIndicator();
            
            // Process the speech
            processSpeech(transcript);
        };
        
        recognition.onerror = function(event) {
            if (event.error !== 'no-speech') {
                statusDiv.innerHTML = "<i class='fas fa-exclamation-circle'></i> Error: " + event.error;
            } else {
                statusDiv.innerHTML = "<i class='fas fa-info-circle'></i> No speech detected.";
            }
            isListening = false;
            
            // If in continuous mode, restart listening
            if (isContinuousMode) {
                setTimeout(() => {
                    if (isContinuousMode) recognition.start();
                }, 500);
            }
        };
        
        recognition.onend = function() {
            if (!isContinuousMode) {
                statusDiv.innerHTML = "<i class='fas fa-info-circle'></i> Ready to listen...";
                isListening = false;
                if (soundWaves) soundWaves.classList.remove('active');
            } else if (isContinuousMode) {
                // Restart in continuous mode
                setTimeout(() => {
                    if (isContinuousMode) recognition.start();
                }, 500);
            }
        };
    }
    
    // Show loading indicator
    function showLoadingIndicator() {
        const loadingIndicator = document.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'flex';
            setTimeout(() => {
                loadingIndicator.style.display = 'none';
            }, 1500);
        }
    }
    
    // Process speech via API
    function processSpeech(text) {
        statusDiv.innerHTML = "<i class='fas fa-cog fa-spin'></i> Processing...";
        
        fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        })
        .then(response => response.json())
        .then(data => {
            responseTextDiv.textContent = data.response;
            
            // Also speak the response
            speakResponse(data.response);
            
            // Refresh locations list
            loadLocations();
            
            // Update status
            if (!isContinuousMode) {
                statusDiv.innerHTML = "<i class='fas fa-info-circle'></i> Ready to listen...";
            } else {
                statusDiv.innerHTML = "<i class='fas fa-satellite-dish'></i> Always listening...";
            }
        })
        .catch(error => {
            console.error('Error:', error);
            responseTextDiv.textContent = "Error processing your request.";
            statusDiv.innerHTML = "<i class='fas fa-exclamation-circle'></i> Error occurred.";
        });
    }
    
    // Text-to-speech for response
    function speakResponse(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            window.speechSynthesis.speak(utterance);
        }
    }
    
    // Toggle continuous listening mode
    function toggleContinuousListening() {
        isContinuousMode = !isContinuousMode;
        
        if (isContinuousMode) {
            // Start continuous listening
            if (!isListening && recognition) {
                continuousListenButton.innerHTML = "<i class='fas fa-stop-circle'></i> Disable Assistant";
                continuousListenButton.classList.add('active');
                if (soundWaves) soundWaves.classList.add('active');
                recognition.start();
            }
        } else {
            // Stop continuous listening
            if (isListening && recognition) {
                recognition.stop();
                statusDiv.innerHTML = "<i class='fas fa-info-circle'></i> Ready to listen...";
                continuousListenButton.innerHTML = "<i class='fas fa-satellite-dish'></i> Enable Assistant";
                continuousListenButton.classList.remove('active');
                if (soundWaves) soundWaves.classList.remove('active');
            }
        }
    }
    
    // Load locations for dropdown
    function loadLocations() {
        fetch('/api/locations')
        .then(response => response.json())
        .then(data => {
            locationSelect.innerHTML = '<option value="">Select a location</option>';
            
            data.locations.forEach(location => {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                locationSelect.appendChild(option);
            });
            
            // Update location count badge if it exists
            const locationCountBadge = document.querySelector('.location-count');
            if (locationCountBadge) {
                locationCountBadge.textContent = data.locations.length;
            }
        })
        .catch(error => console.error('Error loading locations:', error));
    }
    
    // Load reminders for selected location
    function loadReminders(location) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'reminders-loading';
        loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-pulse"></i> Loading...';
        remindersList.innerHTML = '';
        remindersList.appendChild(loadingIndicator);
        
        fetch(`/api/reminders/${encodeURIComponent(location)}`)
        .then(response => response.json())
        .then(data => {
            remindersList.innerHTML = '';
            
            if (data.reminders.length === 0) {
                const li = document.createElement('li');
                li.innerHTML = '<i class="fas fa-info-circle"></i> No reminders for this location';
                remindersList.appendChild(li);
                return;
            }
            
            data.reminders.forEach(reminder => {
                const li = document.createElement('li');
                
                const taskSpan = document.createElement('span');
                taskSpan.textContent = reminder.task;
                taskSpan.className = 'task-text';
                li.appendChild(taskSpan);
                
                const completeBtn = document.createElement('button');
                completeBtn.innerHTML = '<i class="fas fa-check"></i> Complete';
                completeBtn.classList.add('complete-btn');
                completeBtn.onclick = function() {
                    markReminderComplete(reminder.id, li);
                };
                li.appendChild(completeBtn);
                
                remindersList.appendChild(li);
            });
            
            // Update reminder count badge if it exists
            const reminderCountBadge = document.querySelector('.reminder-count');
            if (reminderCountBadge) {
                // Get total reminders across all locations
                fetch('/api/reminders/count')
                    .then(response => response.json())
                    .then(countData => {
                        reminderCountBadge.textContent = countData.count || data.reminders.length;
                    })
                    .catch(() => {
                        reminderCountBadge.textContent = data.reminders.length;
                    });
            }
        })
        .catch(error => {
            console.error('Error loading reminders:', error);
            remindersList.innerHTML = '<li><i class="fas fa-exclamation-circle"></i> Error loading reminders</li>';
        });
    }
    
    // Mark reminder as complete
    function markReminderComplete(reminderId, listItem) {
        listItem.classList.add('completing');
        
        fetch(`/api/reminders/${reminderId}/complete`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                listItem.classList.remove('completing');
                listItem.classList.add('completed');
                
                setTimeout(() => {
                    listItem.style.height = '0';
                    listItem.style.padding = '0';
                    listItem.style.opacity = '0';
                    
                    setTimeout(() => {
                        listItem.remove();
                        if (remindersList.children.length === 0) {
                            const li = document.createElement('li');
                            li.innerHTML = '<i class="fas fa-info-circle"></i> No reminders for this location';
                            remindersList.appendChild(li);
                        }
                        
                        // Update reminder count badge
                        const reminderCountBadge = document.querySelector('.reminder-count');
                        if (reminderCountBadge) {
                            const currentCount = parseInt(reminderCountBadge.textContent);
                            if (!isNaN(currentCount) && currentCount > 0) {
                                reminderCountBadge.textContent = currentCount - 1;
                            }
                        }
                    }, 300);
                }, 500);
            }
        })
        .catch(error => {
            console.error('Error completing reminder:', error);
            listItem.classList.remove('completing');
        });
    }
    
    // Set up event listeners
    if (recordButton) {
        recordButton.addEventListener('mousedown', function() {
            if (!isListening && recognition) {
                if (soundWaves) soundWaves.classList.add('active');
                recognition.start();
            }
        });
        
        recordButton.addEventListener('mouseup', function() {
            if (isListening && recognition && !isContinuousMode) {
                if (soundWaves) soundWaves.classList.remove('active');
                recognition.stop();
            }
        });
    }
    
    // Add the continuous listening button event listener if it exists
    if (continuousListenButton) {
        continuousListenButton.addEventListener('click', toggleContinuousListening);
    }
    
    if (showRemindersBtn) {
        showRemindersBtn.addEventListener('click', function() {
            const selectedLocation = locationSelect.value;
            if (selectedLocation) {
                loadReminders(selectedLocation);
            } else {
                remindersList.innerHTML = '<li><i class="fas fa-exclamation-circle"></i> Please select a location</li>';
            }
        });
    }
    
    // Dark mode toggle
    const modeSwitch = document.querySelector('.mode-switch');
    if (modeSwitch) {
        // Check for saved preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-theme');
            const icon = modeSwitch.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
        }
        
        modeSwitch.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkMode', isDark);
            
            const icon = this.querySelector('i');
            if (icon) {
                if (isDark) {
                    icon.classList.remove('fa-moon');
                    icon.classList.add('fa-sun');
                } else {
                    icon.classList.remove('fa-sun');
                    icon.classList.add('fa-moon');
                }
            }
        });
    }
    
    // Mobile menu toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    const closeSidebar = document.querySelector('.close-sidebar');
    
    if (mobileToggle && sidebar && closeSidebar) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.add('open');
        });
        
        closeSidebar.addEventListener('click', function() {
            sidebar.classList.remove('open');
        });
    }
    
    // Help section toggle
    const helpHeader = document.querySelector('.help-card .card-header');
    const helpContent = document.querySelector('.help-content');
    const toggleHelpBtn = document.querySelector('.toggle-help-btn');
    
    if (helpHeader && helpContent && toggleHelpBtn) {
        // Check if help should be collapsed by default
        if (localStorage.getItem('helpCollapsed') === 'true') {
            helpContent.classList.add('collapsed');
            toggleHelpBtn.classList.add('open');
        }
        
        helpHeader.addEventListener('click', function() {
            helpContent.classList.toggle('collapsed');
            toggleHelpBtn.classList.toggle('open');
            localStorage.setItem('helpCollapsed', helpContent.classList.contains('collapsed'));
        });
    }
    
    // Menu navigation
    const menuItems = document.querySelectorAll('.menu li');
    const pages = document.querySelectorAll('.page');
    
    if (menuItems.length > 0) {
        menuItems.forEach(item => {
            item.addEventListener('click', function() {
                const page = this.getAttribute('data-page');
                
                // Update active menu item
                menuItems.forEach(mi => mi.classList.remove('active'));
                this.classList.add('active');
                
                // Switch page content if available
                if (pages.length > 0 && page) {
                    pages.forEach(p => p.classList.remove('active'));
                    const targetPage = document.querySelector(`.page[data-page="${page}"]`);
                    if (targetPage) {
                        targetPage.classList.add('active');
                    }
                }
                
                // Close sidebar on mobile after selection
                if (sidebar && window.innerWidth < 768) {
                    sidebar.classList.remove('open');
                }
            });
        });
    }
    
    // Initialize the app
    initSpeechRecognition();
    loadLocations();
});