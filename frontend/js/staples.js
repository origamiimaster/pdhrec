let colors = "WBURG";
gtag('event', 'page-view', {name: "staples"});
window.onload = () => {
    $(".symbolW").parent()[0].addEventListener("click", (e)=>{
        if (e.currentTarget.className == "active") {
            colors = colors.replaceAll("W", "")
            e.currentTarget.className = "";
        } else {
            e.currentTarget.className = "active"
            colors += "W"
        }
        changeColors()
    })
    $(".symbolU").parent()[0].addEventListener("click", (e)=>{
        if (e.currentTarget.className == "active") {
            colors = colors.replaceAll("U", "")
            e.currentTarget.className = "";
        } else {
            e.currentTarget.className = "active"
            colors += "U"
        }
        changeColors()
    })
    $(".symbolB").parent()[0].addEventListener("click", (e)=>{
        if (e.currentTarget.className == "active") {
            e.currentTarget.className = "";
            colors = colors.replaceAll("B", "")
        } else {
            e.currentTarget.className = "active"
            colors += "B"
        }
        changeColors()
    })
    $(".symbolR").parent()[0].addEventListener("click", (e)=>{
        if (e.currentTarget.className == "active") {
            e.currentTarget.className = "";
            colors = colors.replaceAll("R", "")
        } else {
            e.currentTarget.className = "active"
            colors += "R"
        }
        changeColors()
    })
    $(".symbolG").parent()[0].addEventListener("click", (e)=>{
        if (e.currentTarget.className == "active") {
            e.currentTarget.className = "";
            colors = colors.replaceAll("G", "")
        } else {
            e.currentTarget.className = "active"
            colors += "G"
        }
        changeColors()
    })
    changeColors()
}


function changeColors() {
    $('#gallery').find('.gallery-item').hide()
    let things = $('#gallery').find(".gallery-item");
    let soFar = [];
    for (let i = 1; i < things.length; i++){
        let tempColors = things[i].getAttribute("color-identity");
        flag = true;
        tempColors.split("").forEach(color=>{
            if (colors.indexOf(color) == -1){
                flag = false;
            }
        })
        if (flag) {
            soFar.push(things[i])
        }
    }
    $("#gallery").find(".gallery-item").first().show()
    let endSlice = soFar.length - (soFar.length % 12)
    if (endSlice > 96) {
        endSlice = 96;
    }
    $(soFar).slice(0, endSlice).show()
}
