const API_BASE_URL = "http://localhost:8080";

// ============================================================
// --> Token Storage <--
// ============================================================

function getAccessToken() {
  return localStorage.getItem("access_token");
}

function getRefreshToken() {
  return localStorage.getItem("refresh_token");
}

function storeTokens({ access_token, refresh_token }) {
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// --> Turns FastAPI's "detail" field (a string, an object, or an array
//     of Pydantic validation errors) into a single readable string for the UI <--
function extractErrorMessage(errorData, status) {
  const detail = errorData?.detail;

  if (!detail) return `Request error: ${status}`;

  // --> Pydantic validation errors (422) — an array of { msg, loc, ... } objects <--
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (item.msg || "").replace(/^Value error,\s*/i, ""))
      .filter(Boolean)
      .join(" ");
  }

  // --> Custom detail as an object, e.g. { message: "...", ... } <--
  if (typeof detail === "object") {
    return detail.message || JSON.stringify(detail);
  }

  // --> Plain string <--
  return detail;
}

// ============================================================
// --> Generic JSON Requests (with automatic token refresh on 401) <--
// ============================================================

async function apiRequest(endpoint, options = {}, _isRetry = false) {
  const token = getAccessToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (response.status === 401 && !_isRetry && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiRequest(endpoint, options, true);
    }
    clearTokens();
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(errorData, response.status));
  }

  if (response.status === 204) return null;
  return response.json();
}

async function tryRefreshToken() {
  try {
    const response = await fetch(`${API_BASE_URL}/user/refresh-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: getRefreshToken() }),
    });
    if (!response.ok) return false;
    storeTokens(await response.json());
    return true;
  } catch {
    return false;
  }
}

// ============================================================
// --> Login uses OAuth2's form-urlencoded format, not JSON <--
// ============================================================

async function apiLoginRequest(email, password) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const response = await fetch(`${API_BASE_URL}/user/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Request error: ${response.status}`);
  }

  return response.json();
}