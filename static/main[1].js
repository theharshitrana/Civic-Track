document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    const map = L.map('map').setView([12.9716, 77.5946], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Marker icons
    const issueIcon = L.icon({
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
        iconSize: [32, 32],
        iconAnchor: [16, 32]
    });

    // DOM Elements
    const issueForm = document.getElementById('issueForm');
    const titleInput = document.getElementById('title');
    const descriptionInput = document.getElementById('description');
    const categorySelect = document.getElementById('category');
    const submitButton = document.getElementById('submitBtn');
    const messageDiv = document.getElementById('message');
    const statusFilter = document.getElementById('statusFilter');
    const categoryFilter = document.getElementById('categoryFilter');
    const radiusFilter = document.getElementById('radiusFilter');
    const applyFiltersBtn = document.getElementById('applyFilters');

    let currentLocation = { lat: 12.9716, lng: 77.5946 };
    let markers = [];

    // Get user location
    function getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    currentLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    map.setView([currentLocation.lat, currentLocation.lng], 14);
                    loadIssues();
                },
                error => {
                    console.error('Geolocation error:', error);
                    showMessage('Could not get your location. Using default location.', 'error');
                    loadIssues();
                }
            );
        } else {
            showMessage('Geolocation is not supported by your browser', 'error');
            loadIssues();
        }
    }

    // Load issues from API
    async function loadIssues() {
        try {
            clearMarkers();
            
            const params = new URLSearchParams({
                lat: currentLocation.lat,
                lng: currentLocation.lng,
                radius: radiusFilter.value,
                status: statusFilter.value,
                category: categoryFilter.value
            });

            const response = await fetch(`/api/issues?${params}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to load issues');
            }

            const issues = await response.json();
            
            issues.forEach(issue => {
                const marker = L.marker([issue.latitude, issue.longitude], { icon: issueIcon })
                    .bindPopup(`
                        <div class="popup-content">
                            <h3>${issue.title}</h3>
                            <p><strong>Status:</strong> ${issue.status}</p>
                            <p><strong>Category:</strong> ${issue.category}</p>
                            <p>${issue.description}</p>
                            <small>${new Date(issue.created_at).toLocaleString()}</small>
                        </div>
                    `)
                    .addTo(map);
                markers.push(marker);
            });
        } catch (error) {
            showMessage(`Error: ${error.message}`, 'error');
        }
    }

    // Clear existing markers
    function clearMarkers() {
        markers.forEach(marker => map.removeLayer(marker));
        markers = [];
    }

    // Show message to user
    function showMessage(text, type = 'error') {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }

    // Form submission
    issueForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Form validation
        if (!titleInput.value.trim()) {
            showMessage('Title is required');
            titleInput.focus();
            return;
        }
        
        if (!descriptionInput.value.trim()) {
            showMessage('Description is required');
            descriptionInput.focus();
            return;
        }
        
        if (!categorySelect.value) {
            showMessage('Please select a category');
            categorySelect.focus();
            return;
        }

        try {
            // Show loading state
            submitButton.disabled = true;
            submitButton.classList.add('button-loading');
            
            // Submit form data
            const formData = {
                title: titleInput.value,
                description: descriptionInput.value,
                category: categorySelect.value,
                latitude: currentLocation.lat,
                longitude: currentLocation.lng
            };

            const response = await fetch('/api/issues', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to report issue');
            }

            // Reset form and show success
            issueForm.reset();
            showMessage('Issue reported successfully!', 'success');
            loadIssues();
            
        } catch (error) {
            showMessage(`Error: ${error.message}`);
        } finally {
            submitButton.disabled = false;
            submitButton.classList.remove('button-loading');
        }
    });

    // Apply filters
    applyFiltersBtn.addEventListener('click', loadIssues);

    // Initialize
    getUserLocation();
});