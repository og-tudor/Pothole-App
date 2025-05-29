let selectedMarker = null;
const map = L.map('map').setView([44.4268, 26.1025], 13);

const tile = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

map.on('click', function(e) {
  const { lat, lng } = e.latlng;

  if (selectedMarker) {
      map.removeLayer(selectedMarker);
  }


  selectedMarker = L.marker([lat, lng]).addTo(map);
  document.getElementById("lat").value = lat.toFixed(6);
  document.getElementById("lon").value = lng.toFixed(6);

  // Reverse geocoding
  fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`)
      .then(res => res.json())
      .then(data => {
      const address = data.display_name || '';
      document.getElementById("address").value = address;
      })
      .catch(() => {
      document.getElementById("address").value = "";
      });
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


function loadReportsList() {
  fetch("/api/reports")
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("reports-list");
      container.innerHTML = "";

      if (data.length === 0) {
        container.innerHTML = "<p class='text-muted'>Nu există rapoarte salvate.</p>";
        return;
      }

      data.forEach(report => {
        const div = document.createElement("div");
        div.className = "card mb-3 shadow-sm";
        if (report.no_detection) {
          div.style.backgroundColor = "#7c0a02"; // grena închis
          div.style.color = "white";
        }

        const timestamp = formatTimestamp(report.timestamp);
        const typeLabel = report.problem_type.replace("_", " ");
        const imgSrc = report.image_path.replace("./static", "/static");

        div.innerHTML = `
          <div class="card-header d-flex justify-content-between align-items-center"
              style="cursor:pointer;"
              data-bs-toggle="collapse"
              data-bs-target="#report-${report.id}"
              aria-expanded="false"
              aria-controls="report-${report.id}">
            <div><b>⚠️ ${typeLabel}</b> — 🕒 ${timestamp} ${report.no_detection ? '<span class="badge bg-warning text-dark">⚠️ fără detecții</span>' : ''}</div>
            <div class="text-muted small">Click pentru detalii</div>
          </div>
          <div id="report-${report.id}" class="collapse">
            <div class="card-body">
              <p><b>📍</b> ${report.address || "Adresă necunoscută"}</p>
              <p><i>${report.description || "Fără descriere"}</i></p>
              <img src="${imgSrc}" class="img-fluid mb-2 rounded" style="max-height:150px;"><br>
              <button class="btn btn-sm btn-danger" onclick="deleteReport(${report.id}, '${report.image_path}')">🗑️ Șterge</button>
            </div>
          </div>
        `;



        container.appendChild(div);
      });
    });
}


function deleteReport(id, imagePath) {
  fetch("/api/delete_report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, image_path: imagePath })
  })
    .then(res => res.json())
    .then(res => {
      if (res.status === "deleted") {
        alert("Raport șters cu succes!");
        loadReportsList();
      }
    })
    .catch(err => {
      console.error("Eroare la ștergere raport:", err);
    });
}





document.addEventListener("DOMContentLoaded", () => {
  if (typeof initializeThemeSwitch === 'function') {
    initializeThemeSwitch();
  }
  loadReportsList();

  // ✅ Afișează alert dacă parametrul `submitted=1` e prezent în URL
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("submitted") === "1") {
    alert("✅ Raportul a fost trimis cu succes! Va fi analizat în câteva secunde.");
  }
});
