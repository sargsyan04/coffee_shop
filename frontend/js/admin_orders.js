// Admin "Заказы" tab — table of all orders with a "Подробнее" popup.
//
// This tab is the order history. Taking an order into work is done in the
// staff panel (staff.html), which admins can open too.
//
// Backend contract:
//   GET /admin/orders?page&page_size&search&status&payment_method&sort_by&sort_order
//     -> { items: AdminOrder[], total, page, page_size, total_pages }
//   GET /admin/orders/{id} -> AdminOrderDetails
// Every field the backend does not return is shown as "—".

const ADMIN_ORDER_STATUS_LABELS = {
  created: "В корзине",
  paid: "Оплачен",
  in_progress: "Готовится",
  ready: "Готов к выдаче",
  completed: "Завершён",
  cancelled: "Отменён",
};

const PAYMENT_METHOD_LABELS = {
  online: "Онлайн",
  cash: "Наличными",
};

const PAYMENT_STATUS_LABELS = {
  paid: "Оплачен",
  unpaid: "Не оплачен",
  refunded: "Возврат",
};

const ordersTableBody = document.getElementById("orders-table-body");
const ordersFormStatus = document.getElementById("orders-form-status");
const ordersSearchInput = document.getElementById("orders-search");
const ordersFilterStatus = document.getElementById("orders-filter-status");
const ordersFilterPayment = document.getElementById("orders-filter-payment");
const ordersSortBy = document.getElementById("orders-sort-by");
const ordersSortOrderBtn = document.getElementById("orders-sort-order");
const ordersPager = document.getElementById("orders-pager");
const ordersPagerInfo = document.getElementById("orders-pager-info");
const ordersPrevBtn = document.getElementById("orders-prev");
const ordersNextBtn = document.getElementById("orders-next");

const orderDetailsOverlay = document.getElementById("order-details-modal-overlay");
const orderDetailsTitle = document.getElementById("order-details-title");
const orderDetailsStatus = document.getElementById("order-details-status");
const orderDetailsBody = document.getElementById("order-details-body");

const ORDERS_PAGE_SIZE = 20;
const ordersState = { page: 1, totalPages: 1 };

// Filled by renderAdminOrdersTable — lets "Подробнее" show something instantly
// from the list row while the full details are still loading
let adminOrdersById = {};

function formatMoney(amount) {
  return `${amount ?? "—"} ֏`;
}

function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function orderStatusBadge(status) {
  const label = ADMIN_ORDER_STATUS_LABELS[status] || escapeHtml(status || "—");
  return `<span class="badge badge-status badge-status-${escapeHtml(status || "unknown")}">${label}</span>`;
}

function paymentCell(order) {
  const method = PAYMENT_METHOD_LABELS[order.payment_method];
  const status = PAYMENT_STATUS_LABELS[order.payment_status];

  if (!method && !status) return "—";

  return `
    <div class="payment-cell">
      <span>${method || "—"}</span>
      ${status ? `<span class="payment-state payment-state-${escapeHtml(order.payment_status)}">${status}</span>` : ""}
    </div>
  `;
}

function customerCell(order) {
  const customer = order.customer || {};
  const name = customer.name || "—";
  const guestTag = customer.is_guest ? ' <span class="badge badge-guest">Гость</span>' : "";
  const phone = customer.phone ? `<span class="cell-sub">${escapeHtml(customer.phone)}</span>` : "";

  return `<div class="customer-cell"><span>${escapeHtml(name)}${guestTag}</span>${phone}</div>`;
}

async function loadAdminOrders() {
  const params = new URLSearchParams();
  params.set("page", ordersState.page);
  params.set("page_size", ORDERS_PAGE_SIZE);

  const search = ordersSearchInput.value.trim();
  if (search) params.set("search", search);
  if (ordersFilterStatus.value) params.set("status", ordersFilterStatus.value);
  if (ordersFilterPayment.value) params.set("payment_method", ordersFilterPayment.value);
  params.set("sort_by", ordersSortBy.value);
  params.set("sort_order", ordersSortOrderBtn.dataset.order);

  ordersFormStatus.hidden = true;

  try {
    const page = await apiRequest(`/admin/orders?${params.toString()}`);
    ordersState.totalPages = page.total_pages || 1;
    renderAdminOrdersTable(page.items);
    renderOrdersPager(page);
  } catch (error) {
    ordersTableBody.innerHTML = "";
    ordersPager.hidden = true;

    // 404/405 = the backend endpoint has not been written yet
    ordersFormStatus.textContent =
      error.status === 404 || error.status === 405
        ? "Список заказов появится, когда на сервере будет готов эндпоинт GET /admin/orders."
        : error.message;
    ordersFormStatus.hidden = false;
  }
}

function renderAdminOrdersTable(orders) {
  adminOrdersById = Object.fromEntries(orders.map((order) => [order.id, order]));

  if (orders.length === 0) {
    ordersTableBody.innerHTML = '<tr><td colspan="7" class="users-empty">Заказов не найдено</td></tr>';
    return;
  }

  ordersTableBody.innerHTML = orders
    .map(
      (order) => `
      <tr>
        <td class="users-id-cell">№${order.id}</td>
        <td>${formatDateTime(order.created_at)}</td>
        <td>${customerCell(order)}</td>
        <td class="nowrap">${formatMoney(order.total_price)}</td>
        <td>${paymentCell(order)}</td>
        <td>${orderStatusBadge(order.status)}</td>
        <td class="nowrap">
          <button type="button" class="btn-secondary orders-details-btn" data-order-id="${order.id}">Подробнее</button>
        </td>
      </tr>
    `
    )
    .join("");

  ordersTableBody.querySelectorAll(".orders-details-btn").forEach((button) => {
    button.addEventListener("click", () => openOrderDetails(Number(button.dataset.orderId)));
  });
}

