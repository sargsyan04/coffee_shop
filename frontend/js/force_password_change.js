const forcePasswordForm = document.getElementById("force-password-form");
const formStatus = document.getElementById("form-status");

if (!getAccessToken()) {
  window.location.href = "login.html";
}

forcePasswordForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const newPassword = document.getElementById("new_password").value;
  const newPasswordConfirm = document.getElementById("new_password_confirm").value;

  formStatus.hidden = true;

  try {
    await apiRequest("/user/change-password", {
      method: "PATCH",
      body: JSON.stringify({ new_password: newPassword, new_password_confirm: newPasswordConfirm }),
    });

    if (typeof setFlashMessage === "function") {
      setFlashMessage("Пароль обновлён. Добро пожаловать!", "success");
    }

    // Route straight to the right home base for the account's role instead
    // of always landing on the customer-facing index page.
    let destination = "index.html";
    try {
      const user = await apiRequest("/user/profile");
      if (user.role === "admin") destination = "admin.html";
      else if (user.role === "barista") destination = "staff.html";
    } catch {
      // Fall back to index.html — layout.js will route correctly on load anyway.
    }

    window.location.href = destination;
  } catch (error) {
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
});