const registerForm = document.getElementById("register-form");
const formStatus = document.getElementById("form-status");

const reactivateModalOverlay = document.getElementById("reactivate-modal-overlay");
const reactivateModalClose = document.getElementById("reactivate-modal-close");
const reactivateModalRestore = document.getElementById("reactivate-modal-restore");
const reactivateModalNew = document.getElementById("reactivate-modal-new");

// Kept around between the initial submit and whichever choice the user
// makes in the modal — both branches need the email, and "create a new
// account instead" needs to resend the whole payload with force_new set.
let lastRegisterPayload = null;

function closeReactivateModal() {
  reactivateModalOverlay.hidden = true;
}

reactivateModalClose.addEventListener("click", closeReactivateModal);
reactivateModalOverlay.addEventListener("click", (event) => {
  if (event.target === reactivateModalOverlay) closeReactivateModal();
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    name: document.getElementById("name").value,
    email: document.getElementById("email").value,
    password: document.getElementById("password").value,
    password_confirm: document.getElementById("password_confirm").value,
    birth_date: document.getElementById("birth_date").value || null,
    phone: document.getElementById("phone").value || null,
    address: document.getElementById("address").value || null,
  };

  lastRegisterPayload = payload;
  formStatus.hidden = true;

  await submitRegistration(payload);
});

async function submitRegistration(payload) {
  try {
    const user = await apiRequest("/user/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    sessionStorage.setItem("pending_verification_email", user.email);
    sessionStorage.setItem("verification_context", "registration");
    window.location.href = "register_step2.html";
  } catch (error) {
    // A deactivated account still owns this email, and the grace period
    // to restore it hasn't run out yet — offer a choice instead of just
    // showing the raw error (see detail.reactivation_available in
    // src/routers/user.py's /register).
    if (error.status === 409 && error.detail?.reactivation_available) {
      reactivateModalOverlay.hidden = false;
      return;
    }

    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
}

reactivateModalRestore.addEventListener("click", async () => {
  reactivateModalRestore.disabled = true;

  try {
    await apiRequest("/user/reactivate", {
      method: "POST",
      body: JSON.stringify({ email: lastRegisterPayload.email }),
    });

    sessionStorage.setItem("pending_verification_email", lastRegisterPayload.email);
    window.location.href = "reactivate_step2.html";
  } catch (error) {
    closeReactivateModal();
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  } finally {
    reactivateModalRestore.disabled = false;
  }
});

reactivateModalNew.addEventListener("click", async () => {
  reactivateModalNew.disabled = true;
  closeReactivateModal();

  // TODO(backend): /user/register needs to accept force_new and free up
  // the email immediately instead of returning 409 again — see the TODO
  // list for src/routers/user.py.
  await submitRegistration({ ...lastRegisterPayload, force_new: true });

  reactivateModalNew.disabled = false;
});