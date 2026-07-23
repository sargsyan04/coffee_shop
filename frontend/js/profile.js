const profileLoading = document.getElementById("profile-loading");
const profileCard = document.getElementById("profile-card");
const profileDetails = document.getElementById("profile-details");
const passwordSection = document.getElementById("password-section");
const dangerZone = document.getElementById("danger-zone");

const logoutButton = document.getElementById("logout-button");
const passwordForm = document.getElementById("password-form");
const passwordStatus = document.getElementById("password-status");
const deactivateButton = document.getElementById("deactivate-button");

function initials(name) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function renderProfile(user) {
  document.getElementById("profile-avatar").textContent = initials(user.name);
  document.getElementById("profile-name").textContent = user.name;
  document.getElementById("profile-email").textContent = user.email;

  document.getElementById("profile-role").textContent = user.role;

  const verifiedBadge = document.getElementById("profile-verified");
  if (user.is_email_verified) {
    verifiedBadge.textContent = "Email подтверждён";
    verifiedBadge.classList.remove("unverified");
  } else {
    verifiedBadge.textContent = "Email не подтверждён";
    verifiedBadge.classList.add("unverified");
  }

  document.getElementById("profile-bonus").textContent = user.bonus_points;

  document.getElementById("detail-phone").textContent = user.phone || "—";
  document.getElementById("detail-address").textContent = user.address || "—";
  document.getElementById("detail-birth-date").textContent = user.birth_date || "—";

  profileLoading.hidden = true;
  profileCard.hidden = false;
  profileDetails.hidden = false;
  passwordSection.hidden = false;
  dangerZone.hidden = false;
}

async function loadProfile() {
  if (!getAccessToken()) {
    window.location.href = "login.html";
    return;
  }

  try {
    // --> /user/status is reachable even when must_change_password is true —
    //     use it first to decide whether to redirect before hitting /profile <--
    const userStatus = await apiRequest("/user/status");

    if (userStatus.must_change_password) {
      window.location.href = "force-password-change.html";
      return;
    }

    const user = await apiRequest("/user/profile");
    renderProfile(user);
  } catch (error) {
    clearTokens();
    window.location.href = "login.html";
  }
}

logoutButton.addEventListener("click", () => {
  clearTokens();
  window.location.href = "index.html";
});

passwordForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    current_password: document.getElementById("current_password").value,
    new_password: document.getElementById("new_password").value,
    new_password_confirm: document.getElementById("new_password_confirm").value,
  };

  try {
    const result = await apiRequest("/user/change-password", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });

    showToast(result.detail || "Пароль успешно изменён", "success");
    passwordForm.reset();
  } catch (error) {
    showToast(error.message, "error");
  }
});

deactivateButton.addEventListener("click", async () => {
  const confirmed = confirm(
    "Вы уверены, что хотите деактивировать аккаунт? Его можно будет восстановить в течение 30 дней."
  );
  if (!confirmed) return;

  try {
    await apiRequest("/user/profile", { method: "DELETE" });
    clearTokens();
    setFlashMessage("Аккаунт деактивирован. Восстановить его можно в течение 30 дней.", "info");
    window.location.href = "index.html";
  } catch (error) {
    showToast(error.message, "error");
  }
});

loadProfile();