async function testConnection() {
  try {
    const response = await fetch("http://localhost:8080/products/");
    const data = await response.json();
    console.log("The backend responds:", data);
  } catch (error) {
    console.error("I can't connect to the backend:", error);
  }
}

testConnection();