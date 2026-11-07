async function loadProduct() {
  const container = document.getElementById("product-detail");
  const productId = new URLSearchParams(window.location.search).get("id");

  if (!productId) {
    container.innerHTML = `<p class="error-text">No product specified. Go back to the menu and choose a product.</p>`;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/products/${productId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Product not found");
      }
      throw new Error(`Server error: ${response.status}`);
    }

    const product = await response.json();
    renderProduct(product);

  } catch (error) {
    container.innerHTML = `<p class="error-text">Could not load the product: ${error.message}</p>`;
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

  extendBreadcrumb(product);

  container.innerHTML = `
    <div class="detail-gallery">
      <div class="detail-image-wrap">
        <img src="${imageUrl}" alt="${product.name}" class="detail-image">
      </div>
    </div>
    <div class="detail-main">
      <div class="detail-info">
        ${categoryHtml}
        <h1 class="detail-name">${product.name}</h1>
        ${renderRatingSummary(product)}
        ${descriptionHtml}
        ${tagsHtml}
        <p class="detail-price" id="detail-price"></p>
        <div class="detail-quantity">
          <button type="button" class="qty-button" id="qty-decrease" aria-label="Decrease quantity">−</button>
          <span id="qty-value">1</span>
          <button type="button" class="qty-button" id="qty-increase" aria-label="Increase quantity">+</button>
        </div>
        <button class="detail-add-button" type="button" id="add-to-cart-button">Add to cart</button>
      </div>

      <div class="reviews-section">
        <h2 class="reviews-heading">
          Reviews
          <span class="reviews-count" id="reviews-count"></span>
        </h2>
        <div id="reviews-list" class="reviews-list">
          <p class="reviews-loading-text">Loading reviews...</p>
        </div>
        <div id="review-form-slot"></div>
      </div>
    </div>
  `;

  document.title = `${product.name} — Coffee Shop`;
  setupAddToCart(product);
  loadReviews(product.id);
  setupReviewForm(product.id);
}

// Adds the category and product name as extra crumbs after "Menu" —
// the first crumb is already in the page shell (product.html) since it
// doesn't depend on the fetched product.
function extendBreadcrumb(product) {
  const nav = document.getElementById("breadcrumb");
  if (!nav) return;

  const categoryCrumb = product.category
    ? `<span class="breadcrumb-sep" aria-hidden="true">/</span><span class="breadcrumb-current">${escapeHtml(product.category.name)}</span>`
    : "";

  nav.innerHTML = `
    <a href="catalog.html" class="breadcrumb-link">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      Menu
    </a>
    ${categoryCrumb}
  `;
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
        <span class="rating-count no-reviews">No reviews yet</span>
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
  return `${count} ${count === 1 ? "review" : "reviews"}`;
}

// Reviews list
async function loadReviews(productId) {
  const listEl = document.getElementById("reviews-list");
  const countEl = document.getElementById("reviews-count");

  try {
    const response = await fetch(`${API_BASE_URL}/review/${productId}/product_reviews`);
    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    const reviews = await response.json();

    countEl.textContent = reviews.length ? `(${reviews.length})` : "";

    if (!reviews.length) {
      listEl.innerHTML = `<p class="reviews-empty-text">No reviews yet — be the first to review this product.</p>`;
      return;
    }

    listEl.innerHTML = reviews.map(renderReviewCard).join("");
  } catch (error) {
    listEl.innerHTML = `<p class="error-text">Could not load reviews: ${error.message}</p>`;
    console.error("Failed to load reviews:", error);
  }
}

function renderReviewCard(review) {
  const author = review.user?.name || "Guest";
  const initial = author.trim().charAt(0).toUpperCase() || "?";
  const avatarUrl = review.user?.image_url ? `${API_BASE_URL}${review.user.image_url}` : null;

  const avatarHtml = avatarUrl
    ? `<img src="${avatarUrl}" alt="${escapeHtml(author)}" class="review-avatar">`
    : `<span class="review-avatar-fallback">${initial}</span>`;

  const date = new Date(review.created_at).toLocaleDateString("en-US", {
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

// Review form — only shown if the user is logged in, has a completed
// order containing this product, and hasn't already reviewed it
async function setupReviewForm(productId) {
  const slot = document.getElementById("review-form-slot");

  if (!getAccessToken()) {
    slot.innerHTML = `<p class="review-status-text">Log in to leave a review.</p>`;
    return;
  }

  try {
    const eligibility = await apiRequest(`/review/${productId}/eligibility`);

    if (eligibility.already_reviewed) {
      slot.innerHTML = `<p class="review-status-text">You have already reviewed this product. Thank you!</p>`;
      return;
    }

    if (!eligibility.can_review) {
      slot.innerHTML = `<p class="review-status-text">You can leave a review after receiving an order with this product.</p>`;
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
      <p class="review-form-title">Leave a review</p>
      <div class="star-input" id="star-input">
        ${[1, 2, 3, 4, 5].map((n) => `<button type="button" data-value="${n}" aria-label="${n} stars">★</button>`).join("")}
      </div>
      <textarea class="review-textarea" id="review-comment" placeholder="Tell us what you liked (or didn't)..."></textarea>
      <div>
        <button type="button" class="review-submit-button" id="review-submit-button">Submit review</button>
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
      showToast("Choose a rating from 1 to 5 stars", "error");
      return;
    }
    if (!comment) {
      showToast("Write a short comment for your review", "error");
      return;
    }

    submitButton.disabled = true;
    try {
      await apiRequest(`/review/${productId}`, {
        method: "POST",
        body: JSON.stringify({ rating: selectedRating, comment }),
      });
      showToast("Thank you for your review!", "success");
      slot.innerHTML = `<p class="review-status-text">You have already reviewed this product. Thank you!</p>`;
      loadReviews(productId);
    } catch (error) {
      showToast(error.message, "error");
      submitButton.disabled = false;
    }
  });
}

// Add to cart — works for guests (localStorage) and logged-in users
// (real backend cart) transparently, see js/cart-store.js
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
      showToast(`"${product.name}" added to cart`, "success");
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
  return Number(amount).toLocaleString("en-US");
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
