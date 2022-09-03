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
    $.get(window.location.pathname + "?format=json", (data) => {
        $("#gallery").append("<div id='commander-information' class='gallery-item' style='width: 100%; display: flex;'></div>")
        data = JSON.parse(data);
        let img = document.createElement("img");
        img.className = "gallery-item"
        img.setAttribute("loading", "lazy")
        img.alt = "Image"
        img.src = data['commander']['urls'][0]

        
        img.alt = data['commander']['commanders'].join(" ");

        document.getElementById("commander-information").appendChild(img)

        $("#commander-information").append(`<div class="big-gallery-item">${data['commander']['commanders'].join(" and ")} <br /> In ${data["commander"]["count"]} decks.</div>`)

        cards = []
        Object.keys(data['cards']).forEach((thing) => {
            cards.push([thing, data['cards'][thing]])
        })
        cards.sort((a, b) => {
            if (a[1] > b[1]) {
                return -1;
            } else if (a[1] < b[1]) {
                return 1;
            } else {
                return 0;
            }
        })


        let gallery = document.getElementById("gallery")
        let count = 0;
        let commanderNames = [];
        cards.forEach(obj => {
            count += 1
            if (count <= 100) {
                let new_box = document.createElement("a");
                new_box.className = "gallery-item"
                let img = document.createElement("img")
                img.setAttribute("loading", "lazy")
                img.alt = "Image"
                placeholder = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASoAAAGfCAQAAABCNFdiAAAC4UlEQVR42u3SQREAAAzCsOHf9EzwI5HQaw7KIgGmwlSYCkyFqTAVmApTYSowFabCVGAqTIWpwFSYClNhKjAVpsJUYCpMhanAVJgKU4GpMBWmAlNhKkyFqcBUmApTgakwFaYCU2EqTAWmwlSYCkyFqTAVmApTYSpMBabCVJgKTIWpMBWYClNhKjAVpsJUYCpMhakwFZgKU2EqMBWmwlRgKkyFqcBUmApTgakwFabCVBJgKkyFqcBUmApTgakwFaYCU2EqTAWmwlSYCkyFqTAVpgJTYSpMBabCVJgKTIWpMBWYClNhKjAVpsJUmApMhakwFZgKU2EqMBWmwlRgKkyFqcBUmApTgakwFabCVGAqTIWpwFSYClOBqTAVpgJTYSpMBabCVJgKU4GpMBWmAlNhKkwFpsJUmApMhakwFZgKU2EqTCUBpsJUmApMhakwFZgKU2EqMBWmwlRgKkyFqcBUmApTYSowFabCVGAqTIWpwFSYClOBqTAVpgJTYSpMhanAVJgKU4GpMBWmAlNhKkwFpsJUmApMhakwFZgKU2EqTAWmwlSYCkyFqTAVmApTYSowFabCVGAqTIWpMBWYClNhKjAVpsJUYCpMhanAVJgKU4GpMBWmwlQSYCpMhanAVJgKU4GpMBWmAlNhKkwFpsJUmApMhakwFaYCU2EqTAWmwlSYCkyFqTAVmApTYSowFabCVJgKTIWpMBWYClNhKjAVpsJUYCpMhanAVJgKU4GpMBWmwlRgKkyFqcBUmApTgakwFaYCU2EqTAWmwlSYClOBqTAVpgJTYSpMBabCVJgKTIWpMBWYClNhKkwlAabCVJgKTIWpMBWYClNhKjAVpsJUYCpMhanAVJgKU2EqMBWmwlRgKkyFqcBUmApTgakwFaYCU2EqTIWpwFSYClOBqTAVpgJTYSpMBabCVJgKTIWpMBWYClNhKkwFpsJUmApMhakwFZgKU2EqMBWmwlRgKkyFqRj2SwUBoCOf66IAAAAASUVORK5CYII="
                try {
                    img.src = placeholder
                    let info_box = document.createElement("div");
                    info_box.className = "info"
                    info_box.innerHTML = obj[0] + ": " + Math.round(obj[1] * 10000) / 100 + "%"

                    img.alt = obj[0]
                    img.classList.add("lazy")
                    let img_url = "https://api.scryfall.com/cards/named?fuzzy="
                    img_url += encodeURIComponent(obj[0]);
                    img.setAttribute('data-src', img_url)
                    new_box.appendChild(img)
                    new_box.appendChild(info_box)
                } catch (e) {
                    console.log(e)
                }
                gallery.appendChild(new_box)
            }
        })
        var lazyloadImages;
        if ("IntersectionObserver" in window) {
            lazyloadImages = document.querySelectorAll(".lazy");
            var imageObserver = new IntersectionObserver(function (entries, observer) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        var image = entry.target;
                        $(window).queue(() => {
                            $.get(image.dataset.src, (response) => {
                                try {
                                    if (response['image_uris'] == undefined) {
                                        image.src = response['card_faces'][0]['image_uris']['normal']
                                    }
                                    image.src = response['image_uris']['normal']
                                } catch (e) {
                                    console.log("Image didn't load", e);
                                }
                                image.classList.remove("lazy");
                                imageObserver.unobserve(image);
                                $(window).delay(50).dequeue();
                            })
                        })
                    }
                });
            });
            lazyloadImages.forEach(function (image) {
                imageObserver.observe(image);
            });
        } else {
            console.log("Not observer")
            var lazyloadThrottleTimeout;
            lazyloadImages = document.querySelectorAll(".lazy");

            function lazyload() {
                if (lazyloadThrottleTimeout) {
                    clearTimeout(lazyloadThrottleTimeout);
                }

                lazyloadThrottleTimeout = setTimeout(function () {
                    var scrollTop = window.pageYOffset;
                    lazyloadImages.forEach(function (img) {
                        if (img.offsetTop < (window.innerHeight + scrollTop)) {
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                        }
                    });
                    if (lazyloadImages.length == 0) {
                        document.removeEventListener("scroll", lazyload);
                        window.removeEventListener("resize", lazyload);
                        window.removeEventListener("orientationChange", lazyload);
                    }
                }, 20);
            }

            document.addEventListener("scroll", lazyload);
            window.addEventListener("resize", lazyload);
            window.addEventListener("orientationChange", lazyload);
        }
    })
}

