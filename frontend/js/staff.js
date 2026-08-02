const panelGuardMessage = document.getElementById("panel-guard-message");
const panelContent = document.getElementById("panel-content");

document.addEventListener("coffeeshop:auth", (event) => {
  const { authenticated, user } = event.detail;

  if (!authenticated) {
    window.location.href = "login.html";
    return;
  }

  if (user.role !== "barista" && user.role !== "admin") {
    panelGuardMessage.hidden = false;
    return;
  }

  panelContent.hidden = false;
  loadOrderQueue("order-queue");
});
