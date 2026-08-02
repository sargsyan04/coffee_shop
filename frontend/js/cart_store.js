const GUEST_CART_KEY = "guest_cart_items";

// --- Guest cart (localStorage) -------------------------------------------

function getGuestCart() {
  try {
    const raw = localStorage.getItem(GUEST_CART_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveGuestCart(items) {
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(items));
  updateCartBadge();
}

function clearGuestCart() {
  localStorage.removeItem(GUEST_CART_KEY);
  updateCartBadge();
}

// `product` needs at least { id, name, price, image_url }
function addToGuestCart(product, quantity = 1) {
  const items = getGuestCart();
  const existing = items.find((item) => item.product_id === product.id);

  if (existing) {
    existing.quantity += quantity;
  } else {
    items.push({
      product_id: product.id,
      name: product.name,
      price: product.price,
      image_url: product.image_url || null,
      quantity,
    });
  }

  saveGuestCart(items);
  return items;
}

function updateGuestCartItemQuantity(productId, quantity) {
  let items = getGuestCart();
  if (quantity <= 0) {
    items = items.filter((item) => item.product_id !== productId);
  } else {
    const item = items.find((item) => item.product_id === productId);
    if (item) item.quantity = quantity;
  }
  saveGuestCart(items);
  return items;
}

function removeFromGuestCart(productId) {
  return updateGuestCartItemQuantity(productId, 0);
}

function guestCartCount() {
  return getGuestCart().reduce((sum, item) => sum + item.quantity, 0);
}

function guestCartTotal() {
  return getGuestCart().reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// --- Badge (header) --------------------------------------------------------

async function updateCartBadge() {
  const badge = document.getElementById("cart-badge");
  if (!badge) return;

  let count = 0;

  if (getAccessToken()) {
    try {
      const cart = await apiRequest("/cart/");
      count = (cart.items || []).reduce((sum, item) => sum + item.quantity, 0);
    } catch {
      count = 0;
    }
  } else {
    count = guestCartCount();
  }

  badge.textContent = String(count);
  badge.hidden = count === 0;
}

// --- Guest → account cart merge on login -----------------------------------

async function mergeGuestCartIntoAccount() {
  const items = getGuestCart();
  if (items.length === 0) return;

  for (const item of items) {
    try {
      await apiRequest("/cart/items", {
        method: "POST",
        body: JSON.stringify({ product_id: item.product_id, quantity: item.quantity }),
      });
    } catch {
      // Skip items the backend rejects (e.g. product removed since) and
      // keep going with the rest instead of losing the whole cart.
    }
  }

  clearGuestCart();
}

// --- Unified "add to cart" entry point used by catalog.js / product.js ----
// Works the same way regardless of auth state — guests get a localStorage
// line item, logged-in users get a real POST /cart/items call.
async function addProductToCart(product, quantity = 1) {
  if (getAccessToken()) {
    await apiRequest("/cart/items", {
      method: "POST",
      body: JSON.stringify({ product_id: product.id, quantity }),
    });
  } else {
    addToGuestCart(product, quantity);
  }
  updateCartBadge();
}

document.addEventListener("coffeeshop:auth", async (event) => {
  if (event.detail.authenticated) {
    await mergeGuestCartIntoAccount();
  }
  updateCartBadge();
});

// Header may not be mounted yet on first script execution — layout.js
// mounts it synchronously before this runs, but this call is harmless
// either way since updateCartBadge() no-ops when the badge isn't found.
updateCartBadge();
