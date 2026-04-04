/**
 * main.js — PublicTrack frontend
 * - polished theme toggle (light/dark)
 * - search above map (nominatim)
 * - map click select + reverse geocode
 * - robust Refresh with retry behavior
 * - socket.io realtime
 */

document.addEventListener('DOMContentLoaded', () => {
  /* ---------- CONSTANTS ---------- */
  const CATEGORY_COLORS = {
    roads: '#ff7a29',    // 🟠 Orange
    water: '#36b3f6',    // 🔵 Blue
    garbage: '#9aa0a6',  // ⚪ Gray
    lighting: '#ffd34d', // 🟡 Yellow
    safety: '#ff5c5c',   // 🔴 Red
    obstructions: '#9b59b6' // 🟣 Purple
  };

  const DEFAULT = { lat: 12.9716, lng: 77.5946, zoom: 13 };
  const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search?format=json&q=';
  const DEBOUNCE_DELAY = 300;
  
  const TOUR = [
    { 
      title: 'Welcome', 
      text: 'PublicTrack helps you report local problems and see what others reported nearby.' 
    },
    { 
      title: 'Map & Colors', 
      text: `
        <div style="margin-bottom: 8px;">Dots = reported issues. Colors indicate the category:</div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
          <div><span style="color: #ff7a29">🟠</span> <b>Roads</b>: Potholes, traffic</div>
          <div><span style="color: #36b3f6">🔵</span> <b>Water</b>: Supply, flooding</div>
          <div><span style="color: #9aa0a6">⚪</span> <b>Garbage</b>: Waste, littering</div>
          <div><span style="color: #ffd34d">🟡</span> <b>Lighting</b>: Streetlights</div>
          <div><span style="color: #ff5c5c">🔴</span> <b>Safety</b>: Hazards, crime</div>
          <div><span style="color: #9b59b6">🟣</span> <b>Obstructions</b>: Blocked paths</div>
        </div>
        <div style="margin-top: 12px;">Click any dot to see details.</div>
      `
    },
    { title: 'Search & Select', text: 'Search your address or click the map. We tolerate typos & special symbols.' },
    { title: 'Filters', text: 'Use Status/Category and the radius slider to focus results.' },
    { title: 'Report', text: 'Fill Title + Description + Category and press Submit. Use location button if unsure.' },
    { title: 'Done', text: 'You are ready — explore or report. You can close the tour anytime.' }
  ];

  /* ---------- ELEMENTS ---------- */
  const loadingOverlay = document.getElementById('loading-overlay');
  const messageEl = document.getElementById('message');
  const addrInput = document.getElementById('addressInput');
  const addrClear = document.getElementById('address-clear');
  const addrSuggestions = document.getElementById('addr-suggestions');
  const addressHidden = document.getElementById('addressHidden');
  const radiusFilter = document.getElementById('radiusFilter');
  const radiusValue = document.getElementById('radiusValue');
  const applyFilters = document.getElementById('applyFilters');
  const refreshBtn = document.getElementById('refresh-data');
  const issueForm = document.getElementById('issueForm');
  const titleInput = document.getElementById('title');
  const descInput = document.getElementById('description');
  const charCounter = document.getElementById('charCounter');
  const categoryInput = document.getElementById('category');
  const clearForm = document.getElementById('clearForm');
  const startTour = document.getElementById('start-tour');
  const tourOverlay = document.getElementById('tour-overlay');
  const tourContent = document.getElementById('tour-content');
  const tourPrev = document.getElementById('tour-prev');
  const tourNext = document.getElementById('tour-next');
  const tourSkip = document.getElementById('tour-skip');
  const tourStep = document.getElementById('tour-step');
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  const locateMeBtn = document.getElementById('locate-me');
  const zoomInBtn = document.getElementById('zoom-in');
  const zoomOutBtn = document.getElementById('zoom-out');
  const statusFilter = document.getElementById('statusFilter');
  const categoryFilter = document.getElementById('categoryFilter');

  /* ---------- HELPER FUNCTIONS ---------- */
  function setLoading(show = true) {
    loadingOverlay.setAttribute('aria-hidden', show ? 'false' : 'true');
  }

  function showMessage(text, options = {}) {
    messageEl.hidden = false;
    messageEl.innerHTML = '';
    const span = document.createElement('span');
    span.textContent = text;
    messageEl.appendChild(span);

    if (options.retry && typeof options.retry === 'function') {
      const btn = document.createElement('button');
      btn.textContent = 'Retry';
      btn.className = 'btn-ghost';
      btn.style.marginLeft = '12px';
      btn.onclick = () => { options.retry(); };
      messageEl.appendChild(btn);
    }

    if (options.timeout) {
      setTimeout(() => { messageEl.hidden = true; }, options.timeout);
    }
  }

  function hideMessage() { messageEl.hidden = true; }

  function getMarkerIcon(category) {
    const color = CATEGORY_COLORS[category] || '#2ecc71';
    return L.divIcon({ 
      html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};box-shadow:0 0 0 4px rgba(0,0,0,0.06)"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });
  }

  function escapeHtml(s = '') { 
    return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); 
  }

  /* ---------- MAP INITIALIZATION ---------- */
  const map = L.map('map', { preferCanvas: true }).setView([DEFAULT.lat, DEFAULT.lng], DEFAULT.zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
    attribution: '© OpenStreetMap' 
  }).addTo(map);

  const issuesLayer = L.layerGroup().addTo(map);
  let currentSelected = null;

  function clearMarkers() { 
    issuesLayer.clearLayers(); 
    currentSelected = null; 
  }

  function addIssueMarker(issue, open = false) {
    const lat = parseFloat(issue.latitude);
    const lng = parseFloat(issue.longitude);
    if (Number.isNaN(lat) || Number.isNaN(lng)) return;
    
    const m = L.marker([lat, lng], { icon: getMarkerIcon(issue.category) });
    const title = issue.title || 'Issue';
    const html = `
      <strong>${escapeHtml(title)}</strong>
      <div class="muted" style="margin-top:6px">
        ${escapeHtml(issue.category || '')} • ${escapeHtml(issue.status || '')}
      </div>
      <p style="margin-top:8px">${escapeHtml(issue.description || '')}</p>
      <div class="small-muted" style="margin-top:6px">
        ${issue.created_at ? new Date(issue.created_at).toLocaleDateString() : ''}
      </div>
    `;
    m.bindPopup(html);
    m.addTo(issuesLayer);
    if (open) m.openPopup();
  }

  /* ---------- ENHANCED SEARCH FUNCTIONS ---------- */
  let debounceTimer;
  let currentSearchResults = [];

  async function fetchEnhancedSuggestions(query) {
    if (!query.trim()) {
      addrSuggestions.hidden = true;
      return;
    }
    
    try {
      // Enhanced search with multiple result types
      const searchUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&addressdetails=1&namedetails=1&countrycodes=in&limit=15`;
      
      const response = await fetch(searchUrl);
      const results = await response.json();
      
      currentSearchResults = results;
      addrSuggestions.innerHTML = '';
      
      if (results.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No results found. Try different keywords.';
        li.style.color = 'var(--muted)';
        li.style.fontStyle = 'italic';
        addrSuggestions.appendChild(li);
      } else {
        results.slice(0, 10).forEach((result, index) => {
          const li = document.createElement('li');
          li.setAttribute('role', 'option');
          li.setAttribute('aria-selected', 'false');
          
          // Create enhanced display text
          const displayText = createEnhancedDisplayText(result);
          li.innerHTML = displayText;
          
          li.onclick = () => selectEnhancedSuggestion(result, index);
          li.onmouseenter = () => highlightSuggestion(index);
          addrSuggestions.appendChild(li);
        });
      }
      
      addrSuggestions.hidden = results.length === 0;
    } catch (e) {
      console.error('Search failed:', e);
      addrSuggestions.hidden = true;
    }
  }

  function createEnhancedDisplayText(result) {
    const addr = result.address || {};
    const name = result.display_name;
    
    let typeIcon = '📍'; // Default icon
    let typeLabel = 'Location';
    
    // Determine type and icon
    if (result.type === 'city' || result.type === 'town' || result.type === 'village') {
      typeIcon = '🏙️';
      typeLabel = 'City/Town';
    } else if (result.type === 'road' || result.type === 'street') {
      typeIcon = '🛣️';
      typeLabel = 'Street';
    } else if (result.type === 'suburb' || result.type === 'neighborhood') {
      typeIcon = '🏘️';
      typeLabel = 'Neighborhood';
    } else if (result.type === 'state') {
      typeIcon = '🗺️';
      typeLabel = 'State';
    } else if (result.class === 'amenity') {
      typeIcon = '🏢';
      typeLabel = 'Amenity';
    } else if (result.class === 'building') {
      typeIcon = '🏠';
      typeLabel = 'Building';
    }
    
    // Create concise address
    let conciseAddress = '';
    if (addr.road) {
      conciseAddress = addr.road;
      if (addr.suburb) conciseAddress += `, ${addr.suburb}`;
      else if (addr.city) conciseAddress += `, ${addr.city}`;
    } else if (addr.city || addr.town || addr.village) {
      conciseAddress = addr.city || addr.town || addr.village;
      if (addr.state) conciseAddress += `, ${addr.state}`;
    } else if (addr.state) {
      conciseAddress = addr.state;
      if (addr.country) conciseAddress += `, ${addr.country}`;
    } else {
      conciseAddress = name.length > 60 ? name.substring(0, 60) + '...' : name;
    }
    
    return `
      <div style="display: flex; align-items: flex-start; gap: 8px;">
        <div style="font-size: 16px; margin-top: 2px;">${typeIcon}</div>
        <div style="flex: 1;">
          <div style="font-weight: 600; color: var(--text);">${conciseAddress}</div>
          <div style="font-size: 12px; color: var(--muted); margin-top: 2px;">
            ${typeLabel} • ${result.display_name.length > 80 ? result.display_name.substring(0, 80) + '...' : result.display_name}
          </div>
        </div>
      </div>
    `;
  }

  function highlightSuggestion(index) {
    // Remove highlight from all
    const allItems = addrSuggestions.querySelectorAll('li');
    allItems.forEach(item => {
      item.setAttribute('aria-selected', 'false');
      item.style.background = 'transparent';
    });
    
    // Highlight current
    if (allItems[index]) {
      allItems[index].setAttribute('aria-selected', 'true');
      allItems[index].style.background = 'linear-gradient(90deg, rgba(6,182,212,0.06), rgba(16,185,129,0.04))';
    }
  }

  function selectEnhancedSuggestion(result, index) {
    const displayText = createEnhancedDisplayText(result);
    const conciseText = result.display_name;
    
    addrInput.value = conciseText;
    addrSuggestions.hidden = true;
    
    // Set appropriate zoom level based on result type
    let zoomLevel = 16; // Default zoom
    
    if (result.type === 'country') zoomLevel = 6;
    else if (result.type === 'state') zoomLevel = 8;
    else if (result.type === 'city' || result.type === 'town') zoomLevel = 12;
    else if (result.type === 'suburb') zoomLevel = 14;
    else if (result.type === 'village') zoomLevel = 15;
    // For streets, roads, buildings keep default 16
    
    map.setView([result.lat, result.lon], zoomLevel);
    addressHidden.value = result.display_name;
    
    // Show success message
    showMessage(`📍 Located: ${conciseText}`, { timeout: 3000 });
  }

  // Enhanced keyboard navigation
  function handleSearchKeyboardNav(e) {
    const items = addrSuggestions.querySelectorAll('li');
    if (!items.length || addrSuggestions.hidden) return;
    
    const currentIndex = Array.from(items).findIndex(item => 
      item.getAttribute('aria-selected') === 'true'
    );
    
    let newIndex = currentIndex;
    
    switch(e.key) {
      case 'ArrowDown':
        e.preventDefault();
        newIndex = (currentIndex + 1) % items.length;
        break;
      case 'ArrowUp':
        e.preventDefault();
        newIndex = (currentIndex - 1 + items.length) % items.length;
        break;
      case 'Enter':
        e.preventDefault();
        if (currentIndex >= 0 && currentSearchResults[currentIndex]) {
          selectEnhancedSuggestion(currentSearchResults[currentIndex], currentIndex);
        }
        break;
      case 'Escape':
        addrSuggestions.hidden = true;
        break;
      default:
        return;
    }
    
    highlightSuggestion(newIndex);
  }

  /* ---------- DATA FETCHING ---------- */
  async function fetchIssues() {
    setLoading(true);
    try {
      const center = map.getCenter();
      const radius = radiusFilter.value;
      const status = statusFilter.value;
      const category = categoryFilter.value;
      
      const params = new URLSearchParams({
        lat: center.lat,
        lng: center.lng,
        radius: radius,
        ...(status && { status }),
        ...(category && { category })
      });
      
      const response = await fetch(`/api/issues?${params}`);
      if (!response.ok) throw new Error('Network response was not ok');
      
      const issues = await response.json();
      
      clearMarkers();
      issues.forEach(issue => addIssueMarker(issue));
      showMessage(`Loaded ${issues.length} issues`, { timeout: 2000 });
    } catch (e) {
      showMessage('Failed to load issues', { retry: fetchIssues });
      console.error('Fetch issues failed:', e);
    } finally {
      setLoading(false);
    }
  }

  /* ---------- FORM HANDLING ---------- */
  async function submitIssueForm(e) {
    e.preventDefault();
    
    if (!titleInput.value.trim() || !descInput.value.trim() || !categoryInput.value) {
      showMessage('Please fill all required fields');
      return;
    }
    
    const center = map.getCenter();
    
    try {
      setLoading(true);
      
      // FIXED: Always include status as 'reported'
      const issueData = {
        title: titleInput.value.trim(),
        description: descInput.value.trim(),
        category: categoryInput.value,
        latitude: center.lat,
        longitude: center.lng,
        status: 'reported',  // ← CRITICAL FIX: Always set status
        address: addressHidden.value || 'Map location'
      };
      
      console.log('Submitting issue data:', issueData); // Debug log
      
      const response = await fetch('/api/issues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(issueData)
      });
      
      if (response.ok) {
        const newIssue = await response.json();
        addIssueMarker(newIssue, true);
        issueForm.reset();
        charCounter.textContent = '0 / 300';
        addressHidden.value = '';
        showMessage('Issue submitted successfully!', { timeout: 3000 });
        
        // Refresh the issues list to show the new one
        setTimeout(fetchIssues, 500);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Submission failed');
      }
    } catch (e) {
      showMessage('Failed to submit issue: ' + e.message, { retry: () => issueForm.requestSubmit() });
      console.error('Submit failed:', e);
    } finally {
      setLoading(false);
    }
  }

  /* ---------- TOUR FUNCTIONS ---------- */
  let tIdx = 0;
  function openTour(i = 0) { 
    tIdx = i; 
    renderTour(); 
    tourOverlay.setAttribute('aria-hidden', 'false'); 
    tourOverlay.style.display = 'flex'; 
    document.body.style.overflow = 'hidden'; 
  }

  function closeTour() { 
    tourOverlay.setAttribute('aria-hidden', 'true'); 
    tourOverlay.style.display = 'none'; 
    document.body.style.overflow = ''; 
  }

  function renderTour() { 
    const s = TOUR[tIdx]; 
    tourContent.innerHTML = `<h4>${s.title}</h4><div>${s.text}</div>`; 
    tourStep.textContent = `${tIdx+1}/${TOUR.length}`; 
    tourPrev.disabled = tIdx === 0; 
    tourNext.textContent = (tIdx === TOUR.length-1 ? 'Finish' : 'Next'); 
  }

  /* ---------- SOCKET.IO ---------- */
  try {
    const socket = io();
    socket.on('connect', () => console.log('Socket connected:', socket.id));
    socket.on('new_issue', (issue) => { 
      addIssueMarker(issue, true); 
      showMessage('New issue posted — map updated', { timeout: 2400 }); 
    });
    socket.on('disconnect', () => console.log('Socket disconnected'));
  } catch (e) { 
    console.warn('Socket.io not available:', e); 
  }

  /* ---------- EVENT LISTENERS ---------- */
  // Theme toggle
  themeToggle?.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    themeIcon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    localStorage.setItem('theme', newTheme);
  });

  // Enhanced search functionality
  addrInput?.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fetchEnhancedSuggestions(e.target.value), DEBOUNCE_DELAY);
  });

  addrInput?.addEventListener('keydown', handleSearchKeyboardNav);

  addrInput?.addEventListener('focus', () => {
    if (currentSearchResults.length > 0) {
      addrSuggestions.hidden = false;
    }
  });

  addrClear?.addEventListener('click', () => {
    addrInput.value = '';
    addrSuggestions.hidden = true;
    addressHidden.value = '';
    currentSearchResults = [];
  });

  document.addEventListener('click', (e) => {
    if (!addrSuggestions.contains(e.target) && e.target !== addrInput) {
      addrSuggestions.hidden = true;
    }
  });

  // Map controls
  locateMeBtn?.addEventListener('click', () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          map.setView([pos.coords.latitude, pos.coords.longitude], 16);
          showMessage('Location found', { timeout: 2000 });
        },
        (err) => showMessage('Location access denied or failed')
      );
    } else {
      showMessage('Geolocation not supported by your browser');
    }
  });

  zoomInBtn?.addEventListener('click', () => map.zoomIn());
  zoomOutBtn?.addEventListener('click', () => map.zoomOut());

  // Form handling
  issueForm?.addEventListener('submit', submitIssueForm);

  descInput?.addEventListener('input', () => {
    charCounter.textContent = `${descInput.value.length} / 300`;
  });

  clearForm?.addEventListener('click', () => {
    issueForm.reset();
    charCounter.textContent = '0 / 300';
    addressHidden.value = '';
  });

  // Filters
  radiusFilter?.addEventListener('input', () => {
    radiusValue.textContent = `${radiusFilter.value} km`;
  });

  applyFilters?.addEventListener('click', fetchIssues);

  // Refresh button
  refreshBtn?.addEventListener('click', fetchIssues);

  // Tour controls
  startTour?.addEventListener('click', () => openTour(0));
  tourNext?.addEventListener('click', () => { 
    if (tIdx < TOUR.length-1) { tIdx++; renderTour(); } 
    else closeTour(); 
  });
  tourPrev?.addEventListener('click', () => { 
    if (tIdx > 0) { tIdx--; renderTour(); } 
  });
  tourSkip?.addEventListener('click', closeTour);

  // Enhanced map click handler for better reverse geocoding
  map.on('click', async (e) => {
    const { lat, lng } = e.latlng;
    
    try {
      // Show loading for reverse geocode
      showMessage('🔄 Getting address details...', { timeout: 5000 });
      
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&namedetails=1`
      );
      const data = await response.json();
      
      if (data.display_name) {
        addressHidden.value = data.display_name;
        
        // Create a nice formatted address
        const addr = data.address || {};
        let formattedAddress = '';
        
        if (addr.road) {
          formattedAddress = `${addr.road}`;
          if (addr.house_number) formattedAddress = `${addr.house_number}, ${formattedAddress}`;
          if (addr.suburb) formattedAddress += `, ${addr.suburb}`;
          else if (addr.neighbourhood) formattedAddress += `, ${addr.neighbourhood}`;
        } else if (addr.suburb || addr.neighbourhood) {
          formattedAddress = addr.suburb || addr.neighbourhood;
          if (addr.city) formattedAddress += `, ${addr.city}`;
        } else if (addr.city || addr.town || addr.village) {
          formattedAddress = addr.city || addr.town || addr.village;
        } else {
          formattedAddress = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
        }
        
        showMessage(`📍 Location selected: ${formattedAddress}`, { timeout: 4000 });
        
        // Add a temporary marker to show selected location
        if (window.selectedLocationMarker) {
          map.removeLayer(window.selectedLocationMarker);
        }
        
        window.selectedLocationMarker = L.marker([lat, lng], {
          icon: L.divIcon({
            html: '<div style="background:#06b6d4;width:20px;height:20px;border-radius:50%;border:3px solid white;box-shadow:0 2px 10px rgba(0,0,0,0.3);"></div>',
            iconSize: [26, 26],
            iconAnchor: [13, 13]
          })
        }).addTo(map);
        
        // Remove marker after 10 seconds
        setTimeout(() => {
          if (window.selectedLocationMarker) {
            map.removeLayer(window.selectedLocationMarker);
            window.selectedLocationMarker = null;
          }
        }, 10000);
      }
    } catch (error) {
      console.log('Reverse geocoding failed, using coordinates');
      addressHidden.value = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
      showMessage('📍 Location selected (coordinates only)', { timeout: 3000 });
    }
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl+Enter to submit form
    if (e.ctrlKey && e.key === 'Enter') {
      if (document.activeElement === titleInput || 
          document.activeElement === descInput || 
          document.activeElement === categoryInput) {
        issueForm.requestSubmit();
      }
    }
    
    // Escape to close suggestions or tour
    if (e.key === 'Escape') {
      if (!addrSuggestions.hidden) {
        addrSuggestions.hidden = true;
      }
      if (tourOverlay.style.display === 'flex') {
        closeTour();
      }
    }
  });

  /* ---------- INITIALIZATION ---------- */
  // Set initial theme
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  themeIcon.className = savedTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';

  // Initialize map and load data
  map.whenReady(() => { 
    setTimeout(() => { 
      setLoading(false); 
      fetchIssues(); 
    }, 600); 
  });

  // Add some sample data for testing if no issues exist
  setTimeout(() => {
    const markers = issuesLayer.getLayers();
    if (markers.length === 0) {
      showMessage('No issues found in this area. Try adjusting the radius or be the first to report!');
    }
  }, 3000);

  // Debug info
  console.log('PublicTrack initialized successfully');
  console.log('Map center:', map.getCenter());
  console.log('Available categories:', Object.keys(CATEGORY_COLORS));
});