function formatTimestamp(raw) {
  const year = raw.substring(0, 4);
  const month = raw.substring(4, 6);
  const day = raw.substring(6, 8);
  const hour = raw.substring(9, 11);
  const minute = raw.substring(11, 13);
  const second = raw.substring(13, 15);
  return `${hour}:${minute}:${second} - ${day}/${month}/${year}`;
}

function loadImagesInGrid() {
  const selectedType = document.getElementById("filter-type").value;

  fetch("/api/defects")
    .then(res => res.json())
    .then(data => {
      const grid = document.getElementById("image-grid");
      grid.innerHTML = "";

      data
        .filter(p => selectedType === "all" || p.type === selectedType)
        .forEach(p => {
          const div = document.createElement("div");
          div.className = "image-item";

          const timestamp = formatTimestamp(p.timestamp);
          const lat = p.lat.toFixed(6);
          const lon = p.lon.toFixed(6);
          const typeLabel = p.type.replace("_", " ");

          div.innerHTML = `
            <img src="${p.image}" alt="Defect">
            <p class="timestamp">🕒 ${timestamp}</p>
            <p class="gps">📍 ${lat}, ${lon}</p>
            <p class="type">⚠️ ${typeLabel}</p>
            <button class="btn btn-sm btn-danger mt-2 w-100" onclick="deleteImage('${p.image}')">
              🗑️ Șterge imaginea
            </button>
          `;

          grid.appendChild(div);
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
        loadImagesInGrid();
      }
    })
    .catch(err => {
      console.error("Eroare la ștergere:", err);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  if (typeof initializeThemeSwitch === 'function') {
    initializeThemeSwitch();
  }
  loadImagesInGrid();
});
