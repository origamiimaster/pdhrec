$(window).on('load', function () {
    let button = $('.sort-button.active').get()[0]
    if (button.classList.contains("synergy")) {
        sortSynergy()
    } else if (button.classList.contains("popularity")) {
        sortPopularity()
    } else {
        sortTopNTypes()
    }
})

function sortSynergy() {
    removeHeaders()
    let itemsToSort = $(".gallery-item:not(:first-child)").get()
    itemsToSort.forEach(item => {
        $(item).show()
    })
    itemsToSort.sort((a, b) => {
        return parseFloat(a.getAttribute("synergy")) < parseFloat(b.getAttribute("synergy")) ? 1 : -1
    })
    for (let i = 60; i < itemsToSort.length; i++) {
        $(itemsToSort[i]).hide()
    }
    $(".sort-button").removeClass("active")
    $(".sort-button.synergy").addClass("active")
    let $sortedDivs = $(itemsToSort);
    $("#gallery").append($sortedDivs)
}

function sortPopularity() {
    removeHeaders()
    let itemsToSort = $(".gallery-item:not(:first-child)").get()
    itemsToSort.forEach(item => {
        $(item).show()
    })
    itemsToSort.sort((a, b) => {
        return parseFloat(a.getAttribute("popularity")) < parseFloat(b.getAttribute("popularity")) ? 1 : -1
    })
    for (let i = 60; i < itemsToSort.length; i++) {
        $(itemsToSort[i]).hide()
    }
    $(".sort-button").removeClass("active")
    $(".sort-button.popularity").addClass("active")
    let $sortedDivs = $(itemsToSort);
    $("#gallery").append($sortedDivs)
}

const TYPES = [
    "Creature",
    "Instant",
    "Sorcery",
    "Artifact",
    "Enchantment",
    "Land",
]

function sortTopNTypes() {
    let itemsToSort = $('.gallery-item:not(:first-child)').get()
    itemsToSort.forEach(item => {
        $(item).show()
    })

    itemsToSort.sort((a, b) => {
        return parseFloat(a.getAttribute("synergy")) < parseFloat(b.getAttribute("synergy")) ? 1 : -1
    })
    let categories = {
        "Creature": [],
        "Instant": [],
        "Sorcery": [],
        "Artifact": [],
        "Enchantment": [],
        "Land": [],
        "Other": [],
    }
    for (let i = 0; i < itemsToSort.length; i++) {
        if (itemsToSort[i].getAttribute("typeline").includes("Creature")) {
            categories.Creature.push(itemsToSort[i])
        } else if (itemsToSort[i].getAttribute("typeline").includes("Instant")) {
            categories.Instant.push(itemsToSort[i])
        } else if (itemsToSort[i].getAttribute("typeline").includes("Sorcery")) {
            categories.Sorcery.push(itemsToSort[i])
        } else if (itemsToSort[i].getAttribute("typeline").includes("Land")) {
            categories.Land.push(itemsToSort[i])
        } else if (itemsToSort[i].getAttribute("typeline").includes("Artifact")) {
            categories.Artifact.push(itemsToSort[i])
        } else if (itemsToSort[i].getAttribute("typeline").includes("Enchantment")) {
            categories.Enchantment.push(itemsToSort[i])
        } else {
            console.log("What happened hered")
            console.log(itemsToSort[i])
            categories.Other.push(itemsToSort[i])
        }
    }
    Object.keys(categories).forEach(category => {
        for (let i = 8; i < categories[category].length; i++) {
            $(categories[category][i]).hide();
        }
    })


    itemsToSort = []
    let header = createHeader("Creatures")
    header.style.paddingTop = 0;
    itemsToSort.push(header)
    itemsToSort.push(...categories.Creature)
    itemsToSort.push(createHeader("Instants"))
    itemsToSort.push(...categories.Instant)
    itemsToSort.push(createHeader("Sorceries"))
    itemsToSort.push(...categories.Sorcery)
    itemsToSort.push(createHeader("Artifacts"))
    itemsToSort.push(...categories.Artifact)
    itemsToSort.push(createHeader("Enchantments"))
    itemsToSort.push(...categories.Enchantment)
    itemsToSort.push(createHeader("Lands"))
    itemsToSort.push(...categories.Land)
    itemsToSort.push(...categories.Other)


    $(".sort-button").removeClass("active")
    $(".sort-button.types").addClass("active")
    let $sortedDivs = $(itemsToSort);
    $("#gallery").append($sortedDivs)
}


function removeHeaders() {
    $('.type-header').remove()

}

function createHeader(title) {
    let header = document.createElement('div')
    header.classList.add("type-header")
    header.classList.add("gallery-item")
    header.innerHTML = title
    return header
}