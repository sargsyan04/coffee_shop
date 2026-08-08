const panelGuardMessage = document.getElementById("panel-guard-message");
const panelContent = document.getElementById("panel-content");
const panelNavList = document.getElementById("panel-nav-list");
const panelPageEyebrow = document.getElementById("panel-page-eyebrow");
const panelPageTitle = document.getElementById("panel-page-title");

// Sidebar navigation — switches which <section class="panel-page">
// is visible, no page reload

const PANEL_PAGES = [
  { id: "dashboard", icon: "icon-dashboard", label: "Дашборд" },
  { id: "users", icon: "icon-users", label: "Пользователи" },
  { id: "products", icon: "icon-products", label: "Продукты" },
  { id: "categories", icon: "icon-categories", label: "Категории" },
  { id: "tags", icon: "icon-tags", label: "Теги" },
  { id: "orders", icon: "icon-orders", label: "Заказы" },
  { id: "stats", icon: "icon-stats", label: "Статистика" },
];

function renderPanelNav() {
  panelNavList.innerHTML = PANEL_PAGES.map(
    (page) => `
    <button type="button" class="panel-nav-item" id="panel-nav-${page.id}" data-page="${page.id}">
      <svg><use href="#${page.icon}"></use></svg>
      ${page.label}
    </button>
  `
  ).join("");

  PANEL_PAGES.forEach((page) => {
    document.getElementById(`panel-nav-${page.id}`).addEventListener("click", () => selectPanelPage(page.id));
  });
}

function selectPanelPage(id) {
  PANEL_PAGES.forEach((page) => {
    document.getElementById(`panel-nav-${page.id}`).classList.toggle("active", page.id === id);
    document.getElementById(`panel-page-${page.id}`).hidden = page.id !== id;
  });

  const page = PANEL_PAGES.find((p) => p.id === id);
  panelPageEyebrow.textContent = "Админ-панель";
  panelPageTitle.textContent = page.label;
}

const categoryForm = document.getElementById("category-form");
const categoryFormStatus = document.getElementById("category-form-status");
const categoriesTableBody = document.getElementById("categories-table-body");

const tagForm = document.getElementById("tag-form");
const tagFormStatus = document.getElementById("tag-form-status");
const tagsTableBody = document.getElementById("tags-table-body");

const productForm = document.getElementById("product-form");
const productFormStatus = document.getElementById("product-form-status");
const productCategorySelect = document.getElementById("product-category");
const productImageInput = document.getElementById("product-image");
const productTagsCheckboxes = document.getElementById("product-tags-checkboxes");
const productsTableBody = document.getElementById("products-table-body");

const usersTableBody = document.getElementById("users-table-body");
const usersFormStatus = document.getElementById("users-form-status");

const usersSearchInput = document.getElementById("users-search");
const usersFilterRole = document.getElementById("users-filter-role");
const usersFilterActive = document.getElementById("users-filter-active");
const usersFilterVerified = document.getElementById("users-filter-verified");
const usersFilterOrders = document.getElementById("users-filter-orders");
const usersFilterReviews = document.getElementById("users-filter-reviews");
const usersSortBy = document.getElementById("users-sort-by");
const usersSortOrderBtn = document.getElementById("users-sort-order");

const tempPasswordModalOverlay = document.getElementById("temp-password-modal-overlay");
const tempPasswordModalClose = document.getElementById("temp-password-modal-close");
const tempPasswordModalOk = document.getElementById("temp-password-modal-ok");
const tempPasswordEmail = document.getElementById("temp-password-email");
const tempPasswordValue = document.getElementById("temp-password-value");
const tempPasswordCopy = document.getElementById("temp-password-copy");

const ROLE_OPTIONS = ["customer", "barista", "admin"];

// Set once auth resolves — used to stop the currently-logged-in admin from
// demoting their own row in the UI (the backend rejects it too, this just
// avoids a confusing round-trip error)
let currentAdminId = null;

// Filled in by renderUsersTable — lets the "Подробнее" button look up the
// full user object (bonus points, email, etc.) by id without another request
let usersById = {};

