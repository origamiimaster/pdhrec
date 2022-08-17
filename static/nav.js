$(document).ready(()=> {
  $(".mobile-nav").hide();
  let mobile_menu_toggle = false;
  $(".nav-menu-button").click(()=>{
    if (mobile_menu_toggle == false) {
      $(".mobile-nav").show();
    } else {
      $(".mobile-nav").hide();
    }
    mobile_menu_toggle = !mobile_menu_toggle;
  })
})
