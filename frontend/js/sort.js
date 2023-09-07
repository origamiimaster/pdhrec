function sortSynergy(){ 
    let itemsToSort = $(".gallery-item:not(:first-child)").get()
    itemsToSort.sort((a, b) => {
      return parseFloat(a.getAttribute("synergy")) < parseFloat(b.getAttribute("synergy")) ? 1: -1
    })
    $(".sort-button:first-child").addClass("active")
    $(".sort-button:last-child").removeClass("active")
    let $sortedDivs = $(itemsToSort);
    $("#gallery").append($sortedDivs)
  }

  function sortPopularity() {
    let itemsToSort = $(".gallery-item:not(:first-child)").get()
    itemsToSort.sort((a, b) => {
      return parseFloat(a.getAttribute("popularity")) < parseFloat(b.getAttribute("popularity")) ? 1: -1
    })
    $(".sort-button:last-child").addClass("active")
    $(".sort-button:first-child").removeClass("active")
    let $sortedDivs = $(itemsToSort);
    $("#gallery").append($sortedDivs)
  }