function renderOrdersPager(page) {
  ordersPager.hidden = page.total_pages <= 1;
  ordersPagerInfo.textContent = `Страница ${page.page} из ${page.total_pages} · всего заказов: ${page.total}`;
  ordersPrevBtn.disabled = page.page <= 1;
  ordersNextBtn.disabled = page.page >= page.total_pages;
}

// Filters / sorting always jump back to the first page

let ordersSearchTimer = null;
function reloadOrdersFromStart() {
  ordersState.page = 1;
  loadAdminOrders();
}

ordersSearchInput.addEventListener("input", () => {
  clearTimeout(ordersSearchTimer);
  ordersSearchTimer = setTimeout(reloadOrdersFromStart, 300);
});
[ordersFilterStatus, ordersFilterPayment, ordersSortBy].forEach((control) => control.addEventListener("change", reloadOrdersFromStart));

ordersSortOrderBtn.addEventListener("click", () => {
  const next = ordersSortOrderBtn.dataset.order === "asc" ? "desc" : "asc";
  ordersSortOrderBtn.dataset.order = next;
  ordersSortOrderBtn.textContent = next === "asc" ? "По возрастанию" : "По убыванию";
  reloadOrdersFromStart();
});

ordersPrevBtn.addEventListener("click", () => {
  if (ordersState.page > 1) {
    ordersState.page -= 1;
    loadAdminOrders();
  }
});
ordersNextBtn.addEventListener("click", () => {
  if (ordersState.page < ordersState.totalPages) {
    ordersState.page += 1;
    loadAdminOrders();
  }
});

// Order details popup

function detailRow(label, value) {
  return `
    <div class="user-detail-row">
      <span class="user-detail-label">${label}</span>
      <span class="user-detail-value">${value}</span>
    </div>
  `;
}

function renderOrderDetails(order) {
  const customer = order.customer || {};
  const items = order.items || [];

  const itemsHtml = items.length
    ? `
      <table class="order-items-table">
        <thead>
          <tr><th>Товар</th><th>Цена</th><th>Кол-во</th><th>Сумма</th></tr>
        </thead>
        <tbody>
          ${items
            .map(
              (item) => `
            <tr>
              <td>${escapeHtml(item.product_name)}</td>
              <td class="nowrap">${formatMoney(item.unit_price)}</td>
              <td>${item.quantity}</td>
              <td class="nowrap">${formatMoney(item.line_total)}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `
    : '<p class="user-detail-empty">Состав заказа загружается…</p>';

  return `
    <h3 class="order-detail-section">Клиент</h3>
    <div class="user-detail-list">
      ${detailRow("Имя", escapeHtml(customer.name || "—"))}
      ${detailRow("Тип", customer.is_guest ? "Гость (без аккаунта)" : "Зарегистрированный клиент")}
      ${customer.user_id ? detailRow("ID пользователя", customer.user_id) : ""}
      ${detailRow("Телефон", escapeHtml(customer.phone || "—"))}
      ${detailRow("Email", escapeHtml(customer.email || "—"))}
    </div>

    <h3 class="order-detail-section">Оплата</h3>
    <div class="user-detail-list">
      ${detailRow("Способ", PAYMENT_METHOD_LABELS[order.payment_method] || "—")}
      ${detailRow("Статус оплаты", PAYMENT_STATUS_LABELS[order.payment_status] || "—")}
      ${detailRow("Итого", `<strong>${formatMoney(order.total_price)}</strong>`)}
    </div>

    <h3 class="order-detail-section">Обработка</h3>
    <div class="user-detail-list">
      ${detailRow("Создан", formatDateTime(order.created_at))}
      ${detailRow("Взял в работу", escapeHtml(order.barista?.name || "—"))}
    </div>

    <h3 class="order-detail-section">Состав заказа</h3>
    ${itemsHtml}
  `;
}

function showOrderDetails(order) {
  orderDetailsTitle.textContent = `Заказ №${order.id}`;
  orderDetailsStatus.className = `badge badge-status badge-status-${order.status}`;
  orderDetailsStatus.textContent = ADMIN_ORDER_STATUS_LABELS[order.status] || order.status;
  orderDetailsBody.innerHTML = renderOrderDetails(order);
}

async function openOrderDetails(orderId) {
  const preview = adminOrdersById[orderId];
  if (preview) showOrderDetails(preview);
  orderDetailsOverlay.hidden = false;

  try {
    const full = await apiRequest(`/admin/orders/${orderId}`);
    showOrderDetails(full);
  } catch (error) {
    // The list row already shows the main fields — only the item list is missing
    if (error.status !== 404 && error.status !== 405) {
      showToast(error.message, "error");
    }
    if (preview && !(preview.items || []).length) {
      orderDetailsBody.querySelector(".user-detail-empty")?.replaceWith(
        Object.assign(document.createElement("p"), {
          className: "user-detail-empty",
          textContent: "Не удалось загрузить состав заказа.",
        })
      );
    }
  }
}

function closeOrderDetails() {
  orderDetailsOverlay.hidden = true;
  orderDetailsBody.innerHTML = "";
}

document.getElementById("order-details-close").addEventListener("click", closeOrderDetails);
orderDetailsOverlay.addEventListener("click", (event) => {
  if (event.target === orderDetailsOverlay) closeOrderDetails();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !orderDetailsOverlay.hidden) closeOrderDetails();
});

PANEL_PAGE_HOOKS.orders = reloadOrdersFromStart;