document.addEventListener("coffeeshop:auth", (event) => {
  const { authenticated, user } = event.detail;

  if (!authenticated) {
    window.location.href = "login.html";
    return;
  }

  if (user.role !== "admin") {
    panelGuardMessage.hidden = false;
    return;
  }

  currentAdminId = user.id;
  panelContent.hidden = false;
  renderPanelNav();
  selectPanelPage("dashboard");
  loadOrderQueue("order-queue");
  loadCategories();
  loadTags();
  loadProducts();
  loadUsers();
});

// Categories — list + create

async function loadCategories() {
  try {
    const categories = await apiRequest("/categories/");
    renderCategoriesTable(categories);
    populateCategorySelect(categories);
  } catch (error) {
    categoriesTableBody.innerHTML = `<tr><td colspan="2" class="users-empty">${escapeHtml(error.message)}</td></tr>`;
  }
}

function renderCategoriesTable(categories) {
  if (categories.length === 0) {
    categoriesTableBody.innerHTML = '<tr><td colspan="2" class="users-empty">Категорий пока нет</td></tr>';
    return;
  }

  categoriesTableBody.innerHTML = categories
    .map((category) => `<tr><td class="users-id-cell">${category.id}</td><td>${escapeHtml(category.name)}</td></tr>`)
    .join("");
}

// Keeps whatever the admin already had selected in the product form
// (if it still exists) when the option list gets refreshed after a create.
function populateCategorySelect(categories) {
  const previousValue = productCategorySelect.value;

  productCategorySelect.innerHTML = '<option value="">Без категории</option>';
  categories.forEach((category) => {
    const option = document.createElement("option");
    option.value = category.id;
    option.textContent = category.name;
    productCategorySelect.appendChild(option);
  });

  if (previousValue && categories.some((category) => String(category.id) === previousValue)) {
    productCategorySelect.value = previousValue;
  }
}

categoryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  categoryFormStatus.hidden = true;

  try {
    await apiRequest("/categories/", {
      method: "POST",
      body: JSON.stringify({ name: document.getElementById("category-name").value }),
    });
    showToast("Категория создана", "success");
    categoryForm.reset();
    loadCategories();
  } catch (error) {
    categoryFormStatus.textContent = error.message;
    categoryFormStatus.hidden = false;
  }
});

// Tags — list + create

async function loadTags() {
  try {
    const tags = await apiRequest("/tags/");
    renderTagsTable(tags);
    renderProductTagCheckboxes(tags);
  } catch (error) {
    tagsTableBody.innerHTML = `<tr><td colspan="3" class="users-empty">${escapeHtml(error.message)}</td></tr>`;
  }
}

function renderTagsTable(tags) {
  if (tags.length === 0) {
    tagsTableBody.innerHTML = '<tr><td colspan="3" class="users-empty">Тегов пока нет</td></tr>';
    return;
  }

  tagsTableBody.innerHTML = tags
    .map(
      (tag) => `<tr><td class="users-id-cell">${tag.id}</td><td>${escapeHtml(tag.name)}</td><td>${escapeHtml(tag.slug ?? "")}</td></tr>`
    )
    .join("");
}

// Renders the tag checkbox list inside the product form — kept in sync
// whenever tags are (re)loaded, so a freshly created tag is selectable
// for a product right away without a page reload.
function renderProductTagCheckboxes(tags) {
  if (tags.length === 0) {
    productTagsCheckboxes.innerHTML = '<p class="users-empty">Тегов пока нет — создайте их в разделе «Теги».</p>';
    return;
  }

  productTagsCheckboxes.innerHTML = tags
    .map(
      (tag) => `
      <label class="checkbox-item">
        <input type="checkbox" name="product-tag" value="${tag.id}">
        ${escapeHtml(tag.name)}
      </label>
    `
    )
    .join("");
}

tagForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  tagFormStatus.hidden = true;

  try {
    await apiRequest("/tags/", {
      method: "POST",
      body: JSON.stringify({ name: document.getElementById("tag-name").value }),
    });
    showToast("Тег создан", "success");
    tagForm.reset();
    loadTags();
  } catch (error) {
    tagFormStatus.textContent = error.message;
    tagFormStatus.hidden = false;
  }
});

