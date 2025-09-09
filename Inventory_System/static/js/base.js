document.addEventListener("DOMContentLoaded", function () {
    const notifLinks = document.querySelectorAll(".dropdown-item[data-notif-id]");
    const badge = document.querySelector("#notifDropdown .badge");

    notifLinks.forEach((link) => {
        // Add green highlight if not yet clicked/read
        if (!link.classList.contains("clicked")) {
            link.classList.add("notif-highlight");
        }

        link.addEventListener("click", function (event) {
            event.preventDefault();

            const notifId = this.dataset.notifId;
            const target = new URL(this.href);

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

                        // Remove green highlight
                        this.classList.remove("notif-highlight");
                        this.classList.add("clicked");
                    }
                })
                .catch(() => console.warn("Failed to mark notification as read"))
                .finally(() => {
                    // Navigate to target page
                    window.location.href = this.href;
                });
        });
    });
});
