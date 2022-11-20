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
    $.get("/get-staples", (data) => {
        data = JSON.parse(data);
        cards = [data['cardcounts'], data['cardnames'], data['coloridentities']]
        cards = cards.map(
            (indices => a => indices.map(i => a[i]))
            ([...cards[0].keys()].sort((a, b) => cards[0][b] - cards[0][a]))
        );


        let gallery = document.getElementById("gallery")
        let count = 0;
        let commanderNames = [];

        for (let i = 0; i < cards[0].length; i++) {
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
                    info_box.innerHTML = cards[1][i] + ": " + cards[0][i]

                    img.alt = cards[1][i]
                    img.classList.add("lazy")
                    let img_url = "https://api.scryfall.com/cards/named?fuzzy="
                    img_url += encodeURIComponent(cards[1][i]);
                    img.setAttribute('data-src', img_url)
                    new_box.appendChild(img)
                    new_box.appendChild(info_box)
                    new_box.setAttribute("color-identity", JSON.stringify(cards[2][i]))
                } catch (e) {
                    console.log(e)
                }
                gallery.appendChild(new_box)
            }
        }
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

