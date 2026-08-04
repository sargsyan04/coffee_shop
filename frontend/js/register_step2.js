const verifyForm = document.getElementById("verify-form");
const resendButton = document.getElementById("resend-code");
const formStatus = document.getElementById("form-status");
const emailLabel = document.getElementById("user-email");
const stepIndicator = document.getElementById("step-indicator");
const stepEyebrow = document.getElementById("step-eyebrow");

const pendingEmail = sessionStorage.getItem("pending_verification_email");
const verificationContext = sessionStorage.getItem("verification_context"); // "registration" | "login"

if (!pendingEmail) {
  // Nothing pending — no reason to be on this page
  window.location.href = verificationContext === "login" ? "login.html" : "register.html";
} else {
  emailLabel.textContent = pendingEmail;
}

// The "step 2 of 2" framing only makes sense right after registration —
// if we got here because login said "email not confirmed", drop it.
if (verificationContext === "login") {
  stepIndicator.hidden = true;
  stepEyebrow.textContent = "Подтверждение email";
}

verifyForm.addEventListener("submit", async (event) => {
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
