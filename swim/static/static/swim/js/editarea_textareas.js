// Wait for the document to load before converting textareas to editareas
dojo.addOnLoad(function() {
    var textareas = dojo.query('textarea'); dojo.forEach(textareas, convertTextAreaToEditArea); 
});


function convertTextAreaToEditArea(textArea) {
    var params = { 
        id                 : textArea.id,      // textarea id
        syntax             : "html",           // syntax to be uses for highgliting
        allow_toggle       : false,
        min_width          : 800,
        min_height         : 400,
        replace_tab_by_spaces: 2,
        allow_resize: "both",
        begin_toolbar: "save",
        save_callback: "editAreaSaveHandler"
    };
        
    // Safari doesn't seem to deal well with highlighting in EditArea
    if (!dojo.isSafari) {
        params.start_highlight = true;
    }
    
    editAreaLoader.init(params);
}


/**
 * Called in response to clicking on save button in editArea toolbar.
 * Performs the same save method as the django save button.
 */
function editAreaSaveHandler(textAreaId, content)
{
	saveAndContinueButtonHandler();
}