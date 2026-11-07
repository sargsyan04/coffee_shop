// Admin "Dashboard" and "Statistics" tabs.
//
// Backend contract:
//   GET /admin/stats/overview?period=today|7d|30d|90d|all
//     -> {
//          period, revenue, orders_count, average_check, new_users,
//          orders_by_status: { paid: 3, ... },
//          revenue_by_day: [{ date: "2026-10-24", revenue: 4200, orders: 5 }],
//          top_products: [{ product_id, name, quantity, revenue }]
//        }
// If the endpoint is unavailable, the dashboard still shows the numbers it
// can get from existing endpoints (users / products totals) plus a short notice.

const dashboardCards = document.getElementById("dashboard-cards");
const dashboardStatuses = document.getElementById("dashboard-statuses");
const dashboardTopProducts = document.getElementById("dashboard-top-products");
const dashboardNotice = document.getElementById("dashboard-notice");

const statsCards = document.getElementById("stats-cards");
const statsChart = document.getElementById("stats-chart");
const statsStatuses = document.getElementById("stats-statuses");
const statsTopProducts = document.getElementById("stats-top-products");
const statsNotice = document.getElementById("stats-notice");
const statsPeriodButtons = document.querySelectorAll("#stats-period-tabs .queue-filter-btn");

const STATS_STATUS_ORDER = ["paid", "in_progress", "ready", "completed", "cancelled"];
const ACTIVE_ORDER_STATUSES = ["paid", "in_progress", "ready"];

function statCard(label, value, hint = "") {
  return `
    <div class="stat-card">
      <span class="stat-card-label">${label}</span>
      <span class="stat-card-value">${value}</span>
      ${hint ? `<span class="stat-card-hint">${hint}</span>` : ""}
    </div>
  `;
}

function formatInt(value) {
  return Number(value ?? 0).toLocaleString("en-US");
}

function formatMoneyShort(value) {
  return `${Math.round(Number(value ?? 0)).toLocaleString("en-US")} ֏`;
}

function noticeForError(error, endpoint) {
  return error.status === 404 || error.status === 405
    ? `Order metrics will appear once the ${endpoint} endpoint is available on the server.`
    : error.message;
}

// Horizontal bars: one row per label, width relative to the biggest value

function renderBarList(container, rows, formatValue) {
  if (!rows.length) {
    container.innerHTML = '<p class="user-detail-empty">No data yet.</p>';
    return;
  }

  const max = Math.max(...rows.map((row) => row.value), 1);

  container.innerHTML = rows
    .map(
      (row) => `
      <div class="bar-row">
        <div class="bar-row-head">
          <span class="bar-row-label">${escapeHtml(row.label)}</span>
          <span class="bar-row-value">${formatValue(row)}</span>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:${Math.max((row.value / max) * 100, row.value > 0 ? 3 : 0)}%"></div></div>
      </div>
    `
    )
    .join("");
}

function statusRows(ordersByStatus) {
  return STATS_STATUS_ORDER.filter((status) => ordersByStatus && ordersByStatus[status] !== undefined).map((status) => ({
    label: ADMIN_ORDER_STATUS_LABELS[status],
    value: Number(ordersByStatus[status]),
  }));
}

function topProductRows(products) {
  return (products || []).map((product) => ({
    label: product.name,
    value: Number(product.quantity),
    revenue: product.revenue,
  }));
}

// Column chart — pure HTML/CSS, no chart library needed for a single series

