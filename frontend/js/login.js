const loginForm = document.getElementById("login-form");
const formStatus = document.getElementById("form-status");

const reactivateModalOverlay = document.getElementById("reactivate-modal-overlay");
const reactivateModalClose = document.getElementById("reactivate-modal-close");
const reactivateModalNew = document.getElementById("reactivate-modal-new");
const reactivateModalRestore = document.getElementById("reactivate-modal-restore");
const reactivateModalText = document.getElementById("reactivate-modal-text");

let lastLoginEmail = null;

function closeReactivateModal() {
  reactivateModalOverlay.hidden = true;
}

reactivateModalClose.addEventListener("click", closeReactivateModal);
reactivateModalOverlay.addEventListener("click", (event) => {
  if (event.target === reactivateModalOverlay) closeReactivateModal();
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  lastLoginEmail = email;
  formStatus.hidden = true;

  try {
    const tokens = await apiLoginRequest(email, password);
    storeTokens(tokens);
    window.location.href = "index.html";
  } catch (error) {
    if (error.message === "Email address not confirmed") {
      // Send the user to the same code-entry screen used during
      // registration, but flag the context so the copy makes sense
      sessionStorage.setItem("pending_verification_email", email);
      sessionStorage.setItem("verification_context", "login");
      window.location.href = "register_step2.html";
      return;
    }

    // Same shape as the 409 from POST /user/register — see src/routers/user.py::login.
    // reactivation_available tells us whether the grace period to restore
    // this account is still open.
    if (error.detail?.reactivation_available !== undefined) {
      reactivateModalRestore.hidden = !error.detail.reactivation_available;
      reactivateModalText.textContent = error.detail.reactivation_available
        ? "Этот аккаунт деактивирован, но его ещё можно восстановить."
        : "Этот аккаунт деактивирован, и срок восстановления истёк. Вы можете создать новый аккаунт с этим email.";
      reactivateModalOverlay.hidden = false;
      return;
    }

    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
});

reactivateModalNew.addEventListener("click", () => {
  // register.js picks these up on load: prefills the email field and
  // marks the next registration submit as force_new
  sessionStorage.setItem("prefill_email", lastLoginEmail);
  sessionStorage.setItem("force_new_registration", "true");
  window.location.href = "register.html";
});

reactivateModalRestore.addEventListener("click", async () => {
  reactivateModalRestore.disabled = true;

  try {
    await apiRequest("/user/reactivate", {
      method: "POST",
      body: JSON.stringify({ email: lastLoginEmail }),
    });

    sessionStorage.setItem("pending_verification_email", lastLoginEmail);
    window.location.href = "reactivate_step2.html";
  } catch (error) {
    closeReactivateModal();
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  } finally {
    reactivateModalRestore.disabled = false;
  }
});