document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  const recommendationsSection = document.querySelector(".recommendations");

  if (!form || !recommendationsSection) {
    return;
  }

  form.addEventListener("submit", () => {
    recommendationsSection.classList.add("loading");
    setTimeout(() => recommendationsSection.classList.remove("loading"), 500);
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("user_id");
  const box = document.getElementById("user_suggestions");

  let cachedUsers = [];

  // 🔥 Load user list 1 lần duy nhất
  fetch("/api/users")
    .then(res => res.json())
    .then(data => {
      cachedUsers = data;
    });

  input.addEventListener("input", () => {
    const query = input.value.trim();
    box.innerHTML = "";

    if (query === "") return;

    const suggestions = cachedUsers
      .filter(id => id.toString().startsWith(query))
      .slice(0, 10); // chỉ show 10 cái

    suggestions.forEach(id => {
      const div = document.createElement("div");
      div.className = "suggest-item";
      div.textContent = id;

      div.onclick = () => {
        input.value = id;
        box.innerHTML = "";
      };

      box.appendChild(div);
    });
  });
});
