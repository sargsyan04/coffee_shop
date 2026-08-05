const newPasswordForm = document.getElementById("new-password-form");
const resendButton = document.getElementById("resend-code");
const submitButton = document.getElementById("submit-button");
const formStatus = document.getElementById("form-status");
const emailLabel = document.getElementById("user-email");
const stepEyebrow = document.getElementById("step-eyebrow");

const pendingEmail = sessionStorage.getItem("pending_verification_email");
const recoveryContext = sessionStorage.getItem("recovery_context"); // "reactivation" | "forgot_password"

// The resend code endpoint differs: /user/reactivate only works for
// deactivated accounts, /user/forgot-password only for active ones.
// POST /user/new-password itself is generic and handles both cases.
const isForgotPassword = recoveryContext === "forgot_password";
const resendEndpoint = isForgotPassword ? "/user/forgot-password" : "/user/reactivate";

if (pendingEmail) {
  emailLabel.textContent = pendingEmail;
} else {
  // Nothing to reactivate without an email in flight — send back to login
  window.location.href = "login.html";
}

if (isForgotPassword) {
  stepEyebrow.textContent = "Восстановление пароля";
  submitButton.textContent = "Сохранить новый пароль";
}

newPasswordForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const code = document.getElementById("code").value;
  const newPassword = document.getElementById("new_password").value;
  const newPasswordConfirm = document.getElementById("new_password_confirm").value;

  if (newPassword !== newPasswordConfirm) {
    formStatus.textContent = "Пароли не совпадают.";
    formStatus.hidden = false;
    return;
  }

  try {
    await apiRequest("/user/new-password", {
      method: "POST",
      body: JSON.stringify({ email: pendingEmail, code, new_password: newPassword }),
    });

    sessionStorage.removeItem("pending_verification_email");
    sessionStorage.removeItem("recovery_context");
    formStatus.textContent = isForgotPassword
      ? "Пароль обновлён! Перенаправляем на вход..."
      : "Аккаунт восстановлен! Перенаправляем на вход...";
    formStatus.hidden = false;

    setTimeout(() => {
      window.location.href = "login.html";
    }, 1200);
  } catch (error) {
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
});

resendButton.addEventListener("click", async () => {
  try {
    // Both endpoints invalidate the previous code and issue a new one —
    // no separate "resend" endpoint needed for either flow.
    await apiRequest(resendEndpoint, {
      method: "POST",
      body: JSON.stringify({ email: pendingEmail }),
    });
    formStatus.textContent = "Код отправлен повторно.";
    formStatus.hidden = false;
  } catch (error) {
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
});
