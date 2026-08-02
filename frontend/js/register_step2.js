const reactivateForm = document.getElementById("reactivate-form");
const resendButton = document.getElementById("resend-code");
const formStatus = document.getElementById("form-status");
const emailLabel = document.getElementById("user-email");

const pendingEmail = sessionStorage.getItem("pending_verification_email");

if (pendingEmail) {
  emailLabel.textContent = pendingEmail;
} else {
  window.location.href = "register.html";
}

reactivateForm.addEventListener("submit", async (event) => {
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
    formStatus.textContent = "Аккаунт восстановлен! Перенаправляем на вход...";
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
    // /user/reactivate invalidates the previous code and issues a new one —
    // no separate "resend" endpoint needed for this flow.
    await apiRequest("/user/reactivate", {
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