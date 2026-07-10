const step2Form = document.getElementById("step2-form");
const skipButton = document.getElementById("skip-step2");
const formStatus = document.getElementById("form-status");

function goToStep3() {
  window.location.href = "register_step3.html";
}

step2Form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    birth_date: document.getElementById("birth_date").value || null,
    phone: document.getElementById("phone").value || null,
    address: document.getElementById("address").value || null,
  };

  // TODO: когда будет готов бэкенд — заменить на реальный запрос
  // await apiRequest("/users/me", { method: "PATCH", body: JSON.stringify(payload) });

  goToStep3();
});

skipButton.addEventListener("click", () => {
  goToStep3();
});