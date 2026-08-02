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
      throw new Error(`Server error: ${response.status}`);
    }

    const product = await response.json();
    renderProduct(product);

  } catch (error) {
    container.innerHTML = `<p class="error-text">Не удалось загрузить товар: ${error.message}</p>`;
    console.error("Failed to load product:", error);
  }
}

function renderProduct(product) {
  const container = document.getElementById("product-detail");

  const imageUrl = product.image_url
    ? `${API_BASE_URL}${product.image_url}`
    : "../images/placeholder.png";

  // Description is optional — only render it if the API response includes it
  const descriptionHtml = product.description
    ? `<p class="detail-description">${escapeHtml(product.description)}</p>`
    : "";

  // Category + tags — this data is already returned by the API
  // (ProductResponse.category / ProductResponse.tags), just wasn't
  // rendered on this page before.
  const categoryHtml = product.category
    ? `<span class="detail-category">${escapeHtml(product.category.name)}</span>`
    : "";

  const tagsHtml = product.tags?.length
    ? `<div class="detail-tags">${product.tags
        .map((tag) => `<span class="detail-tag">${escapeHtml(tag.name)}</span>`)
        .join("")}</div>`
    : "";

  container.innerHTML = `
    <div class="detail-image-wrap">
      <img src="${imageUrl}" alt="${product.name}" class="detail-image">
    </div>
    <div class="detail-info">
      <p class="detail-eyebrow">О товаре</p>
      ${categoryHtml}
      <h1 class="detail-name">${product.name}</h1>
      ${renderRatingSummary(product)}
      ${descriptionHtml}
      ${tagsHtml}
      <p class="detail-price" id="detail-price"></p>
      <div class="detail-quantity">
        <button type="button" class="qty-button" id="qty-decrease" aria-label="Уменьшить количество">−</button>
        <span id="qty-value">1</span>
        <button type="button" class="qty-button" id="qty-increase" aria-label="Увеличить количество">+</button>
      </div>
      <button class="detail-add-button" type="button" id="add-to-cart-button">Добавить в корзину</button>

      ${renderAdditionalInfoAccordion(product)}
    </div>

    <div class="reviews-section">
      <h2 class="reviews-heading">
        Отзывы
        <span class="reviews-count" id="reviews-count"></span>
      </h2>
      <div id="reviews-list" class="reviews-list">
        <p class="reviews-loading-text">Загрузка отзывов...</p>
      </div>
      <div id="review-form-slot"></div>
    </div>
  `;

  document.title = `${product.name} — Coffee Shop`;
  setupAddToCart(product);
  setupAccordion();
  loadReviews(product.id);
  setupReviewForm(product.id);
}

// ============================================================
// Additional info accordion (composition, nutrition, etc.)
//
// TODO(backend): ProductResponse currently only has name / price /
// description / category / tags / image_url / rating fields — there's
// no "composition" field yet. The text below is a placeholder so the
// section isn't empty; once the field exists on the product model +
// schema, swap the hardcoded string for `product.composition` (falling
// back to hiding the accordion item if the field is empty).
// ============================================================
function renderAdditionalInfoAccordion(product) {
  const items = [
    {
      title: "Состав",
      // TODO(backend): replace with product.composition once it exists
      body: "Информация о составе появится здесь после того, как поле будет добавлено на бэкенде.",
    },
    {
      title: "Пищевая ценность",
      // TODO(backend): replace with product.nutrition once it exists
      body: "Калорийность и БЖУ будут отображаться здесь после добавления соответствующих полей.",
    },
  ];

  const itemsHtml = items
    .map(
      (item, index) => `
        <div class="accordion-item" data-index="${index}">
          <button type="button" class="accordion-trigger">
            ${escapeHtml(item.title)}
            <svg class="accordion-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <div class="accordion-panel">${escapeHtml(item.body)}</div>
        </div>
      `
    )
    .join("");

  return `<div class="detail-accordion">${itemsHtml}</div>`;
}

