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
    const message =
      (errorData && (errorData.detail?.message || errorData.detail)) ||
      `Request error: ${response.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
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