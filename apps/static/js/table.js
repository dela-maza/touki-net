document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("tr.clickable-row").forEach(row => {
        row.addEventListener("click", (e) => {
            // 行内の a / button / svg クリックは除外
            if (e.target.closest("a, button, svg, path")) return;

            const href = row.dataset.href;
            if (!href) return;

            // Cmd(⌘) / Ctrl で新規タブ
            if (e.metaKey || e.ctrlKey) {
                window.open(href, "_blank");
            } else {
                window.location.href = href;
            }
        });
    });
});