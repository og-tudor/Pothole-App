document.addEventListener("DOMContentLoaded", () => {
  let intensityMultiplier = 1.0;
  let heatPoints = [];
  let defectMarkers = [];
  let heat;

  const map = L.map("map", {
    minZoom: 6,
    maxZoom: 20
  }).setView([44.428500, 26.052373], 12);

  const darkTheme = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap contributors & CartoDB",
    subdomains: "abcd",
    maxZoom: 19
  }).addTo(map);

  const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    attribution: "Tiles © Esri, USGS, NASA",
    maxZoom: 19,
    maxNativeZoom: 18
  });

  let currentStyle = "stadia";

  document.getElementById("switchStyleBtn").addEventListener("click", () => {
    if (currentStyle === "stadia") {
      map.removeLayer(darkTheme);
      satellite.addTo(map);
      currentStyle = "esri";
    } else {
      map.removeLayer(satellite);
      darkTheme.addTo(map);
      currentStyle = "stadia";
    }
  });

  function initializeHeatLayer() {
    function waitForMapSize(attempt = 0) {
      const size = map.getSize();
      if (size.x > 0 && size.y > 0) {
        map.invalidateSize();
        heat = L.heatLayer([], {
          radius: 14,
          blur: 20,
          maxZoom: 18
        }).addTo(map);
        loadHeatData();
      } else if (attempt < 20) {
        requestAnimationFrame(() => waitForMapSize(attempt + 1));
      }
    }
    waitForMapSize();
  }

  map.whenReady(initializeHeatLayer);

  function loadHeatData() {
    fetch("/api/bumps")
      .then(res => res.json())
      .then(data => {
        heatPoints = data.map(p => [p.lat, p.lon, Math.min(p.intensity * intensityMultiplier, 1.0)]);
        heat.setLatLngs(heatPoints);
      })
      .catch(err => {
        console.error("Eroare la încărcarea denivelărilor:", err);
      });
  }

  document.getElementById("intensitySlider").addEventListener("input", (e) => {
    intensityMultiplier = parseFloat(e.target.value);
    document.getElementById("intensityValue").textContent = intensityMultiplier.toFixed(1) + "x";
    const scaledPoints = heatPoints.map(p => [p[0], p[1], Math.min(p[2] * intensityMultiplier, 1.0)]);
    if (heat) heat.setLatLngs(scaledPoints);
  });

  map.on("zoomend", () => {
    const zoomLevel = map.getZoom();
    const scaledPoints = heatPoints.map(p => [p[0], p[1], Math.min(p[2] * intensityMultiplier, 1.0)]);
    if (zoomLevel < 10) {
      if (map.hasLayer(heat)) map.removeLayer(heat);
    } else {
      if (!map.hasLayer(heat)) {
        heat.setLatLngs(scaledPoints);
        heat.addTo(map);
      } else {
        heat.setLatLngs(scaledPoints);
      }
    }
  });

  // === Sidebar toggle
  document.getElementById("settingsBtn").addEventListener("click", () => {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");
    if (sidebar.style.left === "0px") {
      sidebar.style.left = "-320px";
      overlay.style.display = "none";
    } else {
      sidebar.style.left = "0px";
      overlay.style.display = "block";
      loadImagesInSidebar();
    }
  });

  document.getElementById("overlay").addEventListener("click", () => {
    document.getElementById("sidebar").style.left = "-320px";
    document.getElementById("overlay").style.display = "none";
  });

  function formatTimestamp(raw) {
    const year = raw.substring(0, 4);
    const month = raw.substring(4, 6);
    const day = raw.substring(6, 8);
    const hour = raw.substring(9, 11);
    const minute = raw.substring(11, 13);
    const second = raw.substring(13, 15);
    return `${hour}:${minute}:${second} - ${day}/${month}/${year}`;
  }

  function loadImagesInSidebar() {
    fetch("/api/defects")
      .then(res => res.json())
      .then(data => {
        const list = document.getElementById("imageList");
        list.innerHTML = "";
        data.forEach(p => {
          const div = document.createElement("div");
          div.style.border = "1px solid #ccc";
          div.style.padding = "5px";
          div.style.marginBottom = "10px";
          const formattedTime = formatTimestamp(p.timestamp);
          div.innerHTML = `
            <img src="${p.image}" style="width:100%; border-radius:4px;">
            <p style="margin:5px 0; font-size: 13px;"><b>🕒 ${formattedTime}</b></p>
            <p style="margin:0; font-size: 12px; color: #555;">📍 ${p.lat.toFixed(6)}, ${p.lon.toFixed(6)}</p>
            <button style="background:#d9534f; color:white; border:none; padding:6px 10px; cursor:pointer; border-radius:4px; margin-top:6px;" onclick="deleteImage('${p.image}')">Reject</button>
          `;
          list.appendChild(div);
        });
      });
  }

  function deleteImage(imagePath) {
    fetch("/api/delete_image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_path: imagePath })
    })
      .then(res => res.json())
      .then(res => {
        if (res.status === "deleted") {
          alert("Imagine ștearsă!");
          loadImagesInSidebar();
          const index = defectMarkers.findIndex(m => m.imagePath === imagePath);
          if (index !== -1) {
            map.removeLayer(defectMarkers[index].marker);
            defectMarkers.splice(index, 1);
          }
        }
      })
      .catch(err => {
        console.error("Eroare la ștergere:", err);
      });
  }

  // === AwesomeMarkers integration
  const markerColors = {
    pothole: "red",
    alligator_crack: "orange",
    block_crack: "blue",
    longitudinal_crack: "purple",
    transverse_crack: "green",
    repair: "darkred",
    other_corruption: "cadetblue"
  };

  const markerIcons = {};

  function getMarkerIcon(defectType) {
    const fileMap = {
      pothole: 'red',
      alligator_crack: 'orange',
      block_crack: 'blue',
      longitudinal_crack: 'purple',
      transverse_crack: 'green',
      repair: 'yellow',
      other_corruption: 'magenta'
    };

    const color = fileMap[defectType] || 'red'; // fallback
    const path = `/static/icons/${color}-marker.png`;

    return L.icon({
      iconUrl: path,
      iconSize: [30, 42],
      iconAnchor: [15, 42],
      popupAnchor: [0, -38]
    });
  }



  fetch("/api/defects")
    .then(res => res.json())
    .then(data => {
      data.forEach(def => {
        if (!def.type || def.lat == null || def.lon == null) return;

        const icon = getMarkerIcon(def.type);
        const marker = L.marker([def.lat, def.lon], { icon }).addTo(map);

        const popup = `
          <b>${def.type.replace("_", " ").toUpperCase()}</b><br>
          <i>${formatTimestamp(def.timestamp)}</i><br>
          <img src="${def.image}" style="width: 600px; margin-top: 5px;">
        `;
        marker.bindPopup(popup);
        defectMarkers.push({ marker, imagePath: def.image });
      });
    })
    .catch(err => {
      console.error("Eroare la încărcarea defectelor:", err);
    });
});
