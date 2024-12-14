document.addEventListener('DOMContentLoaded', function() {
    // Only initialize form functionality if we're on the visit form page
    const form = document.getElementById('visitForm');
    if (!form) return; // Exit if we're not on the form page
    
    const steps = document.querySelectorAll('.form-step');
    const dots = document.querySelectorAll('.dot');
    let currentStep = 1;

    function showStep(step) {
        steps.forEach(s => s.classList.add('d-none'));
        dots.forEach(d => d.classList.remove('active'));
        
        const currentStepElement = document.querySelector(`[data-step="${step}"]`);
        currentStepElement.classList.remove('d-none');
        dots[step-1].classList.add('active');
        
        // Update navigation buttons
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const submitBtn = document.getElementById('submitBtn');
        
        if (prevBtn) prevBtn.style.display = step > 1 ? 'block' : 'none';
        if (nextBtn) nextBtn.style.display = step < steps.length ? 'block' : 'none';
        if (submitBtn) submitBtn.style.display = step === steps.length ? 'block' : 'none';
    }

    async function validateStep(step) {
        const stepElement = document.querySelector(`[data-step="${step}"]`);
        if (!stepElement) return false;
        
        const inputs = stepElement.querySelectorAll('input[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });

        return isValid;
    }

    function getCSRFToken() {
        const tokenInput = document.querySelector('input[name="csrf_token"]');
        return tokenInput ? tokenInput.value : '';
    }

    async function saveStepData(step) {
        const stepData = {};
        
        if (step === 4) {
            // Handle children data specially
            const children = [];
            const childEntries = document.querySelectorAll('.child-entry');
            
            childEntries.forEach((entry) => {
                const firstNameInput = entry.querySelector('[name="childFirstName[]"]');
                const lastNameInput = entry.querySelector('[name="childLastName[]"]');
                const dobInput = entry.querySelector('[name="childDob[]"]');
                const instructionsInput = entry.querySelector('[name="specialInstructions[]"]');
                
                if (firstNameInput && lastNameInput && dobInput) {
                    const child = {
                        firstName: firstNameInput.value,
                        lastName: lastNameInput.value,
                        dob: dobInput.value,
                        specialInstructions: instructionsInput ? instructionsInput.value : ''
                    };
                    if (child.firstName || child.lastName || child.dob) {
                        children.push(child);
                    }
                }
            });
            
            stepData.children = children;
        } else if (step === 5) {
            // Handle visit date specially
            const visitDateInput = document.getElementById('visitDate');
            if (!visitDateInput || !visitDateInput.value) {
                throw new Error('Please select a visit date');
            }
            stepData.visitDate = visitDateInput.value;
        } else {
            // Handle regular form fields
            const stepElement = document.querySelector(`[data-step="${step}"]`);
            if (!stepElement) return false;
            
            const inputs = stepElement.querySelectorAll('input, textarea');
            inputs.forEach(input => {
                if (input.id) {
                    stepData[input.id] = input.value;
                }
            });
        }

        try {
            const response = await fetch('/save_step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    step: step,
                    ...stepData
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save step data');
            }
            
            return true;
        } catch (error) {
            console.error('Error saving step data:', error);
            showMessage(error.message);
            return false;
        }
    }

    function fadeOutMessage(messageContainer) {
        if (!messageContainer) return;
        
        // Clear any existing timeouts
        if (messageContainer.fadeTimeout) {
            clearTimeout(messageContainer.fadeTimeout);
        }
        
        messageContainer.fadeTimeout = setTimeout(() => {
            // Start fade out
            messageContainer.style.opacity = '0';
            
            // After fade animation completes, hide the element
            setTimeout(() => {
                messageContainer.classList.add('d-none');
                messageContainer.innerHTML = '';
                messageContainer.style.opacity = '1';
            }, 500); // Match this with the CSS transition duration
        }, 5000);
    }

    function showMessage(message, type = 'danger') {
        const messageContainer = document.getElementById('messageContainer');
        if (!messageContainer) return;
        
        // Remove any existing alerts
        const existingAlerts = messageContainer.querySelectorAll('.alert');
        existingAlerts.forEach(alert => {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            if (bsAlert) {
                bsAlert.dispose();
            }
            alert.remove();
        });
        
        // Create a new alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        
        // Set the message and add close button
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add event listener for when alert is closed
        alertDiv.addEventListener('closed.bs.alert', function() {
            if (messageContainer.children.length === 0) {
                messageContainer.classList.add('d-none');
            }
        });
        
        // Add the alert to the container
        messageContainer.classList.remove('d-none');
        messageContainer.appendChild(alertDiv);
        
        // Initialize Bootstrap alert
        new bootstrap.Alert(alertDiv);
    }

    // Add child form functionality
    const addChildBtn = document.getElementById('addChildBtn');
    const childrenContainer = document.getElementById('childrenContainer');
    
    if (addChildBtn && childrenContainer) {
        addChildBtn.addEventListener('click', () => {
            const childCount = childrenContainer.querySelectorAll('.child-entry').length + 1;
            
            const template = `
                <div class="child-entry mb-3">
                    <h3>Child ${childCount}</h3>
                    <div class="row">
                        <div class="col-md-6">
                            <input type="text" class="form-control" name="childFirstName[]" placeholder="First Name">
                        </div>
                        <div class="col-md-6">
                            <input type="text" class="form-control" name="childLastName[]" placeholder="Last Name">
                        </div>
                        <div class="col-12 mt-2">
                            <input type="date" class="form-control" name="childDob[]" placeholder="Date of Birth">
                        </div>
                        <div class="col-12 mt-2">
                            <textarea class="form-control" name="specialInstructions[]" placeholder="Special Instructions"></textarea>
                        </div>
                        <div class="col-12 mt-2">
                            <button type="button" class="btn btn-outline-danger btn-sm remove-child">Remove</button>
                        </div>
                    </div>
                </div>
            `;
            
            childrenContainer.insertAdjacentHTML('beforeend', template);
        });

        // Handle remove child button clicks using event delegation
        childrenContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-child')) {
                const childEntry = e.target.closest('.child-entry');
                if (childEntry) {
                    childEntry.remove();
                }
            }
        });
    }

    // Navigation button event listeners
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    
    if (nextBtn) {
        nextBtn.addEventListener('click', async () => {
            if (await validateStep(currentStep) && await saveStepData(currentStep)) {
                currentStep++;
                showStep(currentStep);
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            currentStep--;
            showStep(currentStep);
        });
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('submitBtn');
        if (!submitBtn) return;

        try {
            if (!(await validateStep(currentStep))) {
                showMessage('Please fill in all required fields');
                return;
            }

            if (!(await saveStepData(currentStep))) {
                showMessage('Failed to save final step data');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Submitting...';

            const response = await fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });

            const result = await response.json();

            if (result.status === 'success') {
                showMessage(result.message, 'success');
                // Wait for message display and fade out before redirect
                setTimeout(() => {
                    window.location.href = '/';
                }, 5500);
            } else {
                showMessage(result.message || 'Failed to submit form');
            }
        } catch (error) {
            console.error('Submission error:', error);
            showMessage(error.message || 'An error occurred. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Submit';
        }
    });

    // Initialize first step
    showStep(1);
});
