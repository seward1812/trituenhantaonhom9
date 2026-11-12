
document.addEventListener("DOMContentLoaded", function () {

    console.log("RouteOpt application started.");

    const navigationItems = document.querySelectorAll(".nav-item");

    navigationItems.forEach(item => {

        item.addEventListener("click", function () {

            navigationItems.forEach(nav => {
                nav.classList.remove("active");
            });

            this.classList.add("active");
        });

    });

});
