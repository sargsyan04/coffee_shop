const step3Form = document.getElementById("step3-form");
const resendButton = document.getElementById("resend-code");
const formStatus = document.getElementById("form-status");
const emailLabel = document.getElementById("user-email");
const eyebrow = document.getElementById("verify-eyebrow");
const stepIndicator = document.getElementById("step-indicator");

const pendingEmail = sessionStorage.getItem("pending_verification_email");
const context = sessionStorage.getItem("verification_context");

if (pendingEmail) {
  emailLabel.textContent = pendingEmail;

  // --> Adjust the copy depending on how the user got here <--
  if (context === "login") {
    eyebrow.textContent = "Подтверждение входа";
    stepIndicator.hidden = true;
  }
} else {
  window.location.href = "register.html";
}

step3Form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = document.getElementById("code").value;

  try {
    await apiRequest("/user/verify-email", {
      method: "POST",
      body: JSON.stringify({ email: pendingEmail, code }),
    });

    sessionStorage.removeItem("pending_verification_email");
    sessionStorage.removeItem("verification_context");
    formStatus.textContent = "Email подтверждён! Перенаправляем на вход...";
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
    await apiRequest("/user/resend-code", {
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