function setupAccordion() {
  document.querySelectorAll(".accordion-item").forEach((item) => {
    const trigger = item.querySelector(".accordion-trigger");
    trigger.addEventListener("click", () => {
      item.classList.toggle("open");
    });
  });
}

// Basic HTML-escaping for text coming from the API (description, comments) —
// it's rendered via innerHTML, so this avoids it being interpreted as markup.
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function renderStars(rating) {
  const rounded = Math.round(rating);
  let html = "";
  for (let i = 1; i <= 5; i++) {
    html += i <= rounded ? "★" : `<span class="star-empty">★</span>`;
  }
  return `<span class="stars">${html}</span>`;
}

function renderRatingSummary(product) {
  if (!product.review_count) {
    return `
      <div class="detail-rating">
        ${renderStars(0)}
        <span class="rating-count no-reviews">Пока нет отзывов</span>
      </div>
    `;
  }
  return `
    <div class="detail-rating">
      ${renderStars(product.average_rating)}
      <span class="rating-count">${product.average_rating.toFixed(1)} · ${pluralizeReviews(product.review_count)}</span>
    </div>
  `;
}

function pluralizeReviews(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  let word = "отзывов";
  if (mod10 === 1 && mod100 !== 11) word = "отзыв";
  else if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) word = "отзыва";
  return `${count} ${word}`;
}

// ============================================================
// Reviews list
// ============================================================
async function loadReviews(productId) {
  const listEl = document.getElementById("reviews-list");
  const countEl = document.getElementById("reviews-count");

  try {
    const response = await fetch(`${API_BASE_URL}/review/${productId}/product_reviews`);
    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    const reviews = await response.json();

    countEl.textContent = reviews.length ? `(${reviews.length})` : "";

    if (!reviews.length) {
      listEl.innerHTML = `<p class="reviews-empty-text">Отзывов пока нет — станьте первым, кто оставит отзыв на этот товар.</p>`;
      return;
    }

    listEl.innerHTML = reviews.map(renderReviewCard).join("");
  } catch (error) {
    listEl.innerHTML = `<p class="error-text">Не удалось загрузить отзывы: ${error.message}</p>`;
    console.error("Failed to load reviews:", error);
  }
}

function renderReviewCard(review) {
  const author = review.user?.name || "Гость";
  const initial = author.trim().charAt(0).toUpperCase() || "?";
  const avatarUrl = review.user?.image_url ? `${API_BASE_URL}${review.user.image_url}` : null;

  const avatarHtml = avatarUrl
    ? `<img src="${avatarUrl}" alt="${escapeHtml(author)}" class="review-avatar">`
    : `<span class="review-avatar-fallback">${initial}</span>`;

  const date = new Date(review.created_at).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return `
    <article class="review-card">
      <div class="review-card-header">
        <div class="review-author">
          ${avatarHtml}
          <span class="review-author-name">${escapeHtml(author)}</span>
        </div>
        <span class="review-date">${date}</span>
      </div>
      ${renderStars(review.rating)}
      <p class="review-comment">${escapeHtml(review.comment)}</p>
    </article>
  `;
}

// ============================================================
// Review form — only shown if the user is logged in, has a completed
// order containing this product, and hasn't already reviewed it
// ============================================================
async function setupReviewForm(productId) {
  const slot = document.getElementById("review-form-slot");

  if (!getAccessToken()) {
    slot.innerHTML = `<p class="review-status-text">Войдите в аккаунт, чтобы оставить отзыв.</p>`;
    return;
  }

  try {
    const eligibility = await apiRequest(`/review/${productId}/eligibility`);

    if (eligibility.already_reviewed) {
      slot.innerHTML = `<p class="review-status-text">Вы уже оставили отзыв на этот товар. Спасибо!</p>`;
      return;
    }

    if (!eligibility.can_review) {
      slot.innerHTML = `<p class="review-status-text">Оставить отзыв можно после получения заказа с этим товаром.</p>`;
      return;
    }

    renderReviewForm(slot, productId);
  } catch (error) {
    // Not fatal — the reviews list still works without the form
    console.error("Failed to check review eligibility:", error);
    slot.innerHTML = "";
  }
}

