let commanders = [];
function applyHash(hash) {
    if (hash == "about") {
        document.getElementById("main").style.display = "none"
        document.getElementById("about").style.display = "block"
    } else if (hash == "staples") {
        document.getElementById("about").style.display = "none"
        document.getElementById("main").style.display = "none"
    } else {
        document.getElementById("about").style.display = "none"
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
    $('#gallery').find('.gallery-item').hide()
    $("#gallery").find(".gallery-item").slice(0, 96).show()
}

function changeColors() {
    // console.log("Called")
    $('#gallery').find('.gallery-item').hide()
    switch ($("#colors")[0].value) {
        case "White":
            $("#gallery").find(".gallery-item[color-identity=W]").slice(0, 96).show()
            break;
        case "Black":
            $('#gallery').find(`.gallery-item[color-identity=B]`).slice(0, 96).show()
            break;
        case "Blue":
            $('#gallery').find(`.gallery-item[color-identity=U]`).slice(0, 96).show()
            break;
        case "Red":
            $('#gallery').find(`.gallery-item[color-identity=R]`).slice(0, 96).show()
            break;
        case "Green":
            $('#gallery').find(`.gallery-item[color-identity=G]`).slice(0, 96).show()
            break;
        default:
            $('#gallery').find('.gallery-item').hide()
            $('#gallery').find(`.gallery-item`).slice(0, 96).show()
    }
}
