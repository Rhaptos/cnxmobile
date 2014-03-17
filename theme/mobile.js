// this condition about '?basic' is only for the purpose of the mock-ups, but the code inside it is necessary for implementation 
// (even if it's done differently than written)
if (window.location.href.indexOf('?basic') < 0) {

/*
  var fileref = document.createElement("link");
  fileref.setAttribute("rel", "stylesheet");
  fileref.setAttribute("type", "text/css");
  fileref.setAttribute("href", '/_theme/mobile-smart.css');
  document.getElementsByTagName("head")[0].appendChild(fileref);
*/

  document.write("<link rel='stylesheet' type='text/css' href='/_theme/mobile-smart.css' />");
  document.write("<script type='text/javascript' src='/transmenus/transMenus0_9_2.js'> </script>");
  document.write("<script type='text/javascript' src='/transmenus/toc.js'> </script>");

}
