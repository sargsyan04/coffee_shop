async function loadProduct() {
  const container = document.getElementById("product-detail");
  const productId = new URLSearchParams(window.location.search).get("id");

  if (!productId) {
    container.innerHTML = `<p class="error-text">Товар не указан. Вернитесь в меню и выберите товар.</p>`;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/products/${productId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Такой товар не найден");
      }
      throw new Error(`Ошибка сервера: ${response.status}`);
    }

    const product = await response.json();
    renderProduct(product);

  } catch (error) {
    container.innerHTML = `<p class="error-text">Не удалось загрузить товар: ${error.message}</p>`;
    console.error("Ошибка загрузки товара:", error);
  }
}

function renderProduct(product) {
  const container = document.getElementById("product-detail");

  const imageUrl = product.image_url
    ? `${API_BASE_URL}${product.image_url}`
    : "../images/placeholder.png";

  // описание — необязательное поле, показываем только если оно есть в ответе API
  const descriptionHtml = product.description
    ? `<p class="detail-description">${product.description}</p>`
    : "";

  container.innerHTML = `
    <div class="detail-image-wrap">
      <img src="${imageUrl}" alt="${product.name}" class="detail-image">
    </div>
    <div class="detail-info">
      <p class="detail-eyebrow">О товаре</p>
      <h1 class="detail-name">${product.name}</h1>
      ${descriptionHtml}
      <p class="detail-price">${product.price} ֏</p>
      <button class="detail-add-button" type="button">Добавить в корзину</button>
    </div>
  `;

  document.title = `${product.name} — Coffee Shop`;
}

loadProduct();