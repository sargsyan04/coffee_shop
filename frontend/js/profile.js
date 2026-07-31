const profileLoading = document.getElementById("profile-loading");
const profileCard = document.getElementById("profile-card");
const profileDetails = document.getElementById("profile-details");
const dangerZone = document.getElementById("danger-zone");

const logoutButton = document.getElementById("logout-button");
const deactivateButton = document.getElementById("deactivate-button");

const avatarButton = document.getElementById("profile-avatar-button");
const avatarInitials = document.getElementById("profile-avatar");
const avatarImage = document.getElementById("profile-avatar-image");
const avatarInput = document.getElementById("avatar-input");

const ALLOWED_AVATAR_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

function initials(name) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

// image_url comes back from the backend as a relative path (e.g. "/media/users/...")
// so it needs the API's origin in front of it to become a loadable <img src>
function resolveImageUrl(imageUrl) {
  if (!imageUrl) return "";
  return imageUrl.startsWith("http") ? imageUrl : `${API_BASE_URL}${imageUrl}`;
}

function renderAvatar(user) {
  if (user.image_url) {
    avatarImage.src = resolveImageUrl(user.image_url);
    avatarImage.hidden = false;
    avatarInitials.hidden = true;
  } else {
    avatarImage.hidden = true;
    avatarImage.src = "";
    avatarInitials.hidden = false;
    avatarInitials.textContent = initials(user.name);
  }
}

function renderProfile(user) {
  renderAvatar(user);
  document.getElementById("profile-name").textContent = user.name;
  document.getElementById("profile-email").textContent = user.email;

  document.getElementById("profile-role").textContent = user.role;

  const verifiedBadge = document.getElementById("profile-verified");
  if (user.is_email_verified) {
    verifiedBadge.textContent = "Email подтверждён";
    verifiedBadge.classList.remove("unverified");
  } else {
    verifiedBadge.textContent = "Email не подтверждён";
    verifiedBadge.classList.add("unverified");
  }

  document.getElementById("profile-bonus").textContent = user.bonus_points;

  document.getElementById("detail-phone").textContent = user.phone || "—";
  document.getElementById("detail-address").textContent = user.address || "—";
  document.getElementById("detail-birth-date").textContent = user.birth_date || "—";

  profileLoading.hidden = true;
  profileCard.hidden = false;
  profileDetails.hidden = false;
  dangerZone.hidden = false;
}

async function loadProfile() {
  if (!getAccessToken()) {
    window.location.href = "login.html";
    return;
  }

  try {
    // /user/status is reachable even when must_change_password is true —
    // use it first to decide whether to redirect before hitting /profile
    const userStatus = await apiRequest("/user/status");

    if (userStatus.must_change_password) {
      window.location.href = "force-password-change.html";
      return;
    }

    const user = await apiRequest("/user/profile");
    renderProfile(user);
  } catch (error) {
    clearTokens();
    window.location.href = "login.html";
  }
}

logoutButton.addEventListener("click", () => {
  clearTokens();
  window.location.href = "index.html";
});

deactivateButton.addEventListener("click", async () => {
  const confirmed = confirm(
    "Вы уверены, что хотите деактивировать аккаунт? Его можно будет восстановить в течение 30 дней."
  );
  if (!confirmed) return;

  try {
    await apiRequest("/user/profile", { method: "DELETE" });
    clearTokens();
    setFlashMessage("Аккаунт деактивирован. Восстановить его можно в течение 30 дней.", "info");
    window.location.href = "index.html";
  } catch (error) {
    showToast(error.message, "error");
  }
});

// ============================================================
// Avatar Upload
// ============================================================

avatarButton.addEventListener("click", () => {
  avatarInput.click();
});

// role="button" on a <div> gets no native keyboard behavior,
// so Enter/Space have to be wired up by hand for accessibility
avatarButton.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    avatarInput.click();
  }
});

