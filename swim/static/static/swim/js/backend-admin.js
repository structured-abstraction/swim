// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.
//
// Taken from Django's Admin, for use in the front end of swim.

function html_unescape(text) {
    // Unescape a string that was escaped using django.utils.html.escape.
    text = text.replace(/&lt;/g, '<');
    text = text.replace(/&gt;/g, '>');
    text = text.replace(/&quot;/g, '"');
    text = text.replace(/&#39;/g, "'");
    text = text.replace(/&amp;/g, '&');
    return text;
}

// IE doesn't accept periods or dashes in the window name, but the element IDs
// we use to generate popup window names may contain them, therefore we map them
// to allowed characters in a reversible way so that we can locate the correct 
// element when the popup window is dismissed.
function id_to_windowname(text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    return text;
}

function windowname_to_id(text) {
    text = text.replace(/__dot__/g, '.');
    text = text.replace(/__dash__/g, '-');
    return text;
}

function showAddAnotherPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^add_/, '');
    name = id_to_windowname(name);
    href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href  += '&_popup=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function swim_dismissAddAnotherPopup(win, newId, newRepr) {
    // newId and newRepr are expected to have previously been escaped by
    // django.utils.html.escape.
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);

    var hidden_name = name;
    name = name + "-other";
    var hidden_elem = document.getElementById(hidden_name);
    if (hidden_elem) {
        if (hidden_elem.nodeName == "INPUT") {
          hidden_elem.value = newId;
        }
        showThumbnail(hidden_elem.parentNode);
    }
    var elem = document.getElementById(name);
    if (elem) {
        elem.disabled = false;
        elem.readonly = false;
        if (elem.nodeName == 'SELECT') {
            var o = new Option(newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        } else if (elem.nodeName == 'INPUT') {
            elem.value = newId;
        }
        elem.disabled = true;
        elem.readonly = true;
    }
    win.close();
}

/**
 * Not finished add another inline tool javascript
 * <ul class="inline-tools"><li><a class="addlink" href="add/">Add gallery</a></li></ul>
 */
dojo.addOnLoad(function() {
    /*dojo.query(".inline-related").addContent(
     "<span style=\"clear:both\"><ul class=\"inline-tools\"><li><a class=\"addlink\" href=\"javascript:void();\">Add another</a></li></ul></span>"
    );*/

});


/**
 * Switch out all image foreign-key elements for an actual version of the image.
 */

function showThumbnail(element) {
  var element = dojo.byId(element);
  if(!element) return;
  var image_input = dojo.query("select", element)[0];
  var value = dojo.attr(image_input, 'value');
  if (!value) {
    value = image_input.value;
  }
  if (value) {
    var url = '/admin/content/image/' + value + '/thumb';
    dojo.xhrGet({
      url: url,
      load: dojo.hitch(element, function(response) {
        /*dojo.query("select", this).orphan();*/
        var thumbnail = dojo.query(".thumbnail", this)[0];
        thumbnail.innerHTML = response;
      })
    });
  }
}

dojo.addOnLoad(function() {
  //dojo.query(".image").forEach(showThumbnail);
});