// Products — list + create

async function loadProducts() {
  try {
    const page = await apiRequest("/products/");
    renderProductsTable(page.items);
  } catch (error) {
    productsTableBody.innerHTML = `<tr><td colspan="5" class="users-empty">${escapeHtml(error.message)}</td></tr>`;
  }
}

function renderProductsTable(products) {
  if (products.length === 0) {
    productsTableBody.innerHTML = '<tr><td colspan="5" class="users-empty">Товаров пока нет</td></tr>';
    return;
  }

  productsTableBody.innerHTML = products
    .map((product) => {
      const thumb = product.image_url
        ? `<img class="data-table-thumb" src="${resolveImageUrl(product.image_url)}" alt="">`
        : '<span class="data-table-thumb-placeholder">—</span>';

      const tags =
        product.tags && product.tags.length
          ? `<div class="tag-chip-list">${product.tags.map((tag) => `<span class="tag-chip">${escapeHtml(tag.name)}</span>`).join("")}</div>`
          : '<span class="tag-chip-empty">—</span>';

      return `
        <tr>
          <td>${thumb}</td>
          <td>${escapeHtml(product.name)}</td>
          <td>${product.price} ֏</td>
          <td>${product.category ? escapeHtml(product.category.name) : "—"}</td>
          <td>${tags}</td>
        </tr>
      `;
    })
    .join("");
}

productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  productFormStatus.hidden = true;

  const categoryId = productCategorySelect.value;
  const tagIds = Array.from(productTagsCheckboxes.querySelectorAll('input[name="product-tag"]:checked')).map((checkbox) =>
    Number(checkbox.value)
  );
  const imageFile = productImageInput.files[0] || null;

  try {
    const created = await apiRequest("/products/create", {
      method: "POST",
      body: JSON.stringify({
        name: document.getElementById("product-name").value,
        price: document.getElementById("product-price").value,
        category_id: categoryId ? Number(categoryId) : null,
        tag_ids: tagIds,
      }),
    });

    // Image upload is a separate endpoint (POST /products/{id}/image) — run
    // it only once the product actually exists, and don't fail the whole
    // submission if just the photo upload has a problem.
    if (imageFile) {
      try {
        await apiUploadFile(`/products/${created.id}/image`, imageFile);
      } catch {
        showToast("Товар создан, но фото загрузить не удалось", "error");
      }
    }

    showToast("Товар создан", "success");
    productForm.reset();
    loadProducts();
  } catch (error) {
    productFormStatus.textContent = error.message;
    productFormStatus.hidden = false;
  }
});

// Users — list, role change, password reset

async function loadUsers() {
  const params = new URLSearchParams();

  const search = usersSearchInput.value.trim();
  if (search) params.set("search", search);
  if (usersFilterRole.value) params.set("role", usersFilterRole.value);
  if (usersFilterActive.value) params.set("is_active", usersFilterActive.value);
  if (usersFilterVerified.value) params.set("is_email_verified", usersFilterVerified.value);
  if (usersFilterOrders.value) params.set("has_orders", usersFilterOrders.value);
  if (usersFilterReviews.value) params.set("has_reviews", usersFilterReviews.value);
  params.set("sort_by", usersSortBy.value);
  params.set("sort_order", usersSortOrderBtn.dataset.order);

  try {
    const page = await apiRequest(`/admin/users?${params.toString()}`);
    renderUsersTable(page.items);
  } catch (error) {
    usersTableBody.innerHTML = "";
    usersFormStatus.textContent = error.message;
    usersFormStatus.hidden = false;
  }
}

// Debounced so typing in the search box doesn't fire a request per keystroke
let usersSearchDebounceTimer = null;
function scheduleUsersReload() {
  clearTimeout(usersSearchDebounceTimer);
  usersSearchDebounceTimer = setTimeout(loadUsers, 300);
}

