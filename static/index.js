function showAbout(){
    document.getElementById("main").style.display = "none";
    document.getElementById("contact").style.display = "none";
    document.getElementById("about").style.display = "block"
}

function showContact(){
    document.getElementById("main").style.display = "none";
    document.getElementById("about").style.display = "none"
    document.getElementById("contact").style.display = "block";
}

function showHome(){
    document.getElementById("contact").style.display = "none";
    document.getElementById("about").style.display = "none";
    document.getElementById("main").style.display = "block";
}
function init() {
    window.addEventListener("hashchange", (e)=>{
        let hash = window.location.hash.substr(1);
        if (hash == "contact") {
            showContact();
        } else if (hash == "about") {
            showAbout();
        } else {
            showHome();
        }
    })
    let hash = window.location.hash.substr(1);
    if (hash == "contact") {
        showContact();
    } else if (hash == "about") {
        showAbout();
    } else {
        showHome();
    }

    document.getElementById("search").addEventListener("keydown", (e)=>{
        if (e.key == "Enter") {
            doSearch()
        }
    })
}

function doSearch() {
    let input = document.getElementById("search").value
    input = input.toLowerCase().replaceAll(" ", "_").replace(/\W/g, '').replaceAll("_", "-")
    $.get("/commander/" + input, (data)=>{
        console.log(data)
    })
}

let commanders = [];
window.onload = ()=>{
    init();
    $.get("/top-commanders", (data)=>{
        data = JSON.parse(data)
        console.log(data)
        data.sort((a, b) =>{
            if (a.count > b.count ){
                return -1;
            } else if (a.count < b.count) {
                return 1
            } else {
                return 0;
            }
        })
        commanders = data;
        console.log("Starting")

        let gallery = document.createElement("div")
        gallery.className = "gallery"
        document.getElementById("main").appendChild(gallery)
        let count = 0;
        commanders.forEach(obj => {
            count += 1
            if (count <= 100) {
                let new_box = document.createElement("div");
                new_box.className = "card"
                let img = document.createElement("img")
                img.src = "https://c1.scryfall.com/file/scryfall-cards/large/front/8/0/8059c52b-5d25-4052-b48a-e9e219a7a546.jpg?1594736914Y"
                img.alt = "Image"
                let info_box = document.createElement("div");
                info_box.className = "info"
                info_box.innerHTML = "In " + obj.count + " decks"

                if (obj.commanders.length == 1) {
                    img.alt = obj.partner1[0].name
                    img.src = obj.partner1[0].image
                    new_box.appendChild(img)
                    new_box.appendChild(info_box)
                } else {
                    let partners = document.createElement("div")
                    partners.className = "partners"
                    img.className = "partner1"
                    img.src = obj.partner1[0].image
                    img.alt = obj.partner1[0].name
                    let img2 = document.createElement("img")
                    img2.className = "partner2"
                    img2.src = obj.partner2[0].image
                    img2.alt = obj.partner2[0].name

                    partners.appendChild(img)
                    partners.appendChild(img2)
                    new_box.appendChild(partners)
                    partners.appendChild(info_box)

                }
                gallery.appendChild(new_box)
            }

        })
    })
}
