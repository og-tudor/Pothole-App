function drawDefectPieChart(data) {
  const typeCounts = {};

  data.forEach(def => {
    if (!def.type) return;
    typeCounts[def.type] = (typeCounts[def.type] || 0) + 1;
  });

  const labels = Object.keys(typeCounts).map(t => t.replace("_", " "));
  const values = Object.values(typeCounts);

  const chartData = [{
    values: values,
    labels: labels,
    type: 'pie',
    marker: {
      colors: ['#F2C94C', '#BE7462', '#6C757D', '#9B5F50', '#2D9CDB', '#27AE60']
    }
  }];

  const isDark = document.body.classList.contains("dark-theme");

  const layout = {
    title: "Defects by Type",
    paper_bgcolor: isDark ? "#514A73" : "#ffffff",
    font: { color: isDark ? "white" : "black" },
    height: 300
  };

  Plotly.newPlot("defect-type-pie", chartData, layout);
}

let cachedDefectData = [];

document.addEventListener("DOMContentLoaded", () => {
  if (typeof initializeThemeSwitch === 'function') {
    initializeThemeSwitch();
  }

  fetch("/api/defects")
    .then(res => res.json())
    .then(data => {
      cachedDefectData = data;
      drawDefectPieChart(data);
    })
    .catch(err => {
      console.error("Eroare la generarea pie chart:", err);
    });

  // Re-redesenează graficul când se schimbă tema
  window.addEventListener("themeChanged", () => {
    if (cachedDefectData.length > 0) {
      drawDefectPieChart(cachedDefectData);
    }
  });
});
