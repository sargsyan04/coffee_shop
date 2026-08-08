const settingsLoading = document.getElementById("settings-loading");
const settingsContent = document.getElementById("settings-content");

const personalForm = document.getElementById("personal-form");
const passwordForm = document.getElementById("password-form");

const emailInput = document.getElementById("email");
const nameInput = document.getElementById("name");
const phoneInput = document.getElementById("phone");
const addressInput = document.getElementById("address");
const birthDateInput = document.getElementById("birth_date");

const avatarButton = document.getElementById("avatar-preview-button");
const avatarInitials = document.getElementById("avatar-preview-initials");
const avatarImage = document.getElementById("avatar-preview-image");
const avatarInput = document.getElementById("avatar-input");
const avatarUploadButton = document.getElementById("avatar-upload-button");

const ALLOWED_AVATAR_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

function initials(name) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

// image_url comes back from the backend as a relative path (e.g. "/media/users/...")
// so it needs the API's origin in front of it to become a loadable <img src>
function resolveImageUrl(imageUrl) {
  if (!imageUrl) return "";
  return imageUrl.startsWith("http") ? imageUrl : `${API_BASE_URL}${imageUrl}`;
}

function renderAvatarPreview(user) {
  if (user.image_url) {
    avatarImage.src = resolveImageUrl(user.image_url);
    avatarImage.hidden = false;
    avatarInitials.hidden = true;
  } else {
    avatarImage.hidden = true;
    avatarImage.src = "";
    avatarInitials.hidden = false;
    avatarInitials.textContent = initials(user.name);
  }
}

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
      window.location.href = "force_password_change.html";
      return;
    }

    const user = await apiRequest("/user/profile");
    fillPersonalForm(user);
    renderAvatarPreview(user);

    settingsLoading.hidden = true;
    settingsContent.hidden = false;
  } catch (error) {
    clearTokens();
    window.location.href = "login.html";
  }
}

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

// Avatar Upload

function triggerAvatarInput() {
  avatarInput.click();
}

avatarUploadButton.addEventListener("click", triggerAvatarInput);

avatarInput.addEventListener("change", async () => {
  const file = avatarInput.files[0];
  if (!file) return;

  if (!ALLOWED_AVATAR_TYPES.includes(file.type)) {
    showToast("Допустимые форматы: JPG, PNG, WEBP", "error");
    avatarInput.value = "";
    return;
  }

  if (file.size > MAX_AVATAR_SIZE_BYTES) {
    showToast("Файл слишком большой (максимум 5 МБ)", "error");
    avatarInput.value = "";
    return;
  }

  avatarButton.classList.add("avatar-uploading");
  avatarUploadButton.disabled = true;

  try {
    const user = await apiUploadFile("/user/image", file);
    renderAvatarPreview(user);
    showToast("Аватар обновлён", "success");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    avatarButton.classList.remove("avatar-uploading");
    avatarUploadButton.disabled = false;
    avatarInput.value = "";
  }
});