function renderReviewForm(slot, productId) {
  slot.innerHTML = `
    <div class="review-form-box">
      <p class="review-form-title">Оставить отзыв</p>
      <div class="star-input" id="star-input">
        ${[1, 2, 3, 4, 5].map((n) => `<button type="button" data-value="${n}" aria-label="${n} звёзд">★</button>`).join("")}
      </div>
      <textarea class="review-textarea" id="review-comment" placeholder="Расскажите, что понравилось (или нет)..."></textarea>
      <div>
        <button type="button" class="review-submit-button" id="review-submit-button">Отправить отзыв</button>
      </div>
    </div>
  `;

  let selectedRating = 0;
  const starButtons = slot.querySelectorAll("#star-input button");

  function paintStars(value) {
    starButtons.forEach((btn) => {
      btn.classList.toggle("active", Number(btn.dataset.value) <= value);
    });
  }

  starButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedRating = Number(btn.dataset.value);
      paintStars(selectedRating);
    });
    btn.addEventListener("mouseenter", () => paintStars(Number(btn.dataset.value)));
    btn.addEventListener("mouseleave", () => paintStars(selectedRating));
  });

  const submitButton = document.getElementById("review-submit-button");
  submitButton.addEventListener("click", async () => {
    const comment = document.getElementById("review-comment").value.trim();

    if (!selectedRating) {
      showToast("Поставьте оценку от 1 до 5 звёзд", "error");
      return;
    }
    if (!comment) {
      showToast("Напишите короткий комментарий к отзыву", "error");
      return;
    }

    submitButton.disabled = true;
    try {
      await apiRequest(`/review/${productId}`, {
        method: "POST",
        body: JSON.stringify({ rating: selectedRating, comment }),
      });
      showToast("Спасибо за отзыв!", "success");
      slot.innerHTML = `<p class="review-status-text">Вы уже оставили отзыв на этот товар. Спасибо!</p>`;
      loadReviews(productId);
    } catch (error) {
      showToast(error.message, "error");
      submitButton.disabled = false;
    }
  });
}

// ============================================================
// Add to cart — works for guests (localStorage) and logged-in users
// (real backend cart) transparently, see js/cart-store.js
// ============================================================
function setupAddToCart(product) {
  const qtyValue = document.getElementById("qty-value");
  const addButton = document.getElementById("add-to-cart-button");
  let quantity = 1;

  updatePriceDisplay(product.price, quantity);

  document.getElementById("qty-decrease").addEventListener("click", () => {
    quantity = Math.max(1, quantity - 1);
    qtyValue.textContent = quantity;
    updatePriceDisplay(product.price, quantity);
  });

  document.getElementById("qty-increase").addEventListener("click", () => {
    quantity += 1;
    qtyValue.textContent = quantity;
    updatePriceDisplay(product.price, quantity);
  });

  addButton.addEventListener("click", async () => {
    addButton.disabled = true;
    try {
      await addProductToCart(product, quantity);
      showToast(`«${product.name}» добавлен в корзину`, "success");
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      addButton.disabled = false;
    }
  });
}

// Shows the running total for the selected quantity, with a per-unit
// breakdown once more than one is selected (e.g. "5 000 ֏ (2 500 ֏ × 2)").
// unitPrice can arrive as a string from the API (Decimal serialization),
// hence the Number() conversion.
function formatAmount(amount) {
  return Number(amount).toLocaleString("ru-RU");
}

function updatePriceDisplay(unitPrice, quantity) {
  const priceEl = document.getElementById("detail-price");
  const total = Number(unitPrice) * quantity;

  if (quantity <= 1) {
    priceEl.textContent = `${formatAmount(total)} ֏`;
    return;
  }

  priceEl.innerHTML = `${formatAmount(total)} ֏ <span class="price-per-unit">(${formatAmount(unitPrice)} ֏ × ${quantity})</span>`;
}

loadProduct();