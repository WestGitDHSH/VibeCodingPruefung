function toggleTheme(){
document.body.classList.toggle("dark");
}

function toggleMenu(button) {
    const menu = button.nextElementSibling;

    // andere Menüs schließen
    document.querySelectorAll(".menu-dropdown").forEach(m => {
        if (m !== menu) m.style.display = "none";
    });

    menu.style.display = menu.style.display === "block" ? "none" : "block";
}

// Klick außerhalb schließt Menü
window.onclick = function(event) {
    if (!event.target.matches('.menu-btn')) {
        document.querySelectorAll(".menu-dropdown").forEach(m => {
            m.style.display = "none";
        });
    }
}

function confirmDelete() {
    return confirm("Soll dieser Client wirklich gelöscht werden?");
}