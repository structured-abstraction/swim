dojo.require('dojo.fx');
dojo.require("dojo.NodeList-fx");

dojo.addOnLoad(function() {
    // Create a node to temporarily store ajax responses (for dojo.query)
    var ajaxResponseContainer = dojo.doc.createElement("div");
    ajaxResponseContainer.id = "ajaxResponseContainer";
    dojo.place(ajaxResponseContainer, 'container', 'last');
    
    // Instruct all "Save and Continue" buttons to be transformed.
    var saveAndContinueButtons = dojo.query("[name=_continue]");
    dojo.forEach(saveAndContinueButtons, transformSaveAndContinueButton);    
});


/** 
 * Converts button from standard submit button to an input button 
 * which fires an AJAX request to post the form data.
 */
function transformSaveAndContinueButton(button) {
  if (window.location.pathname.match('/add/$')) {
    return; // This is on the ad stage, nix the ajax save.
  } else {
    button.type = "button";
    dojo.connect(button, 'onclick', saveAndContinueButtonHandler);    
  }
}



/** Cause the form to submit using AJAX */
function saveAndContinueButtonHandler(event) {
    var formList = dojo.query("form");
    var form = formList[0];

    // Update the text in the form body to the latest content in the EditArea 
    form.body.value = editAreaLoader.getValue('id_body');
        
    dojo.xhrPost({
        url: ".", 
        form: form,
        load: saveAndContinueResponse, 
        error: saveAndContinueError
    });
    // Remove existing message list, if any exists
    var fades = [
        dojo.query('.messagelist').fadeOut(),
        dojo.query('.errornote').fadeOut(),
        dojo.query('.errorlist').fadeOut()
        ];
    var oldAnim = dojo.fx.combine(fades);

    var messageListRemove = dojo.query('.messagelist');
    var errorNoteRemove = dojo.query('.errornote').orphan();
    var errorList = dojo.query('.errorlist').orphan();
    dojo.connect(fades[0], "onEnd", function() {
        messageListRemove.orphan();
        errorNoteRemove.orphan();
        errorList.orphan();
    });
    oldAnim.play()
    dojo.query("input[type=\"submit\"]").forEach(function(element) {
          element.disabled = false;
        });
    dojo.query("input[type=\"button\"]").forEach(function(element) {
          element.disabled = false;
        });
}


/** Called upon successful return from the ajax submission */
function saveAndContinueResponse(response) {
    
    // Object on which to store the error messages found in the AJAX response
    var errorMessageDict = {};
    
    var ajaxResponseContainer = dojo.byId("ajaxResponseContainer");
    ajaxResponseContainer.innerHTML = response;
    
    // Extract the error messages, and identify them by their label's "for" attribute
    var errorList = dojo.query(".form-row.errors", ajaxResponseContainer);
    dojo.forEach(errorList, function(errorItem) {
        var errorlist = dojo.query(".errorlist", errorItem);
        var label = dojo.query("label[for]", errorItem)[0];
        var label_for = dojo.attr(label, "for");
        errorMessageDict[label_for] = errorlist;
    });
 
    var messageLists = dojo.query(".messagelist", ajaxResponseContainer);
    var errorNoteLists = dojo.query(".errornote", ajaxResponseContainer);

    ajaxResponseContainer.innerHTML = "";
    
    // Now that we have extracted the interesting nodes from the AJAX response
    // AND removed the AJAX response nodes from the document, we try to place
    // the nodes into our visible documents.


    // Success messages
    dojo.forEach(messageLists, function(messageList) {
        dojo.style(messageList, 'opacity', 0);
        dojo.place(messageList, "content", "before"); 
        dojo.fadeIn({node: messageList}).play();
    });
    
    // Place the Error Notes
    dojo.forEach(errorNoteLists, function(errorNote) {    
        dojo.style(errorNote, 'opacity', 0);
        var submit_row = dojo.query(".submit-row")[0];
        dojo.place(errorNote, submit_row, "after");
        dojo.fadeIn({node: errorNote}).play();
    });
    
    // Place the individual error messages
    for (var key in errorMessageDict) {
        var label = dojo.query("label[for='" + key + "']")[0];
        dojo.forEach(errorMessageDict[key], function(errorMessage) {
            dojo.style(errorMessage, 'opacity', 0);
            dojo.place(errorMessage, label, "before");
            dojo.fadeIn({node: errorMessage}).play();
        });
    }
}


/** Called upon failure to perform the ajax submission */
function saveAndContinueError(error) {

}
