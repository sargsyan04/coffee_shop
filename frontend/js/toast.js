// Toast Notifications — replaces native alert() everywhere

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
  // textContent, not innerHTML, for the message itself — avoids
  // rendering any HTML that might appear in a backend error string
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

// Confirm Dialog — replaces native confirm() everywhere

// Builds a one-off .modal-overlay/.modal (same markup/classes used by the
// rest of the project's popups) and resolves true/false depending on which
// button was pressed. Any page that includes this file and one of the
// project's modal stylesheets (auth.css/profile.css/cart.css/panel.css)
// can call it without extra markup.
function confirmDialog(message, { confirmLabel = "Подтвердить", cancelLabel = "Отмена" } = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal modal-narrow" role="dialog" aria-modal="true">
        <p class="modal-text" style="margin-top: 0;"></p>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" data-action="cancel"></button>
          <button type="button" class="button_s sign_in" data-action="confirm"></button>
        </div>
      </div>
    `;
    overlay.querySelector(".modal-text").textContent = message;
    overlay.querySelector('[data-action="cancel"]').textContent = cancelLabel;
    overlay.querySelector('[data-action="confirm"]').textContent = confirmLabel;

    const finish = (result) => {
      overlay.remove();
      resolve(result);
    };

    overlay.querySelector('[data-action="cancel"]').addEventListener("click", () => finish(false));
    overlay.querySelector('[data-action="confirm"]').addEventListener("click", () => finish(true));
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) finish(false);
    });

    document.body.appendChild(overlay);
  });
}

// Flash Messages — survive a page redirect (e.g. after deactivation)

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