usersSearchInput.addEventListener("input", scheduleUsersReload);
[usersFilterRole, usersFilterActive, usersFilterVerified, usersFilterOrders, usersFilterReviews, usersSortBy].forEach(
  (control) => control.addEventListener("change", loadUsers)
);
usersSortOrderBtn.addEventListener("click", () => {
  const nextOrder = usersSortOrderBtn.dataset.order === "asc" ? "desc" : "asc";
  usersSortOrderBtn.dataset.order = nextOrder;
  usersSortOrderBtn.textContent = nextOrder === "asc" ? "По возрастанию" : "По убыванию";
  loadUsers();
});

function renderUsersTable(users) {
  usersTableBody.innerHTML = "";
  usersById = Object.fromEntries(users.map((user) => [user.id, user]));

  if (users.length === 0) {
    usersTableBody.innerHTML = '<tr><td colspan="6" class="users-empty">Пользователей пока нет</td></tr>';
    return;
  }

  users.forEach((user) => {
    const row = document.createElement("tr");

    const isSelf = user.id === currentAdminId;

    const roleOptions = ROLE_OPTIONS.map(
      (role) =>
        `<option value="${role}" ${role === user.role ? "selected" : ""} ${isSelf && role !== "admin" ? "disabled" : ""}>${roleLabel(role)}</option>`
    ).join("");

    row.innerHTML = `
      <td class="users-id-cell">${user.id}</td>
      <td>${escapeHtml(user.name)}</td>
      <td>${escapeHtml(user.email)}</td>
      <td>
        <select class="users-role-select" data-user-id="${user.id}" ${isSelf ? 'title="Нельзя снять роль администратора с самого себя"' : ""}>
          ${roleOptions}
        </select>
      </td>
      <td><span class="badge">${user.is_active ? "Активен" : "Деактивирован"}</span></td>
      <td class="users-actions-cell">
        <button type="button" class="btn-secondary users-details-btn" data-user-id="${user.id}">Подробнее</button>
        <button type="button" class="btn-secondary users-reset-btn" data-user-id="${user.id}" data-user-email="${escapeHtml(user.email)}">Сбросить пароль</button>
      </td>
    `;

    usersTableBody.appendChild(row);
  });

  usersTableBody.querySelectorAll(".users-details-btn").forEach((button) => {
    button.addEventListener("click", () => openUserDetailsModal(usersById[button.dataset.userId]));
  });
  usersTableBody.querySelectorAll(".users-role-select").forEach((select) => {
    select.dataset.previousValue = select.value;
    select.addEventListener("change", onRoleChange);
  });
  usersTableBody.querySelectorAll(".users-reset-btn").forEach((button) => {
    button.addEventListener("click", onResetPassword);
  });
}

// Minimal escaping — user-supplied name/email get interpolated into innerHTML above
function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

