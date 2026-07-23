const loginForm = document.getElementById("login-form");
const formStatus = document.getElementById("form-status");

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  formStatus.hidden = true;

  try {
    const tokens = await apiLoginRequest(email, password);
    storeTokens(tokens);
    window.location.href = "index.html";
  } catch (error) {
    if (error.message === "Email address not confirmed") {
      // --> Send the user to the same code-entry screen used during
      //     registration, but flag the context so the copy makes sense <--
      sessionStorage.setItem("pending_verification_email", email);
      sessionStorage.setItem("verification_context", "login");
      window.location.href = "register_step2.html";
      return;
    }

    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
});