function updateTotalReports(count) {
  document.getElementById("total-reports").textContent = count;
}

function updateTotalUsers(count) {
  document.getElementById("total-users").textContent = count;
}

function drawDefectsByMonthChart(data) {
  const grouped = {};

  data.forEach(def => {
    if (!def.timestamp || def.timestamp.length < 6) return;

    const year = def.timestamp.substring(0, 4);
    const month = def.timestamp.substring(4, 6);
    const key = `${year}-${month}`; // ex: "2025-06"
    grouped[key] = (grouped[key] || 0) + 1;
  });

  const monthNames = ["Ian", "Feb", "Mar", "Apr", "Mai", "Iun", "Iul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const rawMonths = Object.keys(grouped).sort();
  const months = rawMonths.map(m => {
    const [year, month] = m.split("-");
    return `${monthNames[parseInt(month, 10) - 1]} ${year}`;
  });

  const values = rawMonths.map(m => grouped[m]);

  const isDark = document.body.classList.contains("dark-theme");

  const layout = {
    xaxis: { title: "Lună" },
    yaxis: { title: "Număr defecte" },
    paper_bgcolor: isDark ? "#514A73" : "#ffffff",
    plot_bgcolor: isDark ? "#514A73" : "#ffffff",
    font: { color: isDark ? "white" : "black" },
    margin: { t: 30, b: 50, l: 50, r: 20 }
  };

  const chartData = [{
    x: months,
    y: values,
    type: 'bar',
    marker: {
      color: isDark ? "#CDA27E" : "#BE7462"
    }
  }];

  Plotly.newPlot("defects-by-month-chart", chartData, layout);
}



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
      drawDefectsByMonthChart(data);
    });

  fetch("/api/reports/count")
    .then(res => res.json())
    .then(data => updateTotalReports(data.count));

  fetch("/api/users/count")
    .then(res => res.json())
    .then(data => updateTotalUsers(data.count));

  window.addEventListener("themeChanged", () => {
    if (cachedDefectData.length > 0) {
      drawDefectPieChart(cachedDefectData);
      drawDefectsByMonthChart(cachedDefectData);
    }
  });
});
