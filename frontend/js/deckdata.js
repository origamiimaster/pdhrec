let commanders = [];
function applyHash(hash) {
    if (hash == "about") {
        document.getElementById("main").style.display = "none"
        document.getElementById("staples").style.display = "none"
        document.getElementById("about").style.display = "block"
    } else if (hash == "staples") {
        document.getElementById("about").style.display = "none"
        document.getElementById("main").style.display = "none"
        document.getElementById("staples").style.display = "block"
    } else {
        document.getElementById("about").style.display = "none"
        document.getElementById("staples").style.display = "none"
        document.getElementById("main").style.display = "block"
    }
}

function init() {
    window.addEventListener("hashchange", (e) => {
        let hash = window.location.hash.substr(1);
        applyHash(hash)
    })
    applyHash(window.location.hash.substr(1))
}

window.onload = () => {
    init();
}

