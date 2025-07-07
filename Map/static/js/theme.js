function applyTheme(darkModeEnabled) {
  const body = document.body;
  body.classList.remove("dark-theme", "light-theme");
  body.classList.add(darkModeEnabled ? "dark-theme" : "light-theme");

  // Notify the rest of the application about the theme change
  const event = new CustomEvent("themeChanged", { detail: { dark: darkModeEnabled } });
  window.dispatchEvent(event);
}

window.applyTheme = applyTheme;


function initializeThemeSwitch() {
  // default dark mode
  const darkMode = localStorage.getItem("darkModeEnabled") !== "false";
  const switchEl = document.getElementById("darkModeSwitch");
  if (switchEl) switchEl.checked = darkMode;
  applyTheme(darkMode);

  const saveBtn = document.getElementById("saveSettingsBtn");
  if (saveBtn) {
    saveBtn.addEventListener("click", function () {
      const darkMode = switchEl.checked;
      localStorage.setItem("darkModeEnabled", darkMode);
      applyTheme(darkMode);
      const modal = bootstrap.Modal.getInstance(document.getElementById("settingsModal"));
      modal.hide();
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const tabButtons = document.querySelectorAll(".report-text");
  const currentPath = window.location.pathname;

  tabButtons.forEach(btn => {
    const parentLink = btn.closest("a");
    if (!parentLink) return;

    const linkHref = new URL(parentLink.href, window.location.origin).pathname;

    if (linkHref === currentPath) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
});
