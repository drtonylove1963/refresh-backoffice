document.addEventListener('DOMContentLoaded', function() {
    const syncForm = document.querySelector('.sync-form');
    const syncProgress = document.querySelector('.sync-progress');
    const progressBar = document.querySelector('.progress-bar');
    const syncStatus = document.querySelector('.sync-status');

    if (syncForm) {
        syncForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show progress bar
            syncProgress.style.display = 'block';
            progressBar.style.width = '0%';
            syncStatus.textContent = 'Starting sync...';

            // Get the CSRF token from the form
            const csrfToken = syncForm.querySelector('[name=csrf_token]').value;

            // Submit form via AJAX
            fetch(syncForm.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Update progress to 100%
                progressBar.style.width = '100%';
                syncStatus.textContent = `Sync complete: ${data.created} created, ${data.updated} updated, ${data.errors} errors`;
                
                // Hide progress after 3 seconds and reload
                setTimeout(() => {
                    syncProgress.style.display = 'none';
                    window.location.reload();
                }, 3000);
            })
            .catch(error => {
                console.error('Error:', error);
                syncStatus.textContent = 'Error during sync';
                progressBar.classList.add('bg-danger');
                
                // Hide progress after 3 seconds
                setTimeout(() => {
                    syncProgress.style.display = 'none';
                }, 3000);
            });

            // Simulate progress until we get the response
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 5;
                if (progress > 90) {
                    clearInterval(progressInterval);
                    return;
                }
                progressBar.style.width = `${progress}%`;
            }, 200);
        });
    }
});
