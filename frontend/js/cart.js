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
    <li class="cart-item" data-product-id="${item.product_id}" data-item-id="${item.item_id ?? ""}">
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
    // Backend cart endpoints address a line by its own id, not by product id
    const itemId = row.dataset.itemId ? Number(row.dataset.itemId) : null;
    const currentQty = Number(row.querySelector(".cart-item-qty").textContent);

    row.querySelector('[data-action="increase"]').addEventListener("click", () => {
      updateQuantity(productId, itemId, currentQty + 1);
    });
    row.querySelector('[data-action="decrease"]').addEventListener("click", () => {
      updateQuantity(productId, itemId, currentQty - 1);
    });
    row.querySelector('[data-action="remove"]').addEventListener("click", () => {
      removeItem(productId, itemId);
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
      item_id: item.id,
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

async function updateQuantity(productId, itemId, newQuantity) {
  if (newQuantity < 1) {
    return removeItem(productId, itemId);
  }

  if (isGuest()) {
    updateGuestCartItemQuantity(productId, newQuantity);
    loadGuestCart();
    return;
  }

  try {
    await apiRequest(`/cart/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity: newQuantity }),
    });
    await loadAccountCart();
    updateCartBadge();
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function removeItem(productId, itemId) {
  if (isGuest()) {
    removeFromGuestCart(productId);
    loadGuestCart();
    return;
  }

  try {
    await apiRequest(`/cart/items/${itemId}`, { method: "DELETE" });
    await loadAccountCart();
    updateCartBadge();
  } catch (error) {
    showToast(error.message, "error");
  }
}

// --- Checkout -------------------------------------------------------------

async function handleCheckout() {
  if (isGuest()) {
    openGuestCheckout();
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

// Guest checkout popup

const guestSubmit = document.getElementById("guest-submit");

function pluralizePositions(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} позиция`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${count} позиции`;
  return `${count} позиций`;
}

function openGuestCheckout() {
  const total = formatPrice(guestCartTotal());

  document.getElementById("guest-summary-count").textContent = `В заказе: ${pluralizePositions(getGuestCart().length)}`;
  document.getElementById("guest-summary-total").textContent = total;
  document.getElementById("guest-submit-total").textContent = total;

  guestStatus.hidden = true;
  guestOverlay.hidden = false;
  document.getElementById("guest-name").focus();
}

function closeGuestCheckout() {
  guestOverlay.hidden = true;
}

guestOverlay.addEventListener("click", (event) => {
  if (event.target === guestOverlay) closeGuestCheckout();
});
document.getElementById("guest-checkout-close").addEventListener("click", closeGuestCheckout);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !guestOverlay.hidden) closeGuestCheckout();
});

function showGuestError(message) {
  guestStatus.textContent = message;
  guestStatus.hidden = false;
}

guestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  guestStatus.hidden = true;

  const name = document.getElementById("guest-name").value.trim();
  const phone = document.getElementById("guest-phone").value.trim();
  const email = document.getElementById("guest-email").value.trim();

  if (!name || !phone) {
    showGuestError("Укажите имя и телефон — без них мы не сможем передать заказ.");
    return;
  }

  const payload = {
    items: getGuestCart().map((item) => ({ product_id: item.product_id, quantity: item.quantity })),
    contact: { name, phone, email: email || null },
  };

  // Blocks double submits — otherwise a double click creates two orders
  guestSubmit.disabled = true;

  try {
    await apiRequest("/cart/guest/checkout", { method: "POST", body: JSON.stringify(payload) });
    clearGuestCart();
    setFlashMessage("Заказ оформлен! Мы свяжемся с вами для подтверждения.", "success");
    window.location.href = "index.html";
  } catch (error) {
    showGuestError(error.message);
    guestSubmit.disabled = false;
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
