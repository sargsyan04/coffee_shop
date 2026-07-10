const step3Form = document.getElementById("step3-form");
const resendButton = document.getElementById("resend-code");
const formStatus = document.getElementById("form-status");

step3Form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = document.getElementById("code").value;

  // TODO: когда будет готов бэкенд — заменить на реальный запрос
  // await apiRequest("/auth/verify-email", { method: "POST", body: JSON.stringify({ code }) });

  formStatus.textContent = "Email подтверждён! Перенаправляем...";
  formStatus.hidden = false;

  setTimeout(() => {
    window.location.href = "catalog.html";
  }, 1200);
});

resendButton.addEventListener("click", async () => {
  // TODO: await apiRequest("/auth/resend-code", { method: "POST" });
  formStatus.textContent = "Код отправлен повторно.";
  formStatus.hidden = false;
});