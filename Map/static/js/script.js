// Global intensity multiplier
let intensityMultiplier = 1.0;

// Initialize map centered on start point
var map = L.map('map', {
    minZoom: 6,
    maxZoom: 20
}).setView([44.074, 28.63], 14);

// CartoDB Dark Matter (Dark theme)
var darkTheme = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors & CartoDB',
    subdomains: 'abcd',
    maxZoom: 19
}).addTo(map);

// Esri Satellite (Real imagery, but limited)
var satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles © Esri, USGS, NASA',
    maxZoom: 19,
    maxNativeZoom: 18
});


let currentStyle = 'stadia';

// Switch button
document.getElementById('switchStyleBtn').addEventListener('click', () => {
    if (currentStyle === 'stadia') {
        map.removeLayer(darkTheme);
        satellite.addTo(map);
        currentStyle = 'esri';
    } else {
        map.removeLayer(satellite);
        darkTheme.addTo(map);
        currentStyle = 'stadia';
    }
});

// Heatmap layer
var heat = L.heatLayer([], {
    radius: 14,
    blur: 20,
    maxZoom: 18
}).addTo(map);

// Data storage
var heatPoints = [];
let bumpMarker = null;

// Slider logic
document.getElementById('intensitySlider').addEventListener('input', (e) => {
    intensityMultiplier = parseFloat(e.target.value);
    document.getElementById('intensityValue').textContent = intensityMultiplier.toFixed(1) + 'x';

    const scaledPoints = heatPoints.map(p => [p[0], p[1], Math.min(p[2] * intensityMultiplier, 1.0)]);

    // Always update points, even if heatmap not visible yet
    heat.setLatLngs(scaledPoints);
});


// Simulation
var startLat = 44.074, startLng = 28.63;
var endLat = 44.073, endLng = 28.62;
var steps = 50;
var latStep = (endLat - startLat) / steps;
var lngStep = (endLng - startLng) / steps;
var currentStep = 0;

var interval = setInterval(() => {
    if (currentStep > steps) {
        clearInterval(interval);
        return;
    }

    var lat = startLat + latStep * currentStep;
    var lng = startLng + lngStep * currentStep;

    // Simulate sensor
    var az = (currentStep === 5) ? 12.0 : (9.6 + Math.random() * 0.3);
    var baseIntensity = (az > 11.0) ? 1.0 : 0.3;
    var scaledIntensity = Math.min(baseIntensity * intensityMultiplier, 1.0);

    console.log(`Step ${currentStep}: lat=${lat.toFixed(6)}, lng=${lng.toFixed(6)}, az=${az.toFixed(2)}g, intensity=${scaledIntensity}`);

    // Store original intensity for future scaling
    heatPoints.push([lat, lng, baseIntensity]);

    // Add scaled point to heatmap
    heat.addLatLng([lat, lng, scaledIntensity]);

    // Add bump marker once
    if (az > 11.0 && bumpMarker === null) {
        bumpMarker = L.marker([44.07385, 28.63]).addTo(map);
        bumpMarker.bindPopup("<b>Bump Detected!</b><br><img src='static/img/bump.png' width='150'>").openPopup();
    }

    currentStep++;
}, 200);

// Zoom control for heatmap and marker
map.on('zoomend', () => {
    const zoomLevel = map.getZoom();

    // Always prepare scaled heatmap points
    const scaledPoints = heatPoints.map(p => [p[0], p[1], Math.min(p[2] * intensityMultiplier, 1.0)]);

    // Heatmap control
    if (zoomLevel < 10) {
        if (map.hasLayer(heat)) {
            map.removeLayer(heat);
        }
    } else {
        // Add heatmap back if needed
        if (!map.hasLayer(heat)) {
            heat.setLatLngs(scaledPoints);  // update data first
            heat.addTo(map);
        } else {
            heat.setLatLngs(scaledPoints);  // also update while visible (for slider changes)
        }
    }

    // Bump marker control
    if (bumpMarker) {
        if (zoomLevel < 14) {
            if (map.hasLayer(bumpMarker)) {
                map.removeLayer(bumpMarker);
            }
        } else {
            if (!map.hasLayer(bumpMarker)) {
                map.addLayer(bumpMarker);
            }
        }
    }
});


