// Global intensity multiplier
let intensityMultiplier = 1.0;

// Initialize map centered on start point
var map = L.map('map', {
    minZoom: 6,
    maxZoom: 20
}).setView([44.428599, 26.052511], 14);

// CartoDB Dark Matter (Dark theme)
var darkTheme = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors & CartoDB',
    subdomains: 'abcd',
    maxZoom: 19
}).addTo(map);

// Esri Satellite
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
    heat.setLatLngs(scaledPoints);
});

// ✅ Încarcă markerele cu imagini
fetch('/api/potholes')
    .then(res => res.json())
    .then(data => {
        data.forEach(p => {
            const marker = L.marker([p.lat, p.lon]).addTo(map);
            const popupContent = `
                <b>Groapă detectată</b><br>
                <i>${p.timestamp}</i><br>
                <img src="${p.image}" alt="Groapă" 
                    style="width:600px; margin-top:5px; cursor:pointer;">
            `;
            marker.bindPopup(popupContent, {
                maxWidth: "auto",
                className: "big-popup"
            });
            
        });
    })
    .catch(err => {
        console.error("Eroare la încărcarea gropilor:", err);
    });

// Zoom control for heatmap and marker
map.on('zoomend', () => {
    const zoomLevel = map.getZoom();
    const scaledPoints = heatPoints.map(p => [p[0], p[1], Math.min(p[2] * intensityMultiplier, 1.0)]);

    if (zoomLevel < 10) {
        if (map.hasLayer(heat)) {
            map.removeLayer(heat);
        }
    } else {
        if (!map.hasLayer(heat)) {
            heat.setLatLngs(scaledPoints);
            heat.addTo(map);
        } else {
            heat.setLatLngs(scaledPoints);
        }
    }

    if (bumpMarker) {
        if (zoomLevel < 14 && map.hasLayer(bumpMarker)) {
            map.removeLayer(bumpMarker);
        } else if (zoomLevel >= 14 && !map.hasLayer(bumpMarker)) {
            map.addLayer(bumpMarker);
        }
    }
});
