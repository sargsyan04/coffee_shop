const guestActions = document.getElementById("nav-actions-guest");
const accountActions = document.getElementById("nav-actions-account");
const heroGuestActions = document.getElementById("hero-actions-guest");
const heroAccountActions = document.getElementById("hero-actions-account");
const logoutButton = document.getElementById("logout-button");

async function reflectAuthState() {
  if (!getAccessToken()) {
    return; // guest state is the default — nothing to change
  }

  try {
    await apiRequest("/user/profile");
    guestActions.hidden = true;
    accountActions.hidden = false;
    heroGuestActions.hidden = true;
    heroAccountActions.hidden = false;
  } catch {
    // token invalid/expired and refresh failed — stay in guest state
    clearTokens();
  }
}

logoutButton?.addEventListener("click", () => {
  clearTokens();
  window.location.reload();
});

reflectAuthState();