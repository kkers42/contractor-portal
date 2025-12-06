// config.js

if (typeof window.CONFIG_LOADED === 'undefined') {
  window.CONFIG_LOADED = false;

  // Switch to true to force local even in production
  const FORCE_LOCAL = false;

  // Check if running on localhost, 127.x.x.x, or local network (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
  const hostname = window.location.hostname;
  const isLocalhost = FORCE_LOCAL ||
    hostname === "localhost" ||
    hostname.startsWith("127.") ||
    hostname.startsWith("192.168.") ||
    hostname.startsWith("10.") ||
    /^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(hostname);

  // If on local network, use the current hostname:port, otherwise use production VPS
  const API_BASE_URL = isLocalhost
  ? `http://${hostname}:8000`
  : "https://snow-contractor.com";

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

  // Get dashboard URL based on user role
  window.getDashboardUrl = function () {
    const token = localStorage.getItem("token");
    if (!token) {
      return "login.html";
    }

    const payload = JSON.parse(atob(token.split(".")[1]));
    const role = payload.role;

    switch (role) {
      case "Admin":
        return "/static/AdminDashboard.html";
      case "Manager":
        return "/static/ManagerDashboard.html";
      case "Subcontractor":
      case "User":
        return "/static/UserDashboard.html";
      default:
        return "/static/login.html";
    }
  };
}
