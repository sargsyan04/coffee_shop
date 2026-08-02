const panelGuardMessage = document.getElementById("panel-guard-message");
const panelContent = document.getElementById("panel-content");

const categoryForm = document.getElementById("category-form");
const categoryFormStatus = document.getElementById("category-form-status");
const productForm = document.getElementById("product-form");
const productFormStatus = document.getElementById("product-form-status");
const productCategorySelect = document.getElementById("product-category");

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

  panelContent.hidden = false;
  loadOrderQueue("order-queue");
  loadCategoriesIntoSelect();
});

async function loadCategoriesIntoSelect() {
  try {
    const categories = await apiRequest("/categories/");
    categories.forEach((category) => {
      const option = document.createElement("option");
      option.value = category.id;
      option.textContent = category.name;
      productCategorySelect.appendChild(option);
    });
  } catch {
    // Non-critical — the "no category" option still works fine without this.
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
    loadCategoriesIntoSelect();
  } catch (error) {
    categoryFormStatus.textContent = error.message;
    categoryFormStatus.hidden = false;
  }
});

productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  productFormStatus.hidden = true;

  const categoryId = productCategorySelect.value;

  try {
    await apiRequest("/products/create", {
      method: "POST",
      body: JSON.stringify({
        name: document.getElementById("product-name").value,
        price: document.getElementById("product-price").value,
        category_id: categoryId ? Number(categoryId) : null,
        tag_ids: [],
      }),
    });
    showToast("Товар создан", "success");
    productForm.reset();
  } catch (error) {
    productFormStatus.textContent = error.message;
    productFormStatus.hidden = false;
  }
});
