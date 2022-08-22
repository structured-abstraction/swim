dojo.require('dijit.ProgressBar');
dojo.require('dijit.Dialog');

// Generate 32 char random uuid 
function gen_uuid() {
    var uuid = ""
    for (var i=0; i < 32; i++) {
        uuid += Math.floor(Math.random() * 16).toString(16); 
    }
    return uuid
}

dojo.provide("swim.PostProgressWidget");
dojo.declare("swim.PostProgressWidget", null, {
  /**
   * Set up the event handlers that will show the progress dialog.
   */
  constructor: function(form_element) {
    dojo.query("body").addClass("tundra");
    this.form_element = form_element;

    this.poll_frequency = 500;

    this.form_action = dojo.attr(this.form_element, 'action');
    this.uuid = gen_uuid();
    this.form_action += (this.form_action.indexOf('?') == -1 ? '?' : '&') + 'X-Progress-ID=' + this.uuid;
    dojo.attr(this.form_element, 'action', this.form_action);
    
    // Instruct all "Submit" buttons to cause the progress widget to be shown
    dojo.query("input[type=submit]") 
      .connect('onclick', dojo.hitch(this, this.showProgressDialog));
    
    dojo.query("fieldset").addContent("<div class=\"form-row progress\"><div><label for=\"fileUploadProgress\">Progress:</label><div id=\"fileUploadProgress\"></div></div></div>");
    this.progressBar = new dijit.ProgressBar({}, "fileUploadProgress");
    dojo.query("#fileUploadProgress").style({
        width: '300px'
      });

  },

  /** Show the progress during the submission. */
  showProgressDialog: function(event) {
    this.progressBar.update({
      maximum: 0,
      progress: 100,
      indeterminate: true
    });
    // Schedule them to be removed in a few seconds.
    this.timeout = setTimeout(dojo.hitch(this, this.getProgress), this.poll_frequency);

  },

  getProgress: function() {
    // Start a callback that executes 5 times a second which makes a request for the progress
    // and updates the bar.
    var url = "/content/progress/" + this.uuid + "/progress.json";
    var result = dojo.xhrGet({
        url: url,
        preventCache: true,
        handle: dojo.hitch(this, this.progressHandler),
        handleAs: "json"
    });
  },

  /**
   *
   */
  progressHandler: function(responseObject, ioArgs) {
    // If we didn't get a 200 result, let's assume we're done.
    if (ioArgs.xhr.status != 200) {
      this.progressBar.update({
        maximum: this.maximum,
        progress: this.maximum,
        indeterminate: false
      });
      return false;
    }

    if (responseObject.length && responseObject.uploaded) {
      this.progressBar.update({
        maximum: responseObject.length,
        progress: responseObject.uploaded,
        indeterminate: false
      });
      this.maximum = responseObject.length;

      // We got a valid response and updated the progress, let's wait a bit before
      // polling again.
      this.timeout = setTimeout(dojo.hitch(this, this.getProgress), this.poll_frequency);
    } else {
      // We weren't able to get a status update, let's poll immediately
      this.timeout = setTimeout(dojo.hitch(this, this.getProgress), 1);
    }

    return responseObject;
  }

});


/**
 * After the html is loaded, let's find the form and hook into the submission
 * process in order to show a progress bar.
 */
dojo.addOnLoad(function() {
    // Find the form input element.
    elements  = dojo.query("form");
    if(elements.length == 0) {
      return;
    }
    var form_element = elements[0];
    dojo.global.progressWidget = new swim.PostProgressWidget(form_element);
});

