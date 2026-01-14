document.addEventListener("click",(e) =>{
    const th =e.target.closest("th[data-sort]");
    if (!th) return;
    const key = th.getAttribute("data-sort");
    const table = th.closest("table");
    const tbody = table.querySelector("tbody");


    const rows = Array.from(tbody.querySelectorAll("tr"))
        .filter(r => r.querySelector(`[data-key="${key}"]`))

    const asc = th.dataset-asc === "true" ? false : true;
    th.dataset.asc = asc;

    rows.sort((a, b) => {
        const av = a.querySelector(`[data-key="${key}"]`)?.textContent.trim().toLowerCase() || "";
        const bv = b.querySelector(`[data-key="${key}"]`)?.textContent.trim().toLowerCase() || "";
        if (av < bv) return asc ? -1 : 1;
        if (av > bv) return asc ? 1 : -1;
        return 0;
    });


    rows.forEach(r => tbody.appendChild(r));
})