avatarInput.addEventListener("change", async () => {
  const file = avatarInput.files[0];
  if (!file) return;

  if (!ALLOWED_AVATAR_TYPES.includes(file.type)) {
    showToast("Допустимые форматы: JPG, PNG, WEBP", "error");
    avatarInput.value = "";
    return;
  }

  if (file.size > MAX_AVATAR_SIZE_BYTES) {
    showToast("Файл слишком большой (максимум 5 МБ)", "error");
    avatarInput.value = "";
    return;
  }

  avatarButton.classList.add("avatar-uploading");

  try {
    const user = await apiUploadFile("/user/image", file);
    renderAvatar(user);
    showToast("Аватар обновлён", "success");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    avatarButton.classList.remove("avatar-uploading");
    avatarInput.value = "";
  }
});

loadProfile();

// ============================================================
// Tabs: Reviews / Orders
// ============================================================

const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = {
  reviews: document.getElementById("tab-panel-reviews"),
  orders: document.getElementById("tab-panel-orders"),
};

const reviewsEmpty = document.getElementById("reviews-empty");
const reviewList = document.getElementById("review-list");
const ordersEmpty = document.getElementById("orders-empty");
const orderList = document.getElementById("order-list");

let reviewsLoaded = false;
let ordersLoaded = false;

function activateTab(tabName) {
  tabButtons.forEach((button) => {
    const isActive = button.dataset.tab === tabName;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  Object.entries(tabPanels).forEach(([name, panel]) => {
    panel.hidden = name !== tabName;
  });

  if (tabName === "reviews" && !reviewsLoaded) loadReviews();
  if (tabName === "orders" && !ordersLoaded) loadOrders();
}

tabButtons.forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.tab));
});

async function loadReviews() {
  reviewsLoaded = true;
  try {
    const reviews = await apiRequest("/review/user_reviews");
    renderReviews(reviews);
  } catch (error) {
    reviewsEmpty.textContent = "Не удалось загрузить отзывы";
  }
}

function renderReviews(reviews) {
  if (!reviews.length) {
    reviewsEmpty.textContent = "Вы пока не оставили ни одного отзыва";
    return;
  }

  reviewsEmpty.hidden = true;
  reviewList.hidden = false;
  reviewList.innerHTML = "";

  reviews.forEach((review) => {
    const item = document.createElement("li");
    item.className = "review-item";

    const rating = review.rating || 0;
    item.innerHTML = `
      <div class="review-header">
        <span class="review-rating">${"★".repeat(rating)}${"☆".repeat(5 - rating)}</span>
        <span class="review-date"></span>
      </div>
      <p class="review-text"></p>
    `;
    item.querySelector(".review-date").textContent = review.created_at || "";
    item.querySelector(".review-text").textContent = review.comment || review.text || "";

    reviewList.appendChild(item);
  });
}

// These map to whatever string value OrderStatus serializes to; compared
// case-insensitively below in case the enum values aren't upper-case
const ORDER_STATUS_LABELS = {
  CREATED: "Оформляется",
  PAID: "Оплачен",
  IN_PROGRESS: "Готовится",
  READY: "Готов к выдаче",
  COMPLETED: "Выполнен",
  CANCELLED: "Отменён",
};

const NON_CANCELLABLE_STATUSES = ["COMPLETED", "CANCELLED"];

function orderStatusLabel(status) {
  return ORDER_STATUS_LABELS[String(status).toUpperCase()] || status;
}

