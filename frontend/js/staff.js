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
  bindQueueFilterTabs();
});

function bindQueueFilterTabs() {
  const buttons = document.querySelectorAll("#queue-filter-tabs .queue-filter-btn");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.toggle("active", b === button));
      setQueueFilter("order-queue", button.dataset.status);
    });
  });
}