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
    window.addEventListener("hashchange", (e)=>{
        let hash = window.location.hash.substr(1);
        applyHash(hash)
    })
    applyHash(window.location.hash.substr(1))
}

function autocomplete(inp, arr) {
    var currentFocus;
    inp.addEventListener("input", function(e) {
      var a, b, i, val = this.value;
      closeAllLists();
      if (!val) {
      return false;
      }
      currentFocus = -1;
      a = document.createElement("DIV");
      a.setAttribute("id", this.id + "-autocomplete-list");
      a.setAttribute("class", "autocomplete-items");
      this.parentNode.appendChild(a);
      for (i = 0; i < arr.length; i++) {
        if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
          b = document.createElement("DIV");
          b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
          b.innerHTML += arr[i].substr(val.length);
          b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
              b.addEventListener("click", function(e) {
              inp.value = this.getElementsByTagName("input")[0].value;
              closeAllLists();
          });
          a.appendChild(b);
        }
      }
    });
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "-autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            currentFocus++;
            addActive(x);
        } else if (e.keyCode == 38) { //up
            currentFocus--;
            addActive(x);
        } else if (e.keyCode == 13) {
            if (currentFocus > -1) {
                e.preventDefault();
                if (x) x[currentFocus].click();
                currentFocus = -1;
            }
        }
    });
    function addActive(x) {
        if (!x) return false;
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
        for (var i = 0; i < x.length; i++) {
          x[i].classList.remove("autocomplete-active");
        }
    }
    function closeAllLists(elmnt) {
        var x = document.getElementsByClassName("autocomplete-items");
        for (var i = 0; i < x.length; i++) {
            if (elmnt != x[i] && elmnt != inp) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}

window.onload = ()=>{
    init();
    $.get("/top-commanders", (data)=>{
        data = JSON.parse(data)
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

        let gallery = document.getElementById("gallery")
        let count = 0;
        let commanderNames = [];
        commanders.forEach(obj => {
            count += 1
            if (count <= 100) {
                let new_box = document.createElement("a");
                new_box.target="_blank"
                new_box.href = "/commander/" + obj.commanderstring
                new_box.className = "gallery-item"
                let img = document.createElement("img")
                img.setAttribute("loading", "lazy")
                img.alt = "Image"
                placeholder = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASoAAAGfCAQAAABCNFdiAAAC4UlEQVR42u3SQREAAAzCsOHf9EzwI5HQaw7KIgGmwlSYCkyFqTAVmApTYSowFabCVGAqTIWpwFSYClNhKjAVpsJUYCpMhanAVJgKU4GpMBWmAlNhKkyFqcBUmApTgakwFaYCU2EqTAWmwlSYCkyFqTAVmApTYSpMBabCVJgKTIWpMBWYClNhKjAVpsJUYCpMhakwFZgKU2EqMBWmwlRgKkyFqcBUmApTgakwFabCVBJgKkyFqcBUmApTgakwFaYCU2EqTAWmwlSYCkyFqTAVpgJTYSpMBabCVJgKTIWpMBWYClNhKjAVpsJUmApMhakwFZgKU2EqMBWmwlRgKkyFqcBUmApTgakwFabCVGAqTIWpwFSYClOBqTAVpgJTYSpMBabCVJgKU4GpMBWmAlNhKkwFpsJUmApMhakwFZgKU2EqTCUBpsJUmApMhakwFZgKU2EqMBWmwlRgKkyFqcBUmApTYSowFabCVGAqTIWpwFSYClOBqTAVpgJTYSpMhanAVJgKU4GpMBWmAlNhKkwFpsJUmApMhakwFZgKU2EqTAWmwlSYCkyFqTAVmApTYSowFabCVGAqTIWpMBWYClNhKjAVpsJUYCpMhanAVJgKU4GpMBWmwlQSYCpMhanAVJgKU4GpMBWmAlNhKkwFpsJUmApMhakwFaYCU2EqTAWmwlSYCkyFqTAVmApTYSowFabCVJgKTIWpMBWYClNhKjAVpsJUYCpMhanAVJgKU4GpMBWmwlRgKkyFqcBUmApTgakwFaYCU2EqTAWmwlSYClOBqTAVpgJTYSpMBabCVJgKTIWpMBWYClNhKkwlAabCVJgKTIWpMBWYClNhKjAVpsJUYCpMhanAVJgKU2EqMBWmwlRgKkyFqcBUmApTgakwFaYCU2EqTIWpwFSYClOBqTAVpgJTYSpMBabCVJgKTIWpMBWYClNhKkwFpsJUmApMhakwFZgKU2EqMBWmwlRgKkyFqRj2SwUBoCOf66IAAAAASUVORK5CYII="
                try {
                    let info_box = document.createElement("div");
                    info_box.className = "info"
                    info_box.innerHTML = "In " + obj.count + " decks"
                    if (obj.commanders.length == 1) {
                        img.alt = obj.commanders[0]
                        img.src = placeholder
                        img.classList.add("lazy")
                        img.setAttribute('data-src', obj.urls[0])
                        new_box.appendChild(img)
                        new_box.appendChild(info_box)
                        commanderNames.push(obj.commanders[0])
                    } else {
                        let partners = document.createElement("div")
                        partners.className = "partners"
                        img.className = "partner1"
                        img.classList.add("lazy")
                        img.src = placeholder
                        img.setAttribute('data-src', obj.urls[0])
                        img.alt = obj.commanders[0]
                        let img2 = document.createElement("img")
                        img2.setAttribute("loading", "lazy")
                        img2.className = "partner2"
                        img2.classList.add("lazy")
                        img2.src = placeholder
                        img2.setAttribute('data-src', obj.urls[1])
                        img2.alt = obj.commanders[1]
                        partners.appendChild(img)
                        partners.appendChild(img2)
                        new_box.appendChild(partners)
                        partners.appendChild(info_box)
                        commanderNames.push(obj.commanders.join(" "))
                    }
                } catch(e){
                	console.log(e)
                }
                gallery.appendChild(new_box)
            }
        })
        autocomplete(document.getElementById("nav-search-field"), commanderNames)
          var lazyloadImages;
          if ("IntersectionObserver" in window) {
            lazyloadImages = document.querySelectorAll(".lazy");
            var imageObserver = new IntersectionObserver(function(entries, observer) {
              entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                  var image = entry.target;
                  image.src = image.dataset.src;
                  image.classList.remove("lazy");
                  imageObserver.unobserve(image);
                }
              });
            });
            lazyloadImages.forEach(function(image) {
              imageObserver.observe(image);
            });
          } else {
              console.log("Not observer")
            var lazyloadThrottleTimeout;
            lazyloadImages = document.querySelectorAll(".lazy");

            function lazyload () {
              if(lazyloadThrottleTimeout) {
                clearTimeout(lazyloadThrottleTimeout);
              }

              lazyloadThrottleTimeout = setTimeout(function() {
                var scrollTop = window.pageYOffset;
                lazyloadImages.forEach(function(img) {
                    if(img.offsetTop < (window.innerHeight + scrollTop)) {
                      img.src = img.dataset.src;
                      img.classList.remove('lazy');
                    }
                });
                if(lazyloadImages.length == 0) {
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

