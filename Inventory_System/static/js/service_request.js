document.addEventListener("DOMContentLoaded", function () {

    // -------------------------------
    // 1️⃣ Row scroll + zoom animation
    // -------------------------------
    function scrollAndAnimate(row) {
        if (!row) return;

        const rowTop = row.getBoundingClientRect().top + window.pageYOffset;
        const navbarHeight = document.querySelector(".navbar")?.offsetHeight || 0;
        const scrollTo = rowTop - navbarHeight - 10;

        window.scrollTo({ top: scrollTo, behavior: "smooth" });

        row.classList.remove("row-zoom-highlight");
        void row.offsetWidth; // force reflow
        row.classList.add("row-zoom-highlight");

        setTimeout(() => row.classList.remove("row-zoom-highlight"), 600);
    }

    // -------------------------------
    // 2️⃣ Highlight row on page load
    // -------------------------------
    const hash = window.location.hash || localStorage.getItem("highlightRow");
    if (hash) {
        const row = document.querySelector(hash);
        scrollAndAnimate(row);
        localStorage.removeItem("highlightRow");
    }

    // -------------------------------
    // 3️⃣ CSRF helper
    // -------------------------------
    function getCSRFToken() {
        let cookieValue = null;
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = cookie.substring("csrftoken=".length);
                break;
            }
        }
        return cookieValue;
    }

    // -------------------------------
    // 4️⃣ Notification click handling
    // -------------------------------
    const badge = document.querySelector("#notifBadge");
    const dropdown = document.querySelector("#notifDropdown + .dropdown-menu");

    if (dropdown) {
        dropdown.addEventListener("click", function (event) {
            const link = event.target.closest(".dropdown-item[data-notif-id]");
            if (!link) return;

            event.preventDefault();
            const notifId = link.dataset.notifId;

            // ✅ Mark as read via POST with CSRF
            fetch(`/notifications/mark-read/${notifId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.success && badge) {
                        // Update badge count
                        let count = parseInt(badge.textContent) || 0;
                        count = Math.max(count - 1, 0);
                        badge.textContent = count;
                        if (count === 0) badge.classList.add("d-none");

                        // Remove notification item from dropdown
                        const li = link.closest("li");
                        if (li) li.remove();
                    }
                })
                .catch(() => console.warn("Failed to mark notification as read"))
                .finally(() => {
                    // Scroll if it's the current page with a row hash
                    const target = new URL(link.href, window.location.origin);
                    const current = new URL(window.location.href);

                    if (target.pathname === current.pathname && target.hash) {
                        const rowId = target.hash.replace("#row-", "");
                        const row = document.querySelector(`#row-${rowId}`);
                        scrollAndAnimate(row);
                        history.pushState(null, "", link.href); // update URL without reload
                    } else {
                        // Navigate to another page
                        window.location.href = link.href;
                    }
                });
        });
    }

    // -------------------------------
    // 5️⃣ Poll server for new notifications every 10s
    // -------------------------------
    function fetchNotifications() {
        fetch("/notifications/latest/")
            .then((res) => res.json())
            .then((data) => {
                if (!dropdown || !badge) return;

                // Update badge
                if (data.unread_count > 0) {
                    badge.classList.remove("d-none");
                    badge.textContent = data.unread_count;
                } else {
                    badge.classList.add("d-none");
                }

                // Rebuild dropdown
                dropdown.innerHTML = "";
                if (data.notifications.length > 0) {
                    data.notifications.forEach((notif) => {
                        const li = document.createElement("li");
                        const item = document.createElement("a");
                        item.href = notif.url;
                        item.textContent = notif.message;
                        item.className = "dropdown-item";
                        item.dataset.notifId = notif.id;

                        if (!notif.is_read) item.classList.add("notif-highlight");

                        li.appendChild(item);
                        dropdown.appendChild(li);
                    });
                } else {
                    const li = document.createElement("li");
                    li.className = "dropdown-item text-muted";
                    li.textContent = "No new notifications";
                    dropdown.appendChild(li);
                }

                // Divider + footer
                const divider = document.createElement("li");
                divider.innerHTML = `<hr class="dropdown-divider">`;
                dropdown.appendChild(divider);

                const footer = document.createElement("li");
                footer.innerHTML = `<a class="dropdown-item text-center text-primary" href="#">View All</a>`;
                dropdown.appendChild(footer);
            })
            .catch(() => console.warn("Failed to fetch notifications"));
    }

    fetchNotifications();
    setInterval(fetchNotifications, 10000);
});
