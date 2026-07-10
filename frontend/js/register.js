const registerForm = document.getElementById("register-form");
const formStatus = document.getElementById("form-status");

registerForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const password = document.getElementById("password").value;
  const passwordConfirm = document.getElementById("password_confirm").value;

  if (password !== passwordConfirm) {
    formStatus.textContent = "Пароли не совпадают.";
    formStatus.hidden = false;
    return;
  }

  // TODO: когда будет готов бэкенд — заменить на реальный запрос
  // apiRequest("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) })
  formStatus.textContent = "Регистрация пока не подключена к бэкенду — это только оформление формы.";
  formStatus.hidden = false;
});