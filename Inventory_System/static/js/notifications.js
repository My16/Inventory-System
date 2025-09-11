// notifications.js
document.addEventListener("DOMContentLoaded", function () {
    const badge = document.querySelector("#notifBadge");
    const dropdown = document.querySelector("#notifDropdown + .dropdown-menu");

    if (!dropdown) return;

    // 🔹 Get CSRF token from cookie
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

    // Click → mark as read
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
            .then((res) => res.json())
            .then((data) => {
                if (data.success && badge) {
                    // update badge count
                    let count = parseInt(badge.textContent) || 0;
                    count = Math.max(count - 1, 0);
                    badge.textContent = count;

                    if (count === 0) {
                        badge.classList.add("d-none");
                    }

                    // remove notification item from dropdown
                    const li = link.closest("li");
                    if (li) li.remove();
                }
            })
            .catch(() => console.warn("Failed to mark notification as read"))
            .finally(() => {
                // navigate after marking as read
                window.location.href = link.href;
            });
    });

    // Fetch + render
    function fetchNotifications() {
        fetch("/notifications/latest/")
            .then((res) => res.json())
            .then((data) => {
                if (!dropdown) return;

                // update badge
                if (badge) {
                    if (data.unread_count > 0) {
                        badge.classList.remove("d-none");
                        badge.textContent = data.unread_count;
                    } else {
                        badge.classList.add("d-none");
                    }
                }

                // rebuild dropdown with header + notifications + footer
                let html = `
                    <li class="dropdown-header fw-bold">Notifications</li>
                `;

                if (data.notifications.length > 0) {
                    data.notifications.forEach((notif) => {
                        html += `
                            <li>
                                <a class="dropdown-item ${notif.is_read ? "" : "notif-highlight"}"
                                   href="${notif.url}"
                                   data-notif-id="${notif.id}">
                                    ${notif.message} <br>
                                    <small class="text-muted">${notif.created_at}</small>
                                </a>
                            </li>
                        `;
                    });
                } else {
                    html += `<li class="dropdown-item text-muted">No new notifications</li>`;
                }

                html += `
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item text-center text-primary" href="#">View All</a></li>
                `;

                dropdown.innerHTML = html;
            })
            .catch(() => console.warn("Failed to fetch notifications"));
    }

    // initial + interval fetch
    fetchNotifications();
    setInterval(fetchNotifications, 10000);
});
