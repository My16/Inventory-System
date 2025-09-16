document.addEventListener("DOMContentLoaded", function () {
    const badge = document.querySelector("#notifBadge");
    const dropdown = document.querySelector("#notifDropdown + .dropdown-menu");

    if (!dropdown || !badge) return;

    // 🔹 Get CSRF token
    function getCSRFToken() {
        let cookieValue = null;
        document.cookie.split(";").forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = cookie.substring("csrftoken=".length);
            }
        });
        return cookieValue;
    }

    // 🔹 Scroll + zoom row
    function highlightRow(rowId) {
        const row = document.querySelector(`#row-${rowId}`);
        if (!row) return;

        row.classList.add("row-zoom-highlight");
        row.scrollIntoView({ behavior: "smooth", block: "center" });

        setTimeout(() => row.classList.remove("row-zoom-highlight"), 800);
    }

    // ✅ Only zoom on page load if came from notif
    const params = new URLSearchParams(window.location.search);
    if (window.location.hash.startsWith("#row-") && params.get("from") === "notif") {
        const rowId = window.location.hash.replace("#row-", "");
        setTimeout(() => highlightRow(rowId), 300); // wait for table render
    }

    // 🔹 Build dropdown list
    function renderNotifications(notifications) {
        dropdown.innerHTML = "";

        notifications.forEach(notif => {
            const item = document.createElement("a");
            // always append from=notif
            const notifUrl = new URL(notif.url, window.location.origin);
            notifUrl.searchParams.set("from", "notif");

            item.href = notifUrl.toString();
            item.textContent = notif.message;
            item.className = "dropdown-item";
            item.dataset.notifId = notif.id;

            if (!notif.is_read) {
                item.classList.add("notif-highlight");
            }

            dropdown.appendChild(item);
        });
    }

    // 🔹 Fetch latest notifications
    async function fetchNotifications() {
        try {
            const res = await fetch("/notifications/latest/");
            const data = await res.json();

            // Badge update
            if (data.unread_count > 0) {
                badge.style.display = "inline-block";
                badge.textContent = data.unread_count;
            } else {
                badge.style.display = "none";
            }

            renderNotifications(data.notifications);
        } catch (err) {
            console.warn("Failed to fetch notifications", err);
        }
    }

    // 🔹 Click event (mark read + scroll/zoom)
    dropdown.addEventListener("click", function (event) {
        const link = event.target.closest(".dropdown-item[data-notif-id]");
        if (!link) return;

        event.preventDefault();
        const notifId = link.dataset.notifId;

        fetch(`/notifications/mark-read/${notifId}/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    let count = parseInt(badge.textContent) || 0;
                    count = Math.max(count - 1, 0);
                    badge.textContent = count;
                    if (count === 0) badge.style.display = "none";

                    link.classList.remove("notif-highlight");
                    link.classList.add("clicked");
                }
            })
            .finally(() => {
                const targetUrl = new URL(link.href, window.location.origin);
                const currentUrl = new URL(window.location.href);

                if (targetUrl.pathname === currentUrl.pathname) {
                    // ✅ Already on same page → force reload
                    window.location.href = link.href;
                } else {
                    // Different page → normal navigation
                    window.location.href = link.href;
                }
            });
    });

    // 🔹 Run fetch immediately + poll every 10s
    fetchNotifications();
    setInterval(fetchNotifications, 10000);
});
