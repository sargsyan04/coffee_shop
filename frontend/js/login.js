const loginForm = document.getElementById("login-form");
const formStatus = document.getElementById("form-status");

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();

  // TODO: когда будет готов бэкенд — заменить на реальный запрос
  // apiRequest("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) })
  formStatus.textContent = "Вход пока не подключён к бэкенду — это только оформление формы.";
  formStatus.hidden = false;
});