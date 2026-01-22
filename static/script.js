const searchInput = document.getElementById("searchInput");
const suggestions = document.getElementById("suggestions");

searchInput?.addEventListener("input", async () => {
    const query = searchInput.value;
    if (!query) {
        suggestions.innerHTML = "";
        return;
    }

    try {
        const res = await fetch(`/autocomplete?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        console.log("Autocomplete data:", data); // debug

        suggestions.innerHTML = "";

        data.forEach(item => {
            const li = document.createElement("li");
            li.textContent = item.title;
            li.onclick = () => {
                searchInput.value = item.title;
                suggestions.innerHTML = "";
            };
            suggestions.appendChild(li);
        });
    } catch (e) {
        console.error("Autocomplete fetch error:", e);
    }
});


