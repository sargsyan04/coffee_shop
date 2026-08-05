const forgotPasswordForm = document.getElementById("forgot-password-form");
const formStatus = document.getElementById("form-status");

forgotPasswordForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = document.getElementById("email").value;
  formStatus.hidden = true;

  try {
    await apiRequest("/user/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });

    // new_password.js handles both the reactivation and the
    // forgot-password code+new-password flow, see recovery_context below
    sessionStorage.setItem("pending_verification_email", email);
    sessionStorage.setItem("recovery_context", "forgot_password");
    window.location.href = "new_password.html";
  } catch (error) {
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
});
