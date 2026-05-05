document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const loader = document.getElementById('loader');
    const resultTemplate = document.getElementById('result-template');

    // Modal Elements
    const altModal = document.getElementById('alt-modal');
    const modalDiseaseName = document.getElementById('modal-disease-name');
    const modalConfidence = document.getElementById('modal-confidence');
    const modalDescription = document.getElementById('modal-description');
    const modalSymptoms = document.getElementById('modal-symptoms');
    const modalPrecautions = document.getElementById('modal-precautions');
    const closeModalBtn = altModal.querySelector('.close-btn');
    
    // Login Elements
    const loginContainer = document.getElementById('login-container');
    const loginPassword = document.getElementById('login-password');
    const loginBtn = document.getElementById('login-btn');

    // Close Modal Events
    closeModalBtn.onclick = () => altModal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === altModal) altModal.style.display = 'none';
    };



    // Speech Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isListening = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.interimResults = false;

        recognition.onstart = () => {
            isListening = true;
            micBtn.classList.add('listening');
            userInput.placeholder = "Listening...";
        };

        recognition.onend = () => {
            isListening = false;
            micBtn.classList.remove('listening');
            userInput.placeholder = "Describe your symptoms...";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            // Optional: Auto-send after speech
            // handleSendMessage(); 
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            isListening = false;
            micBtn.classList.remove('listening');
            userInput.placeholder = "Error. Try typing.";
        };
    } else {
        micBtn.style.display = 'none'; // Hide if not supported
        console.log("Web Speech API not supported");
    }

    // Auto-focus input on load
    userInput.focus();

    // Auto-focus input on load
    userInput.focus();

    // --- Personalized Health Reports State ---
    let chatState = 'ASK_NAME'; // Initial state for onboarding
    let userName = '';
    let userAge = '';
    let userProfile = {
        gender: '',
        conditions: '',
        allergies: '',
        lifestyle: '',
        medications: ''
    };
    let userLocation = null; // {lat, lon}
    const userDropdown = document.getElementById('user-dropdown');
    const deleteUserBtn = document.getElementById('delete-user-btn');
    
    // Fetch existing users on load
    fetchUsers();


    async function fetchUsers() {
        try {
            const res = await fetch('/users');
            if (res.ok) {
                const data = await res.json();
                populateDropdown(data.users);
                
                // Smarter greeting
                if (data.users && data.users.length > 0) {
                    appendMessage("Welcome back! Select your profile from the dropdown to continue, or tell me your name if you're new.", 'bot');
                } else {
                    appendMessage("Hello! Welcome to MediBot. What is your name?", 'bot');
                }
            }
        } catch (e) {
            console.error("Failed to fetch users", e);
        }
    }

    function populateDropdown(users) {
        // Keep the default "+ Create New User" option
        userDropdown.innerHTML = '<option value="new">+ Create New User</option>';
        users.forEach(user => {
            const opt = document.createElement('option');
            // User format: "raj_25"
            opt.value = opt.textContent = user; 
            userDropdown.appendChild(opt);
        });
    }

    userDropdown.addEventListener('change', async (e) => {
        const val = e.target.value;
        if (val === 'new') {
            loginContainer.style.display = 'none';
            deleteUserBtn.style.display = 'none';
            startNewUserFlow();
        } else {
            // Existing user - show password prompt
            loginContainer.style.display = 'flex';
            loginPassword.value = '';
            loginPassword.focus();
            deleteUserBtn.style.display = 'none'; // Hide delete until logged in
            
            // Clear current state to avoid leakage
            userName = '';
            userAge = '';
            chatHistory.innerHTML = '';
            appendMessage("Please enter the password for this health report to continue.", 'bot');
            updateDownloadLink();
        }
    });

    loginBtn.onclick = async () => {
        const val = userDropdown.value;
        const password = loginPassword.value;
        
        if (!password) {
            alert("Please enter a password.");
            return;
        }

        try {
            const res = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: val, password: password })
            });

            if (res.ok) {
                // Login successful
                const lastIdx = val.lastIndexOf('_');
                userName = val.substring(0, lastIdx);
                userAge = val.substring(lastIdx + 1);
                
                // Fetch profile (without password)
                const profileRes = await fetch(`/users/${val}/profile`);
                if (profileRes.ok) {
                    const data = await profileRes.json();
                    userProfile = data.profile;
                }

                chatState = 'CHATTING';
                currentSessionSymptoms = [];
                chatHistory.innerHTML = ''; 
                appendMessage(`Welcome back, ${capitalize(userName)}! Authorization successful. Please describe your symptoms.`, 'bot');
                
                loginContainer.style.display = 'none';
                deleteUserBtn.style.display = 'block';
                updateDownloadLink();
                requestUserLocation();
            } else {
                const data = await res.json();
                alert(data.error || "Login failed.");
            }
        } catch (error) {
            console.error("Login error:", error);
            alert("An error occurred during login.");
        }
    };

    deleteUserBtn.addEventListener('click', async () => {
        if (!userName || !userAge) return;
        
        const confirmDelete = confirm(`Are you sure you want to delete the health report for ${capitalize(userName)}? This cannot be undone.`);
        if (!confirmDelete) return;

        try {
            const userId = `${userName}_${userAge}`;
            const res = await fetch(`/users/${userId}`, { method: 'DELETE' });
            
            if (res.ok || res.status === 404) {
                alert(`Health report for ${capitalize(userName)} deleted.`);
                await fetchUsers();
                startNewUserFlow();
            } else {
                alert("Failed to delete user report.");
            }
        } catch (error) {
            console.error("Error deleting user:", error);
            alert("An error occurred while deleting the user report.");
        }
    });

    function capitalize(str) {

        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    function startNewUserFlow() {
        chatState = 'ASK_NAME';
        userName = '';
        userAge = '';
        userProfile = { gender: '', conditions: '', allergies: '', lifestyle: '', medications: '', password: '' };
        userLocation = null;
        currentSessionSymptoms = [];
        chatHistory.innerHTML = '';
        appendMessage("Hello! Welcome to MediBot. What is your name?", 'bot');
        userDropdown.value = 'new';
        loginContainer.style.display = 'none';
        deleteUserBtn.style.display = 'none';
        updateDownloadLink();
    }

    function requestUserLocation() {
        if (!navigator.geolocation) {
            console.log("Geolocation not supported by this browser.");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                };
                console.log("Location obtained:", userLocation);
            },
            (error) => {
                let errorMsg = "Location access denied.";
                if (error.code === error.PERMISSION_DENIED) {
                    errorMsg = "Location denied. Nearby facilities will not be shown. Please enable location for full features.";
                } else if (error.code === error.POSITION_UNAVAILABLE) {
                    errorMsg = "Location information is unavailable.";
                } else if (error.code === error.TIMEOUT) {
                    errorMsg = "Location request timed out.";
                }
                console.warn(errorMsg);
                // Only alert once if possible, or just keep in console
            },
            { enableHighAccuracy: false, timeout: 5000, maximumAge: 0 }
        );
    }
    
    // Initialize first message (moved to fetchUsers)
    // appendMessage("Hello! Welcome to MediBot. What is your name?", 'bot');

    let currentSessionSymptoms = [];
    const chatActions = document.getElementById('chat-actions');

    // Event Listeners
    sendBtn.addEventListener('click', () => handleSendMessage());

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSendMessage();
    });

    micBtn.addEventListener('click', () => {
        if (!recognition) return;
        if (isListening) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    async function handleSendMessage(forceDiagnose = false, noneOfThese = false) {
        let message = userInput.value.trim();

        // If force diagnose and no input, just send a trigger
        if (forceDiagnose && !message) {
            message = "Diagnose with my current symptoms.";
        }

        if (noneOfThese) {
            message = "None of these symptoms match.";
        }

        if (!message && !forceDiagnose && !noneOfThese) return;

        // 1. Add User Message

        // 1. Add User Message
        appendMessage(message, 'user');
        userInput.value = '';
        
        // --- State Machine Logic (Extended Onboarding) ---
        if (chatState === 'ASK_NAME') {
            userName = message.replace(/[^a-zA-Z]/g, '').toLowerCase(); // Sanitize
            if (!userName) {
                 appendMessage("Please enter a valid name.", 'bot');
                 return;
            }
            chatState = 'ASK_AGE';
            appendMessage(`Nice to meet you, ${capitalize(userName)}. What is your age?`, 'bot');
            return;
        }

        if (chatState === 'ASK_AGE') {
            const age = parseInt(message, 10);
            if (isNaN(age) || age <= 0 || age > 120) {
                 appendMessage("Please enter a valid age (number).", 'bot');
                 return;
            }
            userAge = age.toString();
            chatState = 'ASK_GENDER';
            appendMessage("What is your gender? (e.g., Male, Female, Other)", 'bot');
            return;
        }

        if (chatState === 'ASK_GENDER') {
            userProfile.gender = message;
            chatState = 'ASK_CONDITIONS';
            appendMessage("Do you have any existing medical conditions? (e.g., Diabetes, Heart problems, Asthma). Type 'None' if none.", 'bot');
            return;
        }

        if (chatState === 'ASK_CONDITIONS') {
            userProfile.conditions = message;
            chatState = 'ASK_ALLERGIES';
            appendMessage("Do you have any allergies? (e.g., Aspirin, Nuts, Pollen). Type 'None' if none.", 'bot');
            return;
        }

        if (chatState === 'ASK_ALLERGIES') {
            userProfile.allergies = message;
            chatState = 'ASK_LIFESTYLE';
            appendMessage("Tell me about your lifestyle habits (e.g., Smoking, Alcohol use, Sleep patterns).", 'bot');
            return;
        }

        if (chatState === 'ASK_LIFESTYLE') {
            userProfile.lifestyle = message;
            chatState = 'ASK_MEDS';
            appendMessage("Are you currently taking any ongoing medications?", 'bot');
            return;
        }

        if (chatState === 'ASK_MEDS') {
            userProfile.medications = message;
            chatState = 'ASK_PASSWORD';
            appendMessage("Finally, please create a password for your health report. This will be required to access your data later.", 'bot');
            return;
        }

        if (chatState === 'ASK_PASSWORD') {
            if (message.length < 3) {
                appendMessage("Please enter a password with at least 3 characters for security.", 'bot');
                return;
            }
            userProfile.password = message;
            chatState = 'CHATTING';
            
            // Add to dropdown if not exists (optimistic UI update)
            const newId = `${userName}_${userAge}`;
            let exists = Array.from(userDropdown.options).some(opt => opt.value === newId);
            if (!exists) {
                const opt = document.createElement('option');
                opt.value = opt.textContent = newId;
                userDropdown.appendChild(opt);
            }
            userDropdown.value = newId;
            deleteUserBtn.style.display = 'block';
            loginContainer.style.display = 'none';
            
            updateDownloadLink();

            appendMessage(`Profile and password saved! How are you feeling today? Please describe your symptoms.`, 'bot');
            
            // Request location upon completing onboarding
            requestUserLocation();
            return;
        }

        userInput.disabled = true;
        sendBtn.disabled = true;
        loader.style.display = 'block';
        chatActions.innerHTML = ''; // Clear actions

        // Try to refresh location before sending if still null
        if (!userLocation) requestUserLocation();

        try {
            // 2. Send to Backend
            console.log("DEBUG: Sending request with location:", userLocation);
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    history: currentSessionSymptoms,
                    force: forceDiagnose,
                    none_of_these: noneOfThese,
                    user_name: userName, // Pass credentials dynamically
                    user_age: userAge,
                    user_profile: userProfile,
                    location: userLocation
                })
            });

            const data = await response.json();

            // 3. Handle Response
            if (response.ok) {
                // Update local symptom state
                if (data.extracted_symptoms) {
                    currentSessionSymptoms = data.extracted_symptoms;
                }

                if (data.status === 'diagnosed') {
                    // Apply dynamic severity theme
                    if (data.is_minor === false) {
                        document.body.classList.add('theme-severe');
                    } else {
                        document.body.classList.remove('theme-severe');
                    }

                    // Show short text
                    appendMessage(data.response, 'bot');
                    // Show detailed card
                    appendResultCard(data);
                    
                    // Handle minor disease hospital offer
                    if (data.is_minor && data.hospitals && data.hospitals.length > 0) {
                        appendMessage("This condition can usually be treated at home. If you'd like, I can still provide related hospital or clinic options nearby anyway?", 'bot');
                        showHospitalOfferButtons();
                    }

                    // Clear state for next session
                    currentSessionSymptoms = [];
                } else if (data.status === 'clarifying') {
                     // Need user to specify ambiguous symptom
                     appendMessage(data.response, 'bot');
                     chatActions.innerHTML = '';
                     data.options.forEach(opt => {
                         const btn = document.createElement('button');
                         btn.className = 'action-btn';
                         btn.innerHTML = `<i class="fa-solid fa-check"></i> ${opt}`;
                         btn.onclick = () => {
                             userInput.value = opt;
                             handleSendMessage();
                         };
                         chatActions.appendChild(btn);
                     });
                } else {
                    // Still collecting
                    appendMessage(data.response, 'bot');

                    // Show suggestions if provided
                    if (data.suggestions && data.suggestions.length > 0) {
                        showSuggestions(data.suggestions);
                    } else if (currentSessionSymptoms.length > 0) {
                        showForceDiagnoseBtn();
                    }
                }
            } else {
                const errorMsg = "Sorry, I encountered an error communicating with the server.";
                appendMessage(errorMsg, 'bot');
            }

        } catch (error) {
            console.error('Error:', error);
            const errorMsg = "Sorry, something went wrong. Please ensure the backend server is running.";
            appendMessage(errorMsg, 'bot');
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            loader.style.display = 'none';
            userInput.focus();
        }
    }

    function updateDownloadLink() {
        const btn = document.getElementById('csv-download-btn');
        const pdfBtn = document.getElementById('pdf-download-btn');
        if (userName && userAge) {
             btn.href = `/download-history?name=${userName}&age=${userAge}`;
             btn.download = `${userName}_Health_History.csv`;
             btn.style.opacity = '1';
             btn.style.pointerEvents = 'auto';
             btn.title = `Download health history CSV for ${userName}`;
             
             pdfBtn.href = `/download-pdf?name=${userName}&age=${userAge}`;
             pdfBtn.download = `${userName}_Medical_Report.pdf`;
             pdfBtn.style.opacity = '1';
             pdfBtn.style.pointerEvents = 'auto';
             pdfBtn.title = `Download professional PDF report for ${userName}`;
        } else {
             btn.href = '#';
             btn.removeAttribute('download');
             btn.style.opacity = '0.5';
             btn.style.pointerEvents = 'none';
             btn.title = "Select a user first to download history";
             
             pdfBtn.href = '#';
             pdfBtn.removeAttribute('download');
             pdfBtn.style.opacity = '0.5';
             pdfBtn.style.pointerEvents = 'none';
             pdfBtn.title = "Select a user first to download report";
        }
    }

    function showSuggestions(suggestions) {
        chatActions.innerHTML = '';
        suggestions.forEach(s => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.innerHTML = `<i class="fa-solid fa-plus"></i> ${s}`;
            btn.onclick = () => {
                userInput.value = s;
                handleSendMessage();
            };
            chatActions.appendChild(btn);
        });


        // Add the "No others" option
        const endBtn = document.createElement('button');
        endBtn.className = 'action-btn';
        endBtn.style.borderColor = 'var(--accent-green)';
        endBtn.innerHTML = '<i class="fa-solid fa-check"></i> No others';
        endBtn.onclick = () => handleSendMessage(true);
        chatActions.appendChild(endBtn);
    }

    function showForceDiagnoseBtn() {
        chatActions.innerHTML = '';
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.innerHTML = '<i class="fa-solid fa-stethoscope"></i> Diagnose Now';
        btn.onclick = () => handleSendMessage(true);
        chatActions.appendChild(btn);

        const resetBtn = document.createElement('button');
        resetBtn.className = 'action-btn';
        resetBtn.innerHTML = '<i class="fa-solid fa-rotate-left"></i> Reset';
        resetBtn.onclick = () => {
            currentSessionSymptoms = [];
            chatActions.innerHTML = '';
            appendMessage("Diagnostic session reset. Tell me your symptoms again.", 'bot');
        };
        chatActions.appendChild(resetBtn);
    }

    function showHospitalOfferButtons() {
        chatActions.innerHTML = '';
        const yesBtn = document.createElement('button');
        yesBtn.className = 'action-btn';
        yesBtn.style.borderColor = 'var(--accent-green)';
        yesBtn.innerHTML = '<i class="fa-solid fa-check"></i> Yes, show hospitals';
        yesBtn.onclick = () => {
            userInput.value = "Yes";
            handleHospitalRequest(true);
        };
        
        const noBtn = document.createElement('button');
        noBtn.className = 'action-btn';
        noBtn.style.borderColor = 'var(--accent-red)';
        noBtn.innerHTML = '<i class="fa-solid fa-xmark"></i> No, thank you';
        noBtn.onclick = () => {
            userInput.value = "No";
            handleHospitalRequest(false);
        };
        
        chatActions.appendChild(yesBtn);
        chatActions.appendChild(noBtn);
    }

    function handleHospitalRequest(show) {
        const lastMessage = userInput.value;
        appendMessage(lastMessage, 'user');
        userInput.value = '';
        chatActions.innerHTML = '';

        if (show) {
            const lastCard = chatHistory.querySelector('.result-card.hospitals-hidden');
            if (lastCard) {
                const hospSection = lastCard.querySelector('.hospitals-section');
                const pharmSection = lastCard.querySelector('.pharmacies-section');
                if (hospSection) hospSection.style.display = 'block';
                if (pharmSection) pharmSection.style.display = 'block';
                lastCard.classList.remove('hospitals-hidden');
                appendMessage("I've displayed the nearby medical facilities for you.", 'bot');
                scrollToBottom();
            }
        } else {
            appendMessage("Understood. Let me know if you need anything else!", 'bot');
        }
    }


    function appendMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');

        // Advanced Formatting
        // 1. Bold: **text** -> <strong>text</strong>
        let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // 2. Multi-line: \n -> <br>
        formattedText = formattedText.replace(/\n/g, '<br>');

        // 3. Bullet points: • text -> stylized list items
        if (formattedText.includes('•')) {
            formattedText = formattedText.replace(/• (.*?)<br>/g, '<div class="list-item"><i class="fa-solid fa-circle-dot"></i> $1</div>');
            // Handle the last bullet point if it doesn't end with <br>
            formattedText = formattedText.replace(/• (.*?)$/g, '<div class="list-item"><i class="fa-solid fa-circle-dot"></i> $1</div>');
        }

        contentDiv.innerHTML = formattedText;

        messageDiv.appendChild(contentDiv);
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function appendResultCard(data) {
        const clone = resultTemplate.content.cloneNode(true);
        const cardContainer = clone.querySelector('.result-card');
        
        // Fill Data
        clone.querySelector('.disease-name').textContent = data.disease;
        clone.querySelector('.disease-description').textContent = data.description || "No description available.";

        // Confidence Badge
        const badge = clone.querySelector('.confidence-badge');
        const percentage = Math.round(data.confidence * 100);
        badge.textContent = `${percentage}% Confidence`;

        if (percentage >= 80) badge.classList.add('high-conf');
        else if (percentage >= 50) badge.classList.add('med-conf');
        else badge.classList.add('low-conf');

        // Symptoms
        const tagsContainer = clone.querySelector('.symptom-tags');
        data.extracted_symptoms.forEach(symptom => {
            const span = document.createElement('span');
            span.classList.add('tag');
            span.textContent = symptom;
            tagsContainer.appendChild(span);
        });

        // Alternative Predictions
        if (data.top_predictions && data.top_predictions.length > 1) {
            const altSection = clone.querySelector('.alternative-predictions');
            const altList = clone.querySelector('.alt-predictions-list');
            altSection.style.display = 'block';

            // Skip the first one as it's the primary prediction
            for (let i = 1; i < data.top_predictions.length; i++) {
                const alt = data.top_predictions[i];
                const li = document.createElement('li');
                li.classList.add('clickable-alt'); // Add this class for CSS styling

                const infoDiv = document.createElement('div');
                infoDiv.style.display = 'flex';
                infoDiv.style.flexDirection = 'column';
                infoDiv.style.gap = '2px';

                const nameSpan = document.createElement('span');
                nameSpan.textContent = alt.disease;
                nameSpan.style.fontWeight = '600';

                const descP = document.createElement('p');
                descP.textContent = alt.description || "No description available.";
                descP.style.fontSize = '0.75rem';
                descP.style.color = 'var(--text-muted)';
                descP.style.fontStyle = 'italic';
                descP.style.margin = '0';
                descP.style.whiteSpace = 'nowrap';
                descP.style.overflow = 'hidden';
                descP.style.textOverflow = 'ellipsis';
                descP.style.maxWidth = '250px';

                infoDiv.appendChild(nameSpan);
                infoDiv.appendChild(descP);

                const confSpan = document.createElement('span');
                confSpan.classList.add('alt-conf');
                const altPercent = Math.round(alt.confidence * 100);
                confSpan.textContent = `${altPercent}%`;

                li.appendChild(infoDiv);
                li.appendChild(confSpan);
                
                // --- DETAILED MODAL LOGIC ---
                li.onclick = () => {
                    // Populate Modal
                    modalDiseaseName.textContent = alt.disease;
                    modalConfidence.textContent = `${altPercent}% Confidence`;
                    
                    // Set Confidence Color
                    modalConfidence.className = 'confidence-badge'; // reset
                    if (altPercent >= 80) modalConfidence.classList.add('high-conf');
                    else if (altPercent >= 50) modalConfidence.classList.add('med-conf');
                    else modalConfidence.classList.add('low-conf');

                    modalDescription.textContent = alt.description || "No description available.";
                    
                    // Populate Symptoms Tags
                    modalSymptoms.innerHTML = '';
                    if (alt.symptoms) {
                        alt.symptoms.forEach(s => {
                            const span = document.createElement('span');
                            span.classList.add('tag');
                            span.textContent = s;
                            modalSymptoms.appendChild(span);
                        });
                    }

                    // Populate Precautions
                    modalPrecautions.innerHTML = '';
                    if (alt.precautions) {
                        alt.precautions.forEach(p => {
                            const liP = document.createElement('li');
                            liP.textContent = p;
                            modalPrecautions.appendChild(liP);
                        });
                    }

                    // Show Modal
                    altModal.style.display = 'flex';
                };
                
                altList.appendChild(li);
            }
        }

        // Precautions
        const list = clone.querySelector('.precautions-list');
        data.precautions.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });

        // Handle When to see a doctor
        if (data.when_to_see_doctor && data.when_to_see_doctor.length > 0) {
            const warningSection = clone.querySelector('.warning-section');
            const warningList = clone.querySelector('.warning-list');
            warningSection.style.display = 'block';
            data.when_to_see_doctor.forEach(item => {
                const li = document.createElement('li');
                // Support bold text in warnings
                li.innerHTML = item.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                warningList.appendChild(li);
            });
        }

        // Handle Quick check
        if (data.quick_check && data.quick_check.length > 0) {
            const questionSection = clone.querySelector('.question-section');
            const questionList = clone.querySelector('.question-list');
            questionSection.style.display = 'block';
            data.quick_check.forEach(s => {
                const btn = document.createElement('button');
                btn.className = 'question-item clickable-question';
                btn.innerHTML = `<i class="fa-solid fa-plus"></i> Yes, I have ${s}`;
                btn.onclick = () => {
                    userInput.value = s;
                    handleSendMessage();
                };
                questionList.appendChild(btn);
            });
        }

        const createFacilityCard = (f) => {
            const hCard = document.createElement('div');
            hCard.className = 'h-card';
            hCard.innerHTML = `
                <div class="h-info">
                    <div class="h-type">${f.type || 'Facility'}</div>
                    <strong>${f.name}</strong>
                    <p><i class="fa-solid fa-location-dot"></i> ${f.address}</p>
                    <p><i class="fa-solid fa-phone"></i> ${f.phone}</p>
                    <span class="h-dist">${f.distance} km away</span>
                </div>
                <a href="https://www.google.com/maps/search/?api=1&query=${f.lat},${f.lon}" target="_blank" class="h-map-btn">
                    <i class="fa-solid fa-map-location-dot"></i> Maps
                </a>
            `;
            return hCard;
        };

        // Hospital Recommendations — hidden for minor diseases (no hospital needed)
        if (data.hospitals && data.hospitals.length > 0) {
            const hospSection = clone.querySelector('.hospitals-section');
            const hospCardsContainer = clone.querySelector('.hospital-cards');
            
            if (data.is_minor) {
                // Minor disease: hide hospitals, user doesn't need to go to a hospital
                hospSection.style.display = 'none';
            } else {
                hospSection.style.display = 'block';
                data.hospitals.forEach(hosp => {
                    hospCardsContainer.appendChild(createFacilityCard(hosp));
                });
            }
        }

        // Pharmacy Recommendations — ALWAYS show for both minor and serious diseases
        // For minor diseases this is the ONLY facility shown (chemist to buy medicines)
        if (data.pharmacies && data.pharmacies.length > 0) {
            const pharmSection = clone.querySelector('.pharmacies-section');
            const pharmCardsContainer = clone.querySelector('.pharmacy-cards');
            
            // Always show pharmacies — for minor diseases this is where they get their medicine
            pharmSection.style.display = 'block';

            if (data.is_minor) {
                // Add a helpful label when it's a minor disease
                const tip = document.createElement('p');
                tip.className = 'pharmacy-tip';
                tip.innerHTML = '<i class="fa-solid fa-circle-info"></i> This condition can be treated at home. Visit a nearby chemist/pharmacy to pick up medicines.';
                pharmSection.insertBefore(tip, pharmSection.querySelector('.pharmacy-cards'));
            }

            data.pharmacies.forEach(pharm => {
                pharmCardsContainer.appendChild(createFacilityCard(pharm));
            });
        }

        // Fallback: If absolutely no facilities found, show a manual search link
        if ((!data.hospitals || data.hospitals.length === 0) && (!data.pharmacies || data.pharmacies.length === 0)) {
            const hospSection = clone.querySelector('.hospitals-section');
            hospSection.style.display = 'block';
            hospSection.querySelector('h4').innerHTML = '<i class="fa-solid fa-magnifying-glass-location"></i> Find Help Nearby';
            
            const fallbackDiv = document.createElement('div');
            fallbackDiv.className = 'h-fallback';
            fallbackDiv.style.padding = '15px';
            fallbackDiv.style.background = 'rgba(255,255,255,0.05)';
            fallbackDiv.style.borderRadius = '10px';
            fallbackDiv.style.textAlign = 'center';
            
            fallbackDiv.innerHTML = `
                <p style="font-size: 0.9em; margin-bottom: 12px; color: var(--text-muted);">
                    We couldn't automatically find facilities nearby. This might be due to location settings.
                </p>
                <a href="https://www.google.com/maps/search/hospitals+and+pharmacies+near+me" target="_blank" class="h-map-btn" style="display: inline-flex; width: auto; padding: 10px 20px;">
                    <i class="fa-solid fa-map-location-dot"></i> Search on Google Maps
                </a>
            `;
            clone.querySelector('.hospital-cards').appendChild(fallbackDiv);
        }

        // Wrap in message container to align correctly
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'bot-message');
        messageDiv.style.width = '100%'; // Allow card to be wider

        // We append the card directly to chat history, but wrapped to keep flow
        chatHistory.appendChild(clone);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Request location immediately on page load
    requestUserLocation();
});
