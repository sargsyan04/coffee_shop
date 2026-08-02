const heroGuestActions = document.getElementById("hero-actions-guest");
const heroAccountActions = document.getElementById("hero-actions-account");

document.addEventListener("coffeeshop:auth", (event) => {
  const { authenticated } = event.detail;
  if (!heroGuestActions || !heroAccountActions) return;

  heroGuestActions.hidden = authenticated;
  heroAccountActions.hidden = !authenticated;
});
