let allProducts = []; // Keeps all loaded products so we can filter them client-side

// Simple line icons for the known café categories (see src/fixtures/data.py
// for the seeded names). Anything else falls back to a plain dot — chips
// stay correct even if new categories get added on the backend later.
const CATEGORY_ICONS = {
  "Напитки": '<path d="M6 3h9l-1 8a3.5 3.5 0 0 1-3.5 3H10.5A3.5 3.5 0 0 1 7 11L6 3Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M9 17h4M11 14v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
  "Десерты": '<path d="M4 15c0-3.5 3.1-6 7-6s7 2.5 7 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M3 15h16v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M11 9V5m0 0-1.4 1.4M11 5l1.4 1.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
  "Еда": '<path d="M4 10h14M4 10a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2M4 10v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
};

const DEFAULT_ICON = '<circle cx="11" cy="11" r="3" stroke="currentColor" stroke-width="1.6"/>';

let activeCategory = "all";

async function loadProducts() {
  const container = document.getElementById("products-container");
  const [sortBy, order] = getSortSelection();

  try {
    const response = await fetch(`${API_BASE_URL}/products/?sort_by=${sortBy}&order=${order}`);

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const page = await response.json();
    allProducts = page.items;
    buildFilterChips(allProducts);
    applyFilters();

  } catch (error) {
    container.innerHTML = `<p class="error-text">Не удалось загрузить меню: ${error.message}</p>`;
    console.error("Failed to load products:", error);
  }
}

function getSortSelection() {
  const select = document.getElementById("sort-select");
  const [sortBy, order] = (select?.value || "name:asc").split(":");
  return [sortBy, order];
}

// Builds the category chip row from the categories actually present in the
// loaded menu, instead of a hardcoded (and previously mismatched) list.
function buildFilterChips(products) {
  const chipsContainer = document.getElementById("filter-chips");

  const categories = [...new Set(
    products.map((p) => p.category?.name).filter(Boolean)
  )].sort((a, b) => a.localeCompare(b, "ru"));

  const chipHtml = (label, category, isActive) => `
    <button class="chip${isActive ? " active" : ""}" data-category="${category}" type="button">
      <svg viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">${
        category === "all" ? DEFAULT_ICON : (CATEGORY_ICONS[category] || DEFAULT_ICON)
      }</svg>
      ${label}
    </button>
  `;

  chipsContainer.innerHTML =
    chipHtml("Всё", "all", activeCategory === "all") +
    categories.map((name) => chipHtml(name, name, name === activeCategory)).join("");

  chipsContainer.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      activeCategory = chip.dataset.category;
      chipsContainer.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      applyFilters();
    });
  });
}

// Combines the search query and the active category chip into one filter
// pass, so switching one never forgets the other.
function applyFilters() {
  const searchInput = document.getElementById("search-input");
  const query = (searchInput?.value || "").trim().toLowerCase();

  const filtered = allProducts.filter((product) => {
    const matchesQuery = product.name.toLowerCase().includes(query);
    const matchesCategory = activeCategory === "all" || product.category?.name === activeCategory;
    return matchesQuery && matchesCategory;
  });

  renderProducts(filtered);
  updateResultsCount(filtered.length, allProducts.length);
}

function updateResultsCount(shown, total) {
  const el = document.getElementById("results-count");
  if (!el) return;
  el.textContent = shown === total
    ? `Позиций в меню: ${total}`
    : `Показано ${shown} из ${total}`;
}

function renderProducts(products) {
  const container = document.getElementById("products-container");
  container.innerHTML = "";

  if (products.length === 0) {
    container.innerHTML = `<p class="empty-text">Ничего не нашлось. Попробуйте другой запрос или категорию.</p>`;
    return;
  }

  products.forEach((product) => {
    const card = createProductCard(product);
    container.appendChild(card);
  });

  setupAddToCartButtons(container);
}

function createProductCard(product) {
  const card = document.createElement("div");
  card.className = "product-card";
  card.dataset.productId = product.id;

  // Fall back to a placeholder image when the product has none
  const imageUrl = product.image_url
    ? `${API_BASE_URL}${product.image_url}`
    : "../images/placeholder.png";

  const categoryTagHtml = product.category
    ? `<span class="product-category-tag">${product.category.name}</span>`
    : "";

  card.innerHTML = `
    <a href="product.html?id=${product.id}" class="product-link">
      <div class="product-image-wrap">
        ${categoryTagHtml}
        <img src="${imageUrl}" alt="${product.name}" class="product-image">
      </div>
      <h3 class="product-name">${product.name}</h3>
    </a>
    <div class="product-footer">
      <span class="product-price">${product.price} ֏</span>
      <button class="add-button" type="button">В корзину</button>
    </div>
  `;

  return card;
}

// Add to cart — works for guests (localStorage) and logged-in users
// (real backend cart) transparently, see js/cart-store.js
function setupAddToCartButtons(container) {
  container.querySelectorAll(".product-card").forEach((card) => {
    const button = card.querySelector(".add-button");
    const productId = Number(card.dataset.productId);

    button.addEventListener("click", async () => {
      const product = allProducts.find((p) => p.id === productId);
      if (!product) return;

      button.disabled = true;
      try {
        await addProductToCart(product, 1);
        showToast(`«${product.name}» добавлен в корзину`, "success");
      } catch (error) {
        showToast(error.message, "error");
      } finally {
        button.disabled = false;
      }
    });
  });
}

// Search — filters loaded products by name, combined with the active chip
function setupSearch() {
  const searchInput = document.getElementById("search-input");
  if (!searchInput) return;

  searchInput.addEventListener("input", applyFilters);
}

// Sorting is resolved on the backend — changing it re-fetches the menu
// with the new sort_by/order query params instead of reordering client-side.
function setupSort() {
  const select = document.getElementById("sort-select");
  if (!select) return;

  select.addEventListener("change", loadProducts);
}

setupSearch();
setupSort();
loadProducts();
