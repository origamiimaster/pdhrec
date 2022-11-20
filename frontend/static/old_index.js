function showAbout(){
    document.getElementById("main").style.display = "none";
    document.getElementById("contact").style.display = "none";
    document.getElementById("commander").style.display = "none";
    document.getElementById("about").style.display = "block"
}

function showContact(){
    document.getElementById("main").style.display = "none";
    document.getElementById("about").style.display = "none"
    document.getElementById("commander").style.display = "none";
    document.getElementById("contact").style.display = "block";
}

function showHome(){
    document.getElementById("contact").style.display = "none";
    document.getElementById("commander").style.display = "none";
    document.getElementById("about").style.display = "none";
    document.getElementById("main").style.display = "block";
}
function showCommander(){
    document.getElementById("contact").style.display = "none";
    document.getElementById("about").style.display = "none";
    document.getElementById("main").style.display = "none";
    document.getElementById("commander").style.display = "block";
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
    } else if (hash == "commander"){
        showCommander()
    } else {
        showHome();
    }

    document.getElementById("search").addEventListener("keydown", (e)=>{
        if (e.key == "Enter") {
            let input = document.getElementById("search").value
            input = input.toLowerCase().replaceAll(" ", "_").replace(/\W/g, '').replaceAll("_", "-")
            doSearch(input)
        }
    })
}

function autocomplete(inp, arr) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
      var a, b, i, val = this.value;
      /*close any already open lists of autocompleted values*/
      closeAllLists();
      if (!val) { return false;}
      currentFocus = -1;
      /*create a DIV element that will contain the items (values):*/
      a = document.createElement("DIV");
      a.setAttribute("id", this.id + "autocomplete-list");
      a.setAttribute("class", "autocomplete-items");
      /*append the DIV element as a child of the autocomplete container:*/
      this.parentNode.appendChild(a);
      /*for each item in the array...*/
      for (i = 0; i < arr.length; i++) {
        /*check if the item starts with the same letters as the text field value:*/
        if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
          /*create a DIV element for each matching element:*/
          b = document.createElement("DIV");
          /*make the matching letters bold:*/
          b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
          b.innerHTML += arr[i].substr(val.length);
          /*insert a input field that will hold the current array item's value:*/
          b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
          /*execute a function when someone clicks on the item value (DIV element):*/
              b.addEventListener("click", function(e) {
              /*insert the value for the autocomplete text field:*/
              inp.value = this.getElementsByTagName("input")[0].value;
              /*close the list of autocompleted values,
              (or any other open lists of autocompleted values:*/
              closeAllLists();
          });
          a.appendChild(b);
        }
      }
    });
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            /*If the arrow DOWN key is pressed,
            increase the currentFocus variable:*/
            currentFocus++;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 13) {
            /*If the ENTER key is pressed, prevent the form from being submitted,*/
            e.preventDefault();
            if (currentFocus > -1) {
                /*and simulate a click on the "active" item:*/
                if (x) x[currentFocus].click();
            }
        }
    });
    function addActive(x) {
        /*a function to classify an item as "active":*/
        if (!x) return false;
        /*start by removing the "active" class on all items:*/
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        /*add class "autocomplete-active":*/
        x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
    }
    function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
      x[i].parentNode.removeChild(x[i]);
    }
  }
}
    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}

let test = ["Alphabet", "Some", "test", "Stuff", "other"]



function doSearch(commanderstring) {
    location.href = "/commander/" + commanderstring
}

let commanders = [];
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

        let gallery = document.createElement("div")
        gallery.className = "gallery"
        document.getElementById("main").appendChild(gallery)
        let count = 0;
        commanders.forEach(obj => {
            count += 1
            if (count <= 100) {
                let new_box = document.createElement("a");
                new_box.target="_blank"
                new_box.href = "/commander/" + obj.commanderstring
                new_box.className = "card"
                let img = document.createElement("img")
                img.src = "https://c1.scryfall.com/file/scryfall-cards/large/front/8/0/8059c52b-5d25-4052-b48a-e9e219a7a546.jpg?1594736914Y"
                img.alt = "Image"
                try {
                    let info_box = document.createElement("div");
                    info_box.className = "info"
                    info_box.innerHTML = "In " + obj.count + " decks"

                    if (obj.commanders.length == 1) {
                         img.alt = obj.commanders[0]
                        img.src = obj.urls[0]
                        new_box.appendChild(img)
                        new_box.appendChild(info_box)
                    } else {
                        let partners = document.createElement("div")
                        partners.className = "partners"
                        img.className = "partner1"
                        img.src = obj.urls[0]
                        img.alt = obj.commanders[0]
                        let img2 = document.createElement("img")
                        img2.className = "partner2"
                        img2.src = obj.urls[1]
                        img2.alt = obj.commanders[1]
                        partners.appendChild(img)
                        partners.appendChild(img2)
                        new_box.appendChild(partners)
                        partners.appendChild(info_box)
                    }
                } catch(e){
                	console.log(e)
                }
                gallery.appendChild(new_box)
            }
            autocomplete(document.getElementById("search"), test)
        })
    })
}
