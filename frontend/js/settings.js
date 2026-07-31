const settingsLoading = document.getElementById("settings-loading");
const settingsContent = document.getElementById("settings-content");

const logoutButton = document.getElementById("logout-button");
const personalForm = document.getElementById("personal-form");
const passwordForm = document.getElementById("password-form");

const emailInput = document.getElementById("email");
const nameInput = document.getElementById("name");
const phoneInput = document.getElementById("phone");
const addressInput = document.getElementById("address");
const birthDateInput = document.getElementById("birth_date");

function fillPersonalForm(user) {
  emailInput.value = user.email;
  nameInput.value = user.name;
  phoneInput.value = user.phone || "";
  addressInput.value = user.address || "";
  birthDateInput.value = user.birth_date || "";
}

async function loadSettings() {
  if (!getAccessToken()) {
    window.location.href = "login.html";
    return;
  }

  try {
    // /user/status is reachable even when must_change_password is true —
    // use it first to decide whether to redirect before hitting /profile
    const userStatus = await apiRequest("/user/status");

    if (userStatus.must_change_password) {
      window.location.href = "force-password-change.html";
      return;
    }

    const user = await apiRequest("/user/profile");
    fillPersonalForm(user);

    settingsLoading.hidden = true;
    settingsContent.hidden = false;
  } catch (error) {
    clearTokens();
    window.location.href = "login.html";
  }
}

logoutButton.addEventListener("click", () => {
  clearTokens();
  window.location.href = "index.html";
});

personalForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  // Email is intentionally left out — it's locked and never sent,
  // even though the field lives in this same form
  const payload = {
    name: nameInput.value,
    phone: phoneInput.value || null,
    address: addressInput.value || null,
    birth_date: birthDateInput.value || null,
  };

  try {
    const result = await apiRequest("/user/update", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });

    showToast(result.detail || "Изменения сохранены", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
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

loadSettings();