const PASSWORD_CHANGE_PAGE = "force_password_change.html";

// Pages reachable without a valid/complete session — never bounced around
// by the auth/must-change-password redirects below.
const PUBLIC_ONLY_PAGES = [
  "login.html",
  "register.html",
  "register_step2.html",
  PASSWORD_CHANGE_PAGE,
];

const NAV_LINKS = [
  { href: "catalog.html", label: "Меню" },
  { href: "cart.html", label: "Корзина", cartBadge: true },
];

function currentPageName() {
  return window.location.pathname.split("/").pop() || "index.html";
}

function renderGuestActions() {
  return `
    <a href="login.html" class="btn-nav btn-nav-ghost">Войти</a>
    <a href="register.html" class="btn-nav btn-nav-solid">Регистрация</a>
  `;
}

// Slightly different action sets per role — same shell, different shortcuts,
// as requested: customers get their profile, staff/admins get a link to
// their own panel instead (they still reach the profile page too).
function renderAccountActions(user) {
  const panelLink =
    user.role === "admin"
      ? `<a href="admin.html" class="btn-nav btn-nav-ghost">Админ-панель</a>`
      : user.role === "barista"
        ? `<a href="staff.html" class="btn-nav btn-nav-ghost">Панель сотрудника</a>`
        : "";

  const roleTag = user.role !== "customer" ? `<span class="nav-role-tag">${roleLabel(user.role)}</span>` : "";

  return `
    ${roleTag}
    ${panelLink}
    <a href="profile.html" class="btn-nav btn-nav-ghost">Профиль</a>
    <button type="button" class="btn-nav btn-nav-solid" id="logout-button">Выйти</button>
  `;
}

function renderHeader() {
  const root = document.getElementById("site-header-root");
  if (!root) return;

  const page = currentPageName();
  const navLinksHtml = NAV_LINKS.map(({ href, label, cartBadge }) => `
    <a href="${href}" class="nav-link${href === page ? " nav-link-active" : ""}">
      ${label}${cartBadge ? '<span class="nav-cart-badge" id="cart-badge" hidden>0</span>' : ""}
    </a>
  `).join("");

  root.innerHTML = `
    <header class="site-nav">
      <a href="index.html" class="nav-brand">
        <img src="../media/logo.png" alt="" class="nav-logo">
        <span>Coffee Shop</span>
      </a>
      <nav class="nav-links">${navLinksHtml}</nav>
      <div class="nav-actions" id="nav-actions">${renderGuestActions()}</div>
    </header>
  `;

  bindLogoutButton();
}

function bindLogoutButton() {
  document.getElementById("logout-button")?.addEventListener("click", async () => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        await fetch(`${API_BASE_URL}/user/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getAccessToken()}`,
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // ignore — log out locally regardless
      }
    }

    clearTokens();
    if (typeof setFlashMessage === "function") setFlashMessage("Вы вышли из аккаунта", "info");
    window.location.href = "index.html";
  });
}

function renderFooter() {
  const root = document.getElementById("site-footer-root");
  if (!root) return;

  // Dynamic on purpose — always the real current year, no manual edits.
  const year = new Date().getFullYear();

  root.innerHTML = `
    <footer class="site-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <img src="../media/logo.png" alt="" class="footer-logo">
          <span>Coffee Shop</span>
        </div>
        <nav class="footer-links">
          <a href="index.html">Главная</a>
          <a href="catalog.html">Меню</a>
          <a href="cart.html">Корзина</a>
        </nav>
      </div>
      <p class="footer-copy">© Coffee Shop, ${year}. Все права защищены.</p>
    </footer>
  `;
}

async function reflectAuthState() {
  const page = currentPageName();
  const navActions = document.getElementById("nav-actions");

  if (!getAccessToken()) {
    document.dispatchEvent(new CustomEvent("coffeeshop:auth", { detail: { authenticated: false, user: null } }));
    return;
  }

  try {
    // /user/status stays reachable even when must_change_password is true,
    // so it's always the first call — /user/profile would 403 in that case.
    const status = await apiRequest("/user/status");

    if (status.must_change_password && page !== PASSWORD_CHANGE_PAGE) {
      window.location.href = PASSWORD_CHANGE_PAGE;
      return;
    }

    if (!status.must_change_password && PUBLIC_ONLY_PAGES.includes(page)) {
      // Already fully logged in — no reason to sit on the login/register/
      // force-password-change screens.
      window.location.href = "index.html";
      return;
    }

    if (status.must_change_password) {
      // We're on the password-change page itself with nothing left to do here.
      document.dispatchEvent(new CustomEvent("coffeeshop:auth", { detail: { authenticated: true, user: status } }));
      return;
    }

    const user = await apiRequest("/user/profile");
    if (navActions) {
      navActions.innerHTML = renderAccountActions(user);
      bindLogoutButton();
    }
    document.dispatchEvent(new CustomEvent("coffeeshop:auth", { detail: { authenticated: true, user } }));
  } catch {
    // Token invalid/expired and refresh failed — fall back to guest state.
    clearTokens();
    document.dispatchEvent(new CustomEvent("coffeeshop:auth", { detail: { authenticated: false, user: null } }));
  }
}

renderHeader();
renderFooter();
reflectAuthState();
if (typeof consumeFlashMessage === "function") consumeFlashMessage();
