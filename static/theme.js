function toggleTheme(){
document.body.classList.toggle("dark");
}

function toggleMenu(button) {

    const menu = button.nextElementSibling;

    // andere Menüs schließen
    document.querySelectorAll(".menu-dropdown").forEach(m => {

        if (m !== menu) {
            m.style.display = "none";
        }

    });

    // aktuelles Menü togglen
    if (menu.style.display === "block") {
        menu.style.display = "none";
    } else {
        menu.style.display = "block";
    }
}


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