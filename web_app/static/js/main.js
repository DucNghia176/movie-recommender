const debounce = (fn, delay = 300) => {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
};

document.addEventListener("DOMContentLoaded", () => {
  // Autocomplete user
  const userInput = document.getElementById("user_id");
  const suggestBox = document.getElementById("user_suggestions");
  let cachedUsers = [];

  fetch("/api/users")
    .then((res) => res.json())
    .then((data) => {
      cachedUsers = data || [];
    })
    .catch(() => {
      cachedUsers = [];
    });

  if (userInput && suggestBox) {
    userInput.addEventListener("input", () => {
      const query = userInput.value.trim();
      suggestBox.innerHTML = "";
      if (query === "") return;
      const suggestions = cachedUsers
        .filter((id) => id.toString().startsWith(query))
        .slice(0, 10);
      suggestions.forEach((id) => {
        const div = document.createElement("div");
        div.className = "suggest-item";
        div.textContent = id;
        div.onclick = () => {
          userInput.value = id;
          suggestBox.innerHTML = "";
        };
        suggestBox.appendChild(div);
      });
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("loading_overlay");
  const form = document.querySelector("form");
  const recList = document.getElementById("recommendations_list");
  const pageInfo = document.getElementById("page_info");
  const paginationBox = document.getElementById("pagination_box");
  const searchInput = document.getElementById("search_input");
  const errorBox = document.getElementById("error_box");
  const placeholderText = document.getElementById("placeholder_text");
  const compareToggle = document.getElementById("compare_toggle");
  const algorithmSelect = document.getElementById("algorithm");
  const algorithmBSelect = document.getElementById("algorithm_b");
  const algorithmBLabel = document.getElementById("algorithm_b_label");
  const compareSection = document.getElementById("compare_section");
  const compareTable = document.getElementById("compare_table");
  const compareSummary = document.getElementById("compare_summary");

  const state = {
    userId: "",
    algA: "hybrid",
    algB: "hybrid",
    search: "",
    compare: false,
    page: 1,
  };

  const setLoading = (flag) => {
    if (overlay) overlay.classList[flag ? "add" : "remove"]("active");
  };

  const showError = (msg) => {
    if (!errorBox) return;
    if (msg) {
      errorBox.style.display = "block";
      errorBox.textContent = msg;
    } else {
      errorBox.style.display = "none";
      errorBox.textContent = "";
    }
  };

  const renderRecommendations = (payload) => {
    if (!recList) return;
    recList.innerHTML = "";
    if (placeholderText) placeholderText.style.display = "none";

    if (!payload || !payload.data || payload.data.length === 0) {
      if (placeholderText) {
        placeholderText.style.display = "block";
        placeholderText.textContent = "Không có kết quả.";
      }
      if (pageInfo) pageInfo.textContent = "Trang 1/1 (0 kết quả)";
      if (paginationBox) paginationBox.style.display = "none";
      return;
    }

    payload.data.forEach((rec) => {
      const li = document.createElement("li");
      const score = document.createElement("div");
      score.className = "score";
      score.textContent = (rec.score ?? 0).toFixed(2);

      const info = document.createElement("div");
      const title = document.createElement("p");
      title.className = "title";
      title.textContent = rec?.metadata?.title || rec.title || `Phim ID: ${rec.movieId}`;

      const mid = document.createElement("p");
      mid.className = "movie-id";
      mid.textContent = `Mã phim (Movie ID): ${rec.movieId}`;

      info.appendChild(title);
      info.appendChild(mid);
      li.appendChild(score);
      li.appendChild(info);
      recList.appendChild(li);
    });

    if (pageInfo) {
      pageInfo.textContent = `Trang ${payload.page}/${payload.total_pages} (${payload.total_results} kết quả)`;
    }

    if (paginationBox) {
      paginationBox.style.display = payload.total_pages > 1 ? "flex" : "none";
      const prev = paginationBox.querySelector(".page-btn:first-child");
      const next = paginationBox.querySelector(".page-btn:last-child");
      if (prev) {
        prev.dataset.page = payload.page - 1;
        prev.disabled = payload.page <= 1;
      }
      if (next) {
        next.dataset.page = payload.page + 1;
        next.disabled = payload.page >= payload.total_pages;
      }
    }
  };

  const clearComparison = () => {
    if (compareSection) compareSection.style.display = "none";
    if (compareTable) compareTable.innerHTML = "";
    if (compareSummary) compareSummary.textContent = "";
  };

  const renderComparison = (dataA, dataB, labelA, labelB) => {
    if (!compareSection || !compareTable) return;
    compareSection.style.display = "block";
    compareTable.innerHTML = "";

    if (!dataA || !dataB || !dataA.data || !dataB.data || (!dataA.data.length && !dataB.data.length)) {
      if (compareSummary) {
        compareSummary.textContent = "Không có dữ liệu để so sánh.";
      }
      return;
    }

    const mapA = new Map((dataA.data || []).map((r) => [r.movieId, r]));
    const mapB = new Map((dataB.data || []).map((r) => [r.movieId, r]));
    const ids = new Set([...mapA.keys(), ...mapB.keys()]);

    const rows = [];
    ids.forEach((id) => {
      const a = mapA.get(id);
      const b = mapB.get(id);
      const title = a?.metadata?.title || a?.title || b?.metadata?.title || b?.title || `Phim ${id}`;
      const scoreA = a?.score ?? 0;
      const scoreB = b?.score ?? 0;
      rows.push({ id, title, scoreA, scoreB, maxScore: Math.max(scoreA, scoreB) });
    });

    rows.sort((x, y) => y.maxScore - x.maxScore);
    const topRows = rows.slice(0, 10);
    const maxScore = topRows.reduce((m, r) => Math.max(m, r.maxScore), 0) || 1;

    const intersect = [...mapA.keys()].filter((k) => mapB.has(k)).length;
    const union = ids.size || 1;
    const jaccard = (intersect / union) * 100;

    compareTable.innerHTML = "";
    topRows.forEach((r) => {
      const row = document.createElement("div");
      row.className = "compare-row";

      const title = document.createElement("div");
      title.className = "compare-title";
      title.textContent = r.title;

      const bars = document.createElement("div");
      bars.className = "bar-container";
      const barA = document.createElement("div");
      barA.className = "bar bar-a";
      barA.style.width = `${(r.scoreA / maxScore) * 100}%`;
      barA.title = `${labelA}: ${r.scoreA.toFixed(2)}`;

      const barB = document.createElement("div");
      barB.className = "bar bar-b";
      barB.style.width = `${(r.scoreB / maxScore) * 100}%`;
      barB.title = `${labelB}: ${r.scoreB.toFixed(2)}`;

      bars.appendChild(barA);
      bars.appendChild(barB);

      const scores = document.createElement("div");
      scores.className = "compare-scores";
      scores.textContent = `${labelA}: ${r.scoreA.toFixed(2)} | ${labelB}: ${r.scoreB.toFixed(2)} | Δ ${(r.scoreA - r.scoreB).toFixed(2)}`;

      row.appendChild(title);
      row.appendChild(bars);
      row.appendChild(scores);
      compareTable.appendChild(row);
    });

    if (compareSummary) {
      compareSummary.textContent = `Giao nhau: ${intersect}/${union} (Jaccard ~ ${jaccard.toFixed(1)}%), hiển thị top 10 theo điểm cao nhất.`;
    }
  };

  const getRecommendations = async (algorithm, page) => {
    const params = new URLSearchParams({
      user_id: state.userId,
      algorithm,
      page: String(page),
    });
    if (state.search) params.set("search", state.search);
    const res = await fetch(`/api/recommendations?${params.toString()}`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error || "Lỗi không xác định");
    }
    return data;
  };

  const loadPage = async (page = 1) => {
    if (!state.userId) return;
    setLoading(true);
    showError("");
    try {
      const dataA = await getRecommendations(state.algA, page);
      renderRecommendations(dataA);
      state.page = dataA.page;

      if (state.compare) {
        const dataB = await getRecommendations(state.algB, page);
        renderComparison(dataA, dataB, state.algA.toUpperCase(), state.algB.toUpperCase());
      } else {
        clearComparison();
      }
    } catch (err) {
      showError(err.message || "Lỗi không xác định");
      clearComparison();
    } finally {
      setLoading(false);
    }
  };

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      state.userId = document.getElementById("user_id")?.value || "";
      state.algA = algorithmSelect?.value || "hybrid";
      state.algB = algorithmBSelect?.value || "hybrid";
      state.search = searchInput?.value?.trim() || "";
      state.compare = compareToggle?.checked || false;
      loadPage(1);
    });
  }

  if (paginationBox) {
    paginationBox.addEventListener("click", (e) => {
      const btn = e.target.closest(".page-btn");
      if (!btn || btn.disabled) return;
      const p = parseInt(btn.dataset.page, 10);
      if (Number.isFinite(p)) {
        loadPage(p);
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", debounce(() => {
      state.search = searchInput.value.trim();
      if (state.userId) {
        loadPage(1);
      }
    }, 300));
  }

  if (compareToggle && algorithmBLabel) {
    algorithmBLabel.style.display = compareToggle.checked ? "block" : "none";
    compareToggle.addEventListener("change", () => {
      const show = compareToggle.checked;
      algorithmBLabel.style.display = show ? "block" : "none";
      state.compare = show;
      if (!show) {
        clearComparison();
      }
      if (show && !state.algB) {
        state.algB = "hybrid";
        if (algorithmBSelect) algorithmBSelect.value = "hybrid";
      }
    });
  }

  if (algorithmBSelect) {
    algorithmBSelect.addEventListener("change", () => {
      state.algB = algorithmBSelect.value;
    });
  }
});
