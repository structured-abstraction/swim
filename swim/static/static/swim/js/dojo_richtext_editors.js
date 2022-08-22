// Load jQuery
google.load("dojo", "1.4.1");
function unescapeHTML(text) {
  var text = text.replace(/&#8217;/m , "'").replace(/&#8243;/m , "\"").replace(/&#60;/m,">").replace(/&#62;/m,"<").replace(/&#38;/m,"&");
  var text = text.replace(/&quot;/mg, "\"").replace(/&gt;/mg,">").replace(/&lt;/mg,"<").replace(/&amp;/mg,"&");
  return text;
}

// on page load complete, fire off a jQuery json-p query
// against Google web search
google.setOnLoadCallback(function() {
    dojo.require("dojo.parser");
    dojo.require("dijit.Editor");
    dojo.require("dijit._editor.plugins.AlwaysShowToolbar");
    dojo.require("dijit._editor.plugins.LinkDialog");
    dojo.addOnLoad(function () {
      var focusOnLoad = true;
      dojo.query('body').addClass('tundra');
      dojo.query('textarea').forEach(function (textarea) {
          var hidden = dojo.doc.createElement("input");
          dojo.attr(hidden, 'type', 'hidden');
          dojo.attr(hidden, 'name', dojo.attr(textarea, 'name'));
          dojo.place(hidden, textarea.parentNode, "last");
          var div = dojo.doc.createElement("div");
          div.innerHTML = unescapeHTML(textarea.innerHTML);
          dojo.place(div, textarea.parentNode, "last");

          var editor = new dijit.Editor({
                height: '',
                width: 900,
                minHeight: 50,
                focusOnLoad: focusOnLoad,
                plugins: ["undo", "redo", "cut", "copy", "paste",
                            "selectAll", "bold", "italic", "underline",
                            "strikethrough", "subscript", "superscript", "removeFormat",
                            "insertOrderedList", "insertUnorderedList", "insertHorizontalRule",
                            "indent", "outdent", "justifyLeft", "justifyRight", "justifyCenter",
                            "justifyFull", "createLink", "unlink"],
                extraPlugins: ['dijit._editor.plugins.AlwaysShowToolbar'],
            }, div);
          //console.log('FOO');
          //console.log(textarea.parentNode);
          //dojo.place(editor, textarea.parentNode, "last");
          //console.log(textarea);
          //console.log(textarea.form);
          /*dojo.connect(*/
          focusOnLoad = false;
        });

      dojo.query('textarea').orphan();
    });
  });

