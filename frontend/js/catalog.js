let allProducts = []; // храним все загруженные товары, чтобы фильтровать на клиенте

async function loadProducts() {
  const container = document.getElementById("products-container");

  try {
    const response = await fetch(`${API_BASE_URL}/products/`);

    if (!response.ok) {
      throw new Error(`Ошибка сервера: ${response.status}`);
    }

    allProducts = await response.json();
    renderProducts(allProducts);

  } catch (error) {
    container.innerHTML = `<p class="error-text">Не удалось загрузить меню: ${error.message}</p>`;
    console.error("Ошибка загрузки товаров:", error);
  }
}

function renderProducts(products) {
  const container = document.getElementById("products-container");
  container.innerHTML = "";

  if (products.length === 0) {
    container.innerHTML = `<p class="empty-text">Ничего не нашлось. Попробуйте другой запрос.</p>`;
    return;
  }

  products.forEach((product) => {
    const card = createProductCard(product);
    container.appendChild(card);
  });
}

function createProductCard(product) {
  const card = document.createElement("div");
  card.className = "product-card";

  // если картинки нет — используем заглушку
  const imageUrl = product.image_url
    ? `${API_BASE_URL}${product.image_url}`
    : "../images/placeholder.png";

  card.innerHTML = `
    <a href="product.html?id=${product.id}" class="product-link">
      <div class="product-image-wrap">
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

// ===== Поиск (работает уже сейчас, фильтрует загруженные товары по названию) =====
function setupSearch() {
  const searchInput = document.getElementById("search-input");
  if (!searchInput) return;

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();
    const filtered = allProducts.filter((product) =>
      product.name.toLowerCase().includes(query)
    );
    renderProducts(filtered);
  });
}

// ===== Фильтр по категориям =====
// Пока просто переключает активную кнопку — реальная фильтрация
// подключится, когда в API появится поле категории.
function setupFilterChips() {
  const chips = document.querySelectorAll(".chip");

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      // TODO: когда бэкенд будет отдавать категорию товара,
      // здесь нужно фильтровать allProducts по chip.dataset.category
    });
  });
}

setupSearch();
setupFilterChips();
loadProducts();