function formatOrderDate(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return isoString;
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Keeps the last-loaded orders around so the modal (and re-render after
// a cancel) don't need a second round-trip to the backend
let ordersById = new Map();

async function loadOrders() {
  ordersLoaded = true;
  try {
    const orders = await apiRequest("/orders/");
    renderOrders(orders);
  } catch (error) {
    ordersEmpty.hidden = false;
    ordersEmpty.textContent = "Не удалось загрузить заказы";
  }
}

function renderOrders(orders) {
  ordersById = new Map(orders.map((order) => [order.id, order]));

  if (!orders.length) {
    ordersEmpty.hidden = false;
    ordersEmpty.textContent = "У вас пока нет заказов";
    orderList.hidden = true;
    return;
  }

  ordersEmpty.hidden = true;
  orderList.hidden = false;
  orderList.innerHTML = "";

  orders.forEach((order) => {
    const item = document.createElement("li");
    item.className = "order-item";

    item.innerHTML = `
      <div class="order-header">
        <span class="order-id">Заказ №${order.id}</span>
        <span class="order-date"></span>
      </div>
      <div class="order-footer">
        <span class="badge badge-role"></span>
        <span class="order-total"></span>
      </div>
      <button type="button" class="order-more-button" data-order-id="${order.id}">Подробнее</button>
    `;
    item.querySelector(".order-date").textContent = formatOrderDate(order.created_at);
    item.querySelector(".badge").textContent = orderStatusLabel(order.status);
    item.querySelector(".order-total").textContent = `${order.total_price} ₽`;

    orderList.appendChild(item);
  });
}

orderList.addEventListener("click", (event) => {
  const button = event.target.closest(".order-more-button");
  if (!button) return;

  const order = ordersById.get(Number(button.dataset.orderId));
  if (order) openOrderModal(order);
});

// ============================================================
// Order Details Modal
// ============================================================

const orderModalOverlay = document.getElementById("order-modal-overlay");
const orderModalClose = document.getElementById("order-modal-close");
const modalOrderId = document.getElementById("modal-order-id");
const modalOrderStatus = document.getElementById("modal-order-status");
const modalOrderDate = document.getElementById("modal-order-date");
const modalItemList = document.getElementById("modal-item-list");
const modalRemovedBlock = document.getElementById("modal-removed-block");
const modalRemovedList = document.getElementById("modal-removed-list");
const modalOrderTotal = document.getElementById("modal-order-total");
const modalCancelButton = document.getElementById("modal-cancel-button");

function openOrderModal(order) {
  modalOrderId.textContent = order.id;
  modalOrderStatus.textContent = orderStatusLabel(order.status);
  modalOrderDate.textContent = formatOrderDate(order.created_at);

  modalItemList.innerHTML = "";
  order.items.forEach((orderItem) => {
    const li = document.createElement("li");
    li.className = "modal-item";
    li.innerHTML = `
      <div>
        <div class="modal-item-name"></div>
        <div class="modal-item-qty"></div>
      </div>
      <span class="modal-item-price"></span>
    `;
    li.querySelector(".modal-item-name").textContent = orderItem.product_name;
    li.querySelector(".modal-item-qty").textContent = `× ${orderItem.quantity}`;
    li.querySelector(".modal-item-price").textContent = `${orderItem.line_total} ₽`;
    modalItemList.appendChild(li);
  });

  if (order.removed_items && order.removed_items.length) {
    modalRemovedBlock.hidden = false;
    modalRemovedList.innerHTML = "";
    order.removed_items.forEach((removed) => {
      const li = document.createElement("li");
      li.textContent = `${removed.product_name} — ${removed.reason}`;
      modalRemovedList.appendChild(li);
    });
  } else {
    modalRemovedBlock.hidden = true;
  }

  modalOrderTotal.textContent = `${order.total_price} ₽`;

  const isCancellable = !NON_CANCELLABLE_STATUSES.includes(String(order.status).toUpperCase());
  modalCancelButton.hidden = !isCancellable;
  modalCancelButton.dataset.orderId = order.id;

  orderModalOverlay.hidden = false;
}

function closeOrderModal() {
  orderModalOverlay.hidden = true;
}

orderModalClose.addEventListener("click", closeOrderModal);

orderModalOverlay.addEventListener("click", (event) => {
  if (event.target === orderModalOverlay) closeOrderModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !orderModalOverlay.hidden) closeOrderModal();
});

modalCancelButton.addEventListener("click", async () => {
  const orderId = modalCancelButton.dataset.orderId;
  const confirmed = confirm("Вы уверены, что хотите отменить заказ?");
  if (!confirmed) return;

  try {
    const updatedOrder = await apiRequest(`/orders/${orderId}/cancel`, { method: "POST" });
    ordersById.set(updatedOrder.id, updatedOrder);
    renderOrders(Array.from(ordersById.values()));
    openOrderModal(updatedOrder);
    showToast("Заказ отменён", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
});

// Reviews tab is active by default — load it right away instead of
// waiting for a click
loadReviews();