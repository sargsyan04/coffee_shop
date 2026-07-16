const registerForm = document.getElementById("register-form");
const formStatus = document.getElementById("form-status");

registerForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const passwordConfirm = document.getElementById("password_confirm").value;

  if (password !== passwordConfirm) {
    formStatus.textContent = "Пароли не совпадают.";
    formStatus.hidden = false;
    return;
  }

  // --> Step 1 only collects data — the account is actually created at the
  //     end of step 2, once optional profile fields are known too <--
  sessionStorage.setItem("registration_step1", JSON.stringify({ name, email, password }));

  window.location.href = "register_step2.html";
});