async function onRoleChange(event) {
  const select = event.target;
  const userId = select.dataset.userId;
  const newRole = select.value;
  const previousValue = select.dataset.previousValue || select.options[0].value;

  select.disabled = true;
  usersFormStatus.hidden = true;

  try {
    await apiRequest(`/admin/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role: newRole }),
    });
    select.dataset.previousValue = newRole;
    showToast("Роль обновлена", "success");
  } catch (error) {
    select.value = previousValue;
    usersFormStatus.textContent = error.message;
    usersFormStatus.hidden = false;
  } finally {
    select.disabled = false;
  }
}

async function onResetPassword(event) {
  const button = event.target;
  const userId = button.dataset.userId;
  const userEmail = button.dataset.userEmail;

  const confirmed = await confirmDialog(`Сбросить пароль для ${userEmail}? Текущий пароль перестанет работать.`, {
    confirmLabel: "Сбросить",
  });
  if (!confirmed) {
    return;
  }

  button.disabled = true;
  usersFormStatus.hidden = true;

  try {
    const result = await apiRequest(`/admin/users/${userId}/reset-password`, {
      method: "POST",
    });

    tempPasswordEmail.textContent = userEmail;
    tempPasswordValue.textContent = result.password;
    tempPasswordModalOverlay.hidden = false;
  } catch (error) {
    usersFormStatus.textContent = error.message;
    usersFormStatus.hidden = false;
  } finally {
    button.disabled = false;
  }
}

function closeTempPasswordModal() {
  tempPasswordModalOverlay.hidden = true;
  tempPasswordValue.textContent = "";
}

tempPasswordModalClose.addEventListener("click", closeTempPasswordModal);
tempPasswordModalOk.addEventListener("click", closeTempPasswordModal);
tempPasswordModalOverlay.addEventListener("click", (event) => {
  if (event.target === tempPasswordModalOverlay) closeTempPasswordModal();
});

tempPasswordCopy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(tempPasswordValue.textContent);
    showToast("Пароль скопирован", "success");
  } catch {
    showToast("Не удалось скопировать — выделите вручную", "error");
  }
});

// User details popup — avatar, id, contact info, bonus points instantly
// (already in the /admin/users list); orders breakdown / total spent /
// reviews load separately from GET /admin/users/{id}/stats

const userDetailsModalOverlay = document.getElementById("user-details-modal-overlay");
const userDetailsModalClose = document.getElementById("user-details-modal-close");
const userDetailsModalTitle = document.getElementById("user-details-modal-title");
const userDetailsModalEmail = document.getElementById("user-details-modal-email");
const userDetailAvatarInitials = document.getElementById("user-detail-avatar-initials");
const userDetailAvatarImage = document.getElementById("user-detail-avatar-image");
const userDetailList = document.getElementById("user-detail-list");

const userDetailsOrdersToggle = document.getElementById("user-details-orders-toggle");
const userDetailsReviewsToggle = document.getElementById("user-details-reviews-toggle");
const userDetailsSidePanel = document.getElementById("user-details-side-panel");
const userDetailsSidePanelTitle = document.getElementById("user-details-side-panel-title");
const userDetailsSidePanelContent = document.getElementById("user-details-side-panel-content");
const userDetailsSidePanelClose = document.getElementById("user-details-side-panel-close");

// Same fallback pattern as the profile page avatar: initials on a colored
// circle when there's no photo, the real image once one exists.
function userInitials(name) {
  return name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function resolveImageUrl(imageUrl) {
  if (!imageUrl) return "";
  return imageUrl.startsWith("http") ? imageUrl : `${API_BASE_URL}${imageUrl}`;
}

function renderUserDetailAvatar(user) {
  if (user.image_url) {
    userDetailAvatarImage.src = resolveImageUrl(user.image_url);
    userDetailAvatarImage.hidden = false;
    userDetailAvatarInitials.hidden = true;
  } else {
    userDetailAvatarImage.hidden = true;
    userDetailAvatarImage.src = "";
    userDetailAvatarInitials.hidden = false;
    userDetailAvatarInitials.textContent = userInitials(user.name);
  }
}

const ORDER_STATUS_LABELS = {
  created: "Оформлен",
  paid: "Оплачен",
  in_progress: "Готовится",
  ready: "Готов",
  completed: "Завершён",
};

function userDetailRow(label, value, isLoading = false) {
  return `
    <div class="user-detail-row">
      <span class="user-detail-label">${label}</span>
      <span class="user-detail-value${isLoading ? " is-loading" : ""}">${value}</span>
    </div>
  `;
}

function renderUserDetailRows(user, stats) {
  return [
    userDetailRow("ID", user.id),
    userDetailRow("Роль", roleLabel(user.role)),
    userDetailRow("Статус", user.is_active ? "Активен" : "Деактивирован"),
    userDetailRow("Бонусные очки", user.bonus_points),
    stats
      ? userDetailRow("Заказов", stats.orders_count)
      : userDetailRow("Заказов", "Загрузка...", true),
    stats
      ? userDetailRow("Потрачено", `${stats.total_spent} ֏`)
      : userDetailRow("Потрачено", "Загрузка...", true),
    stats
      ? userDetailRow("Отзывов", stats.reviews_count)
      : userDetailRow("Отзывов", "Загрузка...", true),
  ].join("");
}

// Backend returns a per-status breakdown (see AdminUserStatsResponse.orders),
// not a flat list of individual orders — so the side panel shows one row per
// status with how much was spent in it. Draft/CREATED orders are excluded
// (see get_user_stats in routers/admin.py); cancelled orders are included but
// spend zero.
function renderOrdersList(stats) {
  const entries = Object.entries(stats.orders || {});

  if (!entries.length) {
    return `<p class="user-detail-empty">Заказов пока нет.</p>`;
  }

  return entries
    .map(
      ([statusKey, amount]) => `
      <div class="user-detail-sublist-row">
        <span>${ORDER_STATUS_LABELS[statusKey] || escapeHtml(statusKey)}</span>
        <span>${amount} ֏</span>
      </div>
    `
    )
    .join("");
}

function renderReviewsList(stats) {
  const reviews = stats.reviews || [];

  if (!reviews.length) {
    return `<p class="user-detail-empty">Отзывов пока нет.</p>`;
  }

  return reviews
    .map((review) => {
      const date = new Date(review.created_at).toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "long",
        year: "numeric",
      });

      return `
        <div class="user-detail-sublist-row user-detail-review-row">
          <div class="user-detail-review-header">
            <span class="user-detail-review-product">${escapeHtml(review.product?.name || "Товар")}</span>
            <span class="user-detail-review-rating">${"★".repeat(review.rating)}${"☆".repeat(5 - review.rating)}</span>
          </div>
          <p class="user-detail-review-comment">${escapeHtml(review.comment)}</p>
          <span class="user-detail-review-date">${date}</span>
        </div>
      `;
    })
    .join("");
}

function resetUserDetailToggles() {
  userDetailsOrdersToggle.disabled = true;
  userDetailsReviewsToggle.disabled = true;
  closeSidePanel();
}

// Stats are cached on the modal once loaded so opening the side panel
// afterwards doesn't need another request.
let currentUserStats = null;

async function openUserDetailsModal(user) {
  if (!user) return;

  currentUserStats = null;
  userDetailsModalTitle.textContent = user.name;
  userDetailsModalEmail.textContent = user.email;
  renderUserDetailAvatar(user);
  userDetailList.innerHTML = renderUserDetailRows(user, null);
  resetUserDetailToggles();
  userDetailsModalOverlay.hidden = false;

  try {
    const stats = await apiRequest(`/admin/users/${user.id}/stats`);
    currentUserStats = stats;
    userDetailList.innerHTML = renderUserDetailRows(user, stats);
    userDetailsOrdersToggle.disabled = false;
    userDetailsReviewsToggle.disabled = false;
  } catch {
    // Stats endpoint failed — leave the rest of the popup usable, just mark
    // those rows as unavailable and keep the side-panel buttons disabled
    // instead of failing the whole popup.
    userDetailList.querySelectorAll(".is-loading").forEach((el) => {
      el.textContent = "—";
    });
  }
}

function closeUserDetailsModal() {
  userDetailsModalOverlay.hidden = true;
  closeSidePanel();
}

function closeSidePanel() {
  userDetailsSidePanel.hidden = true;
  userDetailsSidePanelContent.innerHTML = "";
}

function openSidePanel(title, contentHtml) {
  userDetailsSidePanelTitle.textContent = title;
  userDetailsSidePanelContent.innerHTML = contentHtml;
  userDetailsSidePanel.hidden = false;
}

userDetailsOrdersToggle.addEventListener("click", () => {
  if (!userDetailsSidePanel.hidden && userDetailsSidePanelTitle.textContent === "Заказы") {
    closeSidePanel();
    return;
  }
  openSidePanel("Заказы", renderOrdersList(currentUserStats));
});

userDetailsReviewsToggle.addEventListener("click", () => {
  if (!userDetailsSidePanel.hidden && userDetailsSidePanelTitle.textContent === "Отзывы") {
    closeSidePanel();
    return;
  }
  openSidePanel("Отзывы", renderReviewsList(currentUserStats));
});

userDetailsSidePanelClose.addEventListener("click", closeSidePanel);

userDetailsModalClose.addEventListener("click", closeUserDetailsModal);
userDetailsModalOverlay.addEventListener("click", (event) => {
  if (event.target === userDetailsModalOverlay) closeUserDetailsModal();
});