function renderRevenueChart(container, points) {
  if (!points || !points.length) {
    container.innerHTML = '<p class="user-detail-empty">No orders in the selected period.</p>';
    return;
  }

  const max = Math.max(...points.map((point) => Number(point.revenue)), 1);
  // Show roughly 8 date labels no matter how long the period is
  const labelEvery = Math.max(1, Math.ceil(points.length / 8));

  container.innerHTML = `
    <div class="column-chart" role="img" aria-label="Revenue by day">
      ${points
        .map((point, index) => {
          const height = Math.max((Number(point.revenue) / max) * 100, Number(point.revenue) > 0 ? 2 : 0);
          const date = new Date(point.date).toLocaleDateString("en-US", { day: "2-digit", month: "2-digit" });
          const tooltip = `${date}: ${formatMoneyShort(point.revenue)}, orders: ${point.orders ?? 0}`;

          return `
            <div class="column-chart-col" title="${escapeHtml(tooltip)}">
              <div class="column-chart-bar" style="height:${height}%"></div>
              <span class="column-chart-label">${index % labelEvery === 0 ? date : ""}</span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

// Dashboard

async function loadDashboard() {
  dashboardNotice.hidden = true;
  dashboardCards.innerHTML = [
    statCard("Revenue today", "…"),
    statCard("Orders today", "…"),
    statCard("Average order value", "…"),
    statCard("New customers", "…"),
  ].join("");

  const [overviewResult, usersResult, productsResult] = await Promise.allSettled([
    apiRequest("/admin/stats/overview?period=today"),
    apiRequest("/admin/users?page_size=1"),
    apiRequest("/products/?page_size=1"),
  ]);

  const cards = [];

  if (overviewResult.status === "fulfilled") {
    const overview = overviewResult.value;
    const active = ACTIVE_ORDER_STATUSES.reduce((sum, status) => sum + Number(overview.orders_by_status?.[status] ?? 0), 0);

    cards.push(
      statCard("Revenue today", formatMoneyShort(overview.revenue)),
      statCard("Orders today", formatInt(overview.orders_count)),
      statCard("Active orders", formatInt(active), "paid, in progress or waiting for pickup"),
      statCard("Average order value", formatMoneyShort(overview.average_check)),
      statCard("New customers", formatInt(overview.new_users), "registered today")
    );

    renderBarList(dashboardStatuses, statusRows(overview.orders_by_status), (row) => formatInt(row.value));
    renderBarList(dashboardTopProducts, topProductRows(overview.top_products), (row) => `${formatInt(row.value)} pcs`);
  } else {
    dashboardStatuses.innerHTML = '<p class="user-detail-empty">No data.</p>';
    dashboardTopProducts.innerHTML = '<p class="user-detail-empty">No data.</p>';
    dashboardNotice.textContent = noticeForError(overviewResult.reason, "GET /admin/stats/overview");
    dashboardNotice.hidden = false;
  }

  if (usersResult.status === "fulfilled") {
    cards.push(statCard("Total users", formatInt(usersResult.value.total)));
  }
  if (productsResult.status === "fulfilled") {
    cards.push(statCard("Products in catalog", formatInt(productsResult.value.total)));
  }

  dashboardCards.innerHTML = cards.join("");
}

// Statistics

let statsPeriod = "7d";

async function loadStats() {
  statsNotice.hidden = true;
  statsCards.innerHTML = statCard("Loading", "…");

  try {
    const overview = await apiRequest(`/admin/stats/overview?period=${statsPeriod}`);

    statsCards.innerHTML = [
      statCard("Revenue", formatMoneyShort(overview.revenue)),
      statCard("Orders", formatInt(overview.orders_count)),
      statCard("Average order value", formatMoneyShort(overview.average_check)),
      statCard("New customers", formatInt(overview.new_users)),
    ].join("");

    renderRevenueChart(statsChart, overview.revenue_by_day);
    renderBarList(statsStatuses, statusRows(overview.orders_by_status), (row) => formatInt(row.value));
    renderBarList(
      statsTopProducts,
      topProductRows(overview.top_products),
      (row) => `${formatInt(row.value)} pcs · ${formatMoneyShort(row.revenue)}`
    );
  } catch (error) {
    statsCards.innerHTML = "";
    statsChart.innerHTML = "";
    statsStatuses.innerHTML = "";
    statsTopProducts.innerHTML = "";
    statsNotice.textContent = noticeForError(error, "GET /admin/stats/overview");
    statsNotice.hidden = false;
  }
}

statsPeriodButtons.forEach((button) => {
  button.addEventListener("click", () => {
    statsPeriodButtons.forEach((b) => b.classList.toggle("active", b === button));
    statsPeriod = button.dataset.period;
    loadStats();
  });
});

PANEL_PAGE_HOOKS.dashboard = loadDashboard;
PANEL_PAGE_HOOKS.stats = loadStats;
