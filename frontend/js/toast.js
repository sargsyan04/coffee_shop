// ============================================================
// --> Toast Notifications — replaces native alert() everywhere <--
// ============================================================

function ensureToastContainer() {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  return container;
}

function showToast(message, type = "info", duration = 4000) {
  const container = ensureToastContainer();

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.setAttribute("role", "status");

  const icon = { success: "✓", error: "!", info: "i" }[type] || "i";

  toast.innerHTML = `<span class="toast-icon">${icon}</span><span class="toast-message"></span>`;
  // --> textContent, not innerHTML, for the message itself — avoids
  //     rendering any HTML that might appear in a backend error string <--
  toast.querySelector(".toast-message").textContent = message;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("toast-visible"));

  const remove = () => {
    toast.classList.remove("toast-visible");
    toast.addEventListener("transitionend", () => toast.remove(), { once: true });
  };

  const timer = setTimeout(remove, duration);
  toast.addEventListener("click", () => {
    clearTimeout(timer);
    remove();
  });
}

// ============================================================
// --> Flash Messages — survive a page redirect (e.g. after deactivation) <--
// ============================================================

function setFlashMessage(message, type = "info") {
  sessionStorage.setItem("flash_message", message);
  sessionStorage.setItem("flash_type", type);
}

function consumeFlashMessage() {
  const message = sessionStorage.getItem("flash_message");
  if (!message) return;

  const type = sessionStorage.getItem("flash_type") || "info";
  sessionStorage.removeItem("flash_message");
  sessionStorage.removeItem("flash_type");
  showToast(message, type);
}