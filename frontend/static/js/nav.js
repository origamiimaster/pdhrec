$(document).ready(() => {
    $(".mobile-nav").hide();
    let mobile_menu_toggle = false;
    $(".nav-menu-button").click(() => {
        if (mobile_menu_toggle == false) {
            $(".mobile-nav").show();
        } else {
            $(".mobile-nav").hide();
        }
        mobile_menu_toggle = !mobile_menu_toggle;
    })


    function autocomplete(inp, arr) {
        var currentFocus;
        inp.addEventListener("input", function (e) {
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
                    b.innerHTML += `<input type="hidden" value="${arr[i]}">`
                    b.addEventListener("click", function (e) {
                        console.log("Clicked", this.getElementsByTagName("input")[0].value)
                        inp.value = this.getElementsByTagName("input")[0].value;
                        closeAllLists();
                        // $('form').submit()
                        window.location.href = "/commander/"+ inp.value.replaceAll(" ", "-").toLowerCase().replaceAll(",", "").replaceAll("'", "")
                    });
                    a.appendChild(b);
                }
            }
            
        });
        inp.addEventListener("keydown", function (e) {
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
                if (arr.indexOf(inp.value) != -1) {
                    window.location.href = "/commander/"+ inp.value.replaceAll(" ", "-").toLowerCase().replaceAll(",", "").replaceAll("'", "")
                } else {
                    e.preventDefault();
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

    $.get("/commandernames.json", (data) => {
        let commanderNames = []
        // data = JSON.parse(data)
        data.forEach((obj) => {
            commanderNames.push(obj)
        })
        autocomplete(document.getElementById("nav-search-field"), commanderNames)
    })
    // $.get("/counter", (data) => {
    //      $('#footer-flex').append($(`<p>Site visited ${data["count"]} times.</p>`))
    // })
})