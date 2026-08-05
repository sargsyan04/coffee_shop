const NEXT_STATUS = {
  paid: { next: "in_progress", label: "Взять в работу" },
  in_progress: { next: "ready", label: "Готово к выдаче" },
  ready: { next: "completed", label: "Выдан" },
};

const STATUS_LABELS = {
  created: "Создан",
  paid: "Оплачен",
  in_progress: "Готовится",
  ready: "Готов к выдаче",
  completed: "Завершён",
  cancelled: "Отменён",
};

function formatOrderDate(iso) {
  return new Date(iso).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

// containerId -> { orders: [...], filter: "all" | order status }. Keeping the
// full list here means a status filter (see setQueueFilter) can re-render
// instantly without another request, and survives the reload that happens
// after advancing an order's status.
const queueState = {};

async function loadOrderQueue(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = `<p class="queue-loading">Загрузка заказов...</p>`;
  queueState[containerId] = queueState[containerId] || { orders: [], filter: "all" };

  try {
    const orders = await apiRequest("/orders/staff/all");
    queueState[containerId].orders = orders;
    renderQueueList(containerId);
  } catch (error) {
    container.innerHTML = `<p class="queue-error">Не удалось загрузить заказы: ${error.message}</p>`;
  }
}

function renderQueueList(containerId) {
  const container = document.getElementById(containerId);
  const state = queueState[containerId];
  if (!container || !state) return;

  const orders = state.filter === "all" ? state.orders : state.orders.filter((order) => order.status === state.filter);

  if (orders.length === 0) {
    container.innerHTML = `<p class="queue-empty">${state.orders.length === 0 ? "Активных заказов нет." : "Нет заказов с этим статусом."}</p>`;
    return;
  }

  container.innerHTML = orders.map(renderOrderCard).join("");
  bindOrderQueueActions(containerId);
}

// Called by the filter tabs on staff.html — status is "all" or one of
// paid / in_progress / ready
function setQueueFilter(containerId, status) {
  queueState[containerId] = queueState[containerId] || { orders: [], filter: "all" };
  queueState[containerId].filter = status;
  renderQueueList(containerId);
}

function renderOrderCard(order) {
  const action = NEXT_STATUS[order.status];
  const itemsHtml = order.items
    .map((item) => `<li>${item.product_name} × ${item.quantity}</li>`)
    .join("");

  return `
    <li class="queue-card" data-order-id="${order.id}">
      <div class="queue-card-header">
        <span class="queue-order-id">Заказ №${order.id}</span>
        <span class="badge badge-role">${STATUS_LABELS[order.status] || order.status}</span>
      </div>
      <ul class="queue-items">${itemsHtml}</ul>
      <div class="queue-card-footer">
        <span class="queue-total">${order.total_price} ֏</span>
        <span class="queue-date">${formatOrderDate(order.created_at)}</span>
      </div>
      ${action ? `<button type="button" class="btn-queue-advance" data-next-status="${action.next}">${action.label}</button>` : ""}
    </li>
  `;
}

function bindOrderQueueActions(containerId) {
  const container = document.getElementById(containerId);
  container.querySelectorAll(".btn-queue-advance").forEach((button) => {
    button.addEventListener("click", async () => {
      const card = button.closest(".queue-card");
      const orderId = card.dataset.orderId;
      const nextStatus = button.dataset.nextStatus;

      button.disabled = true;
      try {
        await apiRequest(`/orders/${orderId}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: nextStatus }),
        });
        showToast(`Заказ №${orderId} обновлён`, "success");
        loadOrderQueue(containerId);
      } catch (error) {
        showToast(error.message, "error");
        button.disabled = false;
      }
    });
  });
}