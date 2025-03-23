function initMap() {
    const center = { lat: 45.9432, lng: 24.9668 }; // Romania example

    const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 13,
        center: center,
        mapTypeId: 'roadmap'
    });

    // Hardcoded "noisy" points
    const noiseData = [
        { location: new google.maps.LatLng(44.074, 28.63), weight: 1 }
    ];

    const heatmap = new google.maps.visualization.HeatmapLayer({
        data: noiseData,
        radius: 30  // Initial radius
    });

    heatmap.setMap(map);

    // Dynamically scale radius to maintain consistent look
    map.addListener('zoom_changed', () => {
        const zoomLevel = map.getZoom();

        // You can tweak this scaling factor
        const adjustedRadius = Math.floor(30 * Math.pow(13 / zoomLevel, 1.2)); 
        heatmap.set('radius', adjustedRadius);
    });
}
