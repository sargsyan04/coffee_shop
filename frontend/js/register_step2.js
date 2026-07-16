const step2Form = document.getElementById("step2-form");
const skipButton = document.getElementById("skip-step2");
const formStatus = document.getElementById("form-status");

async function submitRegistration(extraFields) {
  const step1Raw = sessionStorage.getItem("registration_step1");
  if (!step1Raw) {
    window.location.href = "register.html";
    return;
  }

  const step1 = JSON.parse(step1Raw);
  const payload = { ...step1, ...extraFields };

  try {
    const user = await apiRequest("/user/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    sessionStorage.setItem("pending_verification_email", user.email);
    sessionStorage.removeItem("registration_step1");
    sessionStorage.setItem("verification_context", "registration");
    window.location.href = "register_step3.html";
  } catch (error) {
    formStatus.textContent = error.message;
    formStatus.hidden = false;
  }
}

step2Form.addEventListener("submit", (event) => {
  event.preventDefault();

  submitRegistration({
    birth_date: document.getElementById("birth_date").value || null,
    phone: document.getElementById("phone").value || null,
    address: document.getElementById("address").value || null,
  });
});

skipButton.addEventListener("click", () => {
  submitRegistration({ birth_date: null, phone: null, address: null });
});