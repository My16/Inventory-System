document.addEventListener("DOMContentLoaded", function () {
    // --- Make dropdown scrollable (only 8 visible) ---
    const notifDropdown = document.querySelector(".notifications-dropdown");
    if (notifDropdown) {
        const itemHeight = 45; // adjust if your items are taller
        notifDropdown.style.maxHeight = `${itemHeight * 8}px`;
        notifDropdown.style.overflowY = "auto";
    }

    // --- Animate a row in service request page ---
    function scrollAndAnimate(row) {
        const rowTop = row.getBoundingClientRect().top + window.pageYOffset;
        const navbarHeight = document.querySelector(".navbar")?.offsetHeight || 0;
        const scrollTo = rowTop - navbarHeight - 10;

        window.scrollTo({ top: scrollTo, behavior: "smooth" });

        row.classList.add("row-zoom-highlight");
        setTimeout(() => row.classList.remove("row-zoom-highlight"), 600);
    }

    // --- Handle notification clicks globally ---
    const notifLinks = document.querySelectorAll(".dropdown-item[data-notif-id]");
    const badge = document.querySelector(".badge");

    notifLinks.forEach((link) => {
        if (!link.classList.contains("clicked")) {
            link.classList.add("notif-highlight");
        }

        link.addEventListener("click", function (event) {
            event.preventDefault();

            const notifId = this.dataset.notifId;
            const target = new URL(this.href);

            // Mark notification as read via Django endpoint
            fetch(`/notifications/mark-read/${notifId}/`)
                .then((res) => res.json())
                .then((data) => {
                    if (data.success) {
                        // Update badge count
                        let count = parseInt(badge?.textContent) || 0;
                        count = Math.max(count - 1, 0);
                        if (badge) {
                            badge.textContent = count;
                            if (count === 0) badge.style.display = "none";
                        }

                        // Remove highlight
                        this.classList.remove("notif-highlight");
                        this.classList.add("clicked");
                    }
                })
                .catch(() => {
                    console.warn("Failed to mark notification as read");
                })
                .finally(() => {
                    // Navigate to target page
                    if (target.hash) {
                        // If same page → animate row without reload
                        if (window.location.pathname === target.pathname) {
                            const row = document.querySelector(target.hash);
                            if (row) scrollAndAnimate(row);
                        } else {
                            // If different page → store for animation after reload
                            localStorage.setItem("highlightRow", target.hash);
                            window.location.href = this.href;
                        }
                    } else {
                        window.location.href = this.href;
                    }
                });
        });
    });

    // --- On page load: check if a row needs animation ---
    const hash = window.location.hash || localStorage.getItem("highlightRow");
    if (hash) {
        const row = document.querySelector(hash);
        if (row) scrollAndAnimate(row);
        localStorage.removeItem("highlightRow");
    }
});
