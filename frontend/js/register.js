const registerForm = document.getElementById("register-form");
const formStatus = document.getElementById("form-status");

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

  formStatus.hidden = true;

  try {
    const user = await apiRequest("/user/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    sessionStorage.setItem("pending_verification_email", user.email);
    sessionStorage.setItem("verification_context", "registration");
    window.location.href = "register_step2.html";
  } catch (error) {
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
});