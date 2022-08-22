
function convertTextAreaToEditArea(textArea) {
    var params = { 
        id                 : textArea.id,      // textarea id
        syntax             : "html",           // syntax to be uses for highgliting
        allow_toggle       : false,
        min_width          : 800,
        min_height         : 400,
        replace_tab_by_spaces: 2,
        allow_resize: "both"
    };
        
    // Safari doesn't seem to deal well with highlighting in EditArea
    if (!dojo.isSafari) {
        params.start_highlight = true;
    }
    
    editAreaLoader.init(params);
}


// Wait for the document to load before converting textareas to editareas
dojo.addOnLoad(function() {

  // Convert the textareas that are explicitly marked as editareas to edit areas.
  var textareas = dojo.query('.swimEditArea');
  dojo.forEach(textareas, convertTextAreaToEditArea);    

});

