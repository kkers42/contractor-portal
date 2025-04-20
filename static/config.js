// config.js

if (typeof window.CONFIG_LOADED === 'undefined') {
  window.CONFIG_LOADED = false;

  // Switch to true to force local even in production
  const FORCE_LOCAL = false;

  const isLocalhost = FORCE_LOCAL || window.location.hostname === "localhost" || window.location.hostname.startsWith("127.");

  const API_BASE_URL = isLocalhost
  ? "http://127.0.0.1:8000"
  : "https://contractor-portal-410182375480.us-central1.run.app";

  window.API_BASE_URL = API_BASE_URL;

  // Shared function: role-based access check
  window.checkAccess = function (allowedRoles) {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "login.html";
      return;
    }

    const payload = JSON.parse(atob(token.split(".")[1]));
    const role = payload.role;

    if (!allowedRoles.includes(role)) {
      alert("Access denied.");
      window.location.href = "login.html";
    }
  };
}
