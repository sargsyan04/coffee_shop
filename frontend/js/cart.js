const cartLoading = document.getElementById("cart-loading");
const cartEmpty = document.getElementById("cart-empty");
const cartLayout = document.getElementById("cart-layout");
const cartItemsList = document.getElementById("cart-items");
const cartTotalEl = document.getElementById("cart-total");
const cartGuestNote = document.getElementById("cart-guest-note");
const checkoutButton = document.getElementById("checkout-button");
const checkoutHint = document.getElementById("checkout-hint");

const guestOverlay = document.getElementById("guest-checkout-overlay");
const guestForm = document.getElementById("guest-checkout-form");
const guestStatus = document.getElementById("guest-checkout-status");

function formatPrice(amount) {
  return `${amount} ֏`;
}

function isGuest() {
  return !getAccessToken();
}

// --- Rendering --------------------------------------------------------

function renderEmpty() {
  cartLoading.hidden = true;
  cartLayout.hidden = true;
  cartEmpty.hidden = false;
}

function renderItems(items, total) {
  cartLoading.hidden = true;
  cartEmpty.hidden = true;
  cartLayout.hidden = false;

  cartItemsList.innerHTML = items.map((item) => `
    <li class="cart-item" data-product-id="${item.product_id}">
      <div class="cart-item-info">
        <span class="cart-item-name">${item.name}</span>
        <span class="cart-item-price">${formatPrice(item.price)} × ${item.quantity}</span>
      </div>
      <div class="cart-item-controls">
        <button type="button" class="qty-button" data-action="decrease" aria-label="Уменьшить количество">−</button>
        <span class="cart-item-qty">${item.quantity}</span>
        <button type="button" class="qty-button" data-action="increase" aria-label="Увеличить количество">+</button>
        <button type="button" class="cart-item-remove" data-action="remove" aria-label="Удалить">Удалить</button>
      </div>
    </li>
  `).join("");

  cartTotalEl.textContent = formatPrice(total);
  bindItemControls();
}

function bindItemControls() {
  cartItemsList.querySelectorAll(".cart-item").forEach((row) => {
    const productId = Number(row.dataset.productId);
    const currentQty = Number(row.querySelector(".cart-item-qty").textContent);

    row.querySelector('[data-action="increase"]').addEventListener("click", () => {
      updateQuantity(productId, currentQty + 1, row);
    });
    row.querySelector('[data-action="decrease"]').addEventListener("click", () => {
      updateQuantity(productId, currentQty - 1, row);
    });
    row.querySelector('[data-action="remove"]').addEventListener("click", () => {
      removeItem(productId, row);
    });
  });
}

// --- Guest cart ---------------------------------------------------------

function loadGuestCart() {
  const items = getGuestCart();
  cartGuestNote.hidden = false;

  if (items.length === 0) {
    renderEmpty();
    return;
  }
  renderItems(items, guestCartTotal());
}

// --- Backend cart (logged-in users) --------------------------------------

async function loadAccountCart() {
  cartGuestNote.hidden = true;

  try {
    const cart = await apiRequest("/cart/");
    const items = (cart.items || []).map((item) => ({
      product_id: item.product_id,
      name: item.product_name,
      price: item.unit_price,
      quantity: item.quantity,
    }));

    if (items.length === 0) {
      renderEmpty();
      return;
    }
    renderItems(items, cart.total_price);
  } catch (error) {
    renderEmpty();
    showToast(error.message, "error");
  }
}

// --- Quantity / removal ---------------------------------------------------

async function updateQuantity(productId, newQuantity, row) {
  if (newQuantity < 1) {
    return removeItem(productId, row);
  }

  if (isGuest()) {
    updateGuestCartItemQuantity(productId, newQuantity);
    loadGuestCart();
    return;
  }

  try {
    // NOTE: PATCH /cart/items/{id} is currently a 501 stub on the backend —
    // once it's implemented this will just work.
    await apiRequest(`/cart/items/${productId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity: newQuantity }),
    });
    await loadAccountCart();
    updateCartBadge();
  } catch (error) {
    showToast("Изменение количества пока не реализовано на сервере", "info");
  }
}

async function removeItem(productId, row) {
  if (isGuest()) {
    removeFromGuestCart(productId);
    loadGuestCart();
    return;
  }

  try {
    // NOTE: DELETE /cart/items/{id} is currently a 501 stub on the backend.
    await apiRequest(`/cart/items/${productId}`, { method: "DELETE" });
    await loadAccountCart();
    updateCartBadge();
  } catch (error) {
    showToast("Удаление позиции пока не реализовано на сервере", "info");
  }
}

// --- Checkout -------------------------------------------------------------

async function handleCheckout() {
  if (isGuest()) {
    guestOverlay.hidden = false;
    return;
  }

  checkoutButton.disabled = true;
  try {
    await apiRequest("/cart/checkout", { method: "POST" });
    setFlashMessage("Заказ оформлен и оплачен. Спасибо!", "success");
    window.location.href = "profile.html";
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    checkoutButton.disabled = false;
  }
}

guestOverlay.addEventListener("click", (event) => {
  if (event.target === guestOverlay) guestOverlay.hidden = true;
});
document.getElementById("guest-checkout-close").addEventListener("click", () => {
  guestOverlay.hidden = true;
});

guestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  guestStatus.hidden = true;

  const payload = {
    items: getGuestCart().map((item) => ({ product_id: item.product_id, quantity: item.quantity })),
    contact: {
      name: document.getElementById("guest-name").value,
      phone: document.getElementById("guest-phone").value,
      email: document.getElementById("guest-email").value || null,
    },
  };

  try {
    // NOTE: this endpoint is a TODO stub on the backend for now
    // (see src/routers/guest_cart.py) — it will 501 until implemented.
    await apiRequest("/cart/guest/checkout", { method: "POST", body: JSON.stringify(payload) });
    clearGuestCart();
    setFlashMessage("Заказ оформлен! Мы свяжемся с вами для подтверждения.", "success");
    window.location.href = "index.html";
  } catch (error) {
    guestStatus.textContent =
      "Оформление заказа без аккаунта пока недоступно. Пожалуйста, войдите или зарегистрируйтесь, чтобы завершить оплату — корзина сохранится.";
    guestStatus.hidden = false;
  }
});

checkoutButton.addEventListener("click", handleCheckout);

// --- Init -------------------------------------------------------------

function loadCart() {
  if (isGuest()) {
    loadGuestCart();
  } else {
    loadAccountCart();
  }
}

// Guest cart is merged into the account right after login (see
// cart-store.js) — reload once that settles so this page reflects it.
document.addEventListener("coffeeshop:auth", () => loadCart());
loadCart();
