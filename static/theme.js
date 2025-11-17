function toggleTheme() {
    let theme = document.body.classList.toggle("dark");

    if (document.body.classList.contains("dark")) {
        localStorage.setItem("theme", "dark");
    } else {
        localStorage.setItem("theme", "light");
    }
}

window.onload = function () {
    let saved = localStorage.getItem("theme");
    if (saved === "dark") {
        document.body.classList.add("dark");
    }
};
