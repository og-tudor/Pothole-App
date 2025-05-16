function applyTheme(darkModeEnabled) {
  const body = document.body;
  body.classList.remove("dark-theme", "light-theme");
  body.classList.add(darkModeEnabled ? "dark-theme" : "light-theme");

  // Notificăm restul aplicației că tema s-a schimbat
  const event = new CustomEvent("themeChanged", { detail: { dark: darkModeEnabled } });
  window.dispatchEvent(event);
}

window.applyTheme = applyTheme;


function initializeThemeSwitch() {
  const darkMode = localStorage.getItem("darkModeEnabled") !== "false"; // default: dark
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
