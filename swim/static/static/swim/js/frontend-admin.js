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

/*
 * newId and newRepr are typically used within the main admin for updating the select box
 * with information about the newly added entity.  We don't use it in this case, but
 * we define it to remain comaptible with the django admin.
 */
function dismissAddAnotherPopup(popupWindow, newId, newRepr) {
    popupWindow.close();
    window.location.reload();
}


/**
 * Listen for the special keypress for the admin site and show the admin bar when they
 * get it right
 */
var swimAdminCode = 'swimadmin';
var currentIndex = 0;
function swim_listenForAdmin(event) {
  var charCode = event.charCode;
  if (charCode == swimAdminCode.charCodeAt(currentIndex)) {
    ++currentIndex;
    if (currentIndex == swimAdminCode.length) {
      swim_createAdminBar(true, true);
    }
  } else {
    currentIndex = 0;
  }
}

dojo.addOnLoad(function() {
    dojo.connect(document, "onkeypress", swim_listenForAdmin);
});

/**
 * Create the swim admin bar.
 */
function swim_createAdminBar(animate, login) {
  var adminBar = dojo.query("#swimAdminBar");
  if (adminBar.length > 0) {
    // We already have one, don't create another.
    return;
  }

  var admin_bar = document.createElement("div");
  dojo.attr(admin_bar, "id", "swimAdminBar");
  var height = 50;
  if (animate) {
    height = 0;
  }
  dojo.style(admin_bar, {
      position: 'absolute',
      top: '0',
      left: '0',
      width: '100%',
      height: height + 'px',
      backgroundColor: "#226688",
      opacity: '0.75',
      borderBottom: '2px solid #999'
    });


  var admin_h2_a = document.createElement('a');
  dojo.attr(admin_h2_a, 'href', '/admin/');
  admin_h2_a.innerHTML = 'SWIM Admin';

  var admin_h2 = document.createElement('h2');
  dojo.attr(admin_h2, 'id', 'swimAdminBarTitle');
  dojo.place(admin_h2, admin_bar, "first");
  dojo.place(admin_h2_a, admin_h2, "first");
  dojo.place(admin_bar, document.body, "first");

  var admin_links = document.createElement('div');
  dojo.attr(admin_links, 'id', 'swimEditLinks');
  dojo.place(admin_links, admin_bar, "first");

  if (login) {
    //--------------------------------------------------------------------------
    // Build the login link
    var login_a = document.createElement('a');
    dojo.attr(login_a, 'id', 'swimAdminBarLogin');
    dojo.place(login_a, admin_links, "first");
    login_a.innerHTML = 'Show Edit Links';

    dojo.attr(login_a, 'href', '/admin/?_admin_redirect=' + window.location.pathname + window.location.search);

  } else {
    //--------------------------------------------------------------------------
    // Build the Show/Hide edit links
    var admin_edit_link = document.createElement('a');
    dojo.attr(admin_edit_link, 'id', 'swimAdminBarAdminLinks');
    dojo.place(admin_edit_link, admin_links, "first");

    // Remove the _admin_edit_links parameter if there is one. 
    var new_search = window.location.search.replace("_admin_edit_links=1", "");
    
    // If there wasn't one, then put it back in.
    if (new_search == window.location.search) {

      // If there already are values, use '&'
      if (new_search) {
        new_search = new_search + '&_admin_edit_links=1';
      // Otherwise don't.
      } else {
        new_search = '?_admin_edit_links=1';
      }
      admin_edit_link.innerHTML = 'Show Edit Links';
    } else {
      admin_edit_link.innerHTML = 'Hide Edit Links';
    }
    if (new_search == "?") new_search == "";
    dojo.attr(admin_edit_link, 'href', window.location.pathname + new_search);

    //--------------------------------------------------------------------------
    // Build the hide link
    var logout_a = document.createElement('a');
    dojo.attr(logout_a, 'id', 'swimAdminBarLogin');
    dojo.place(logout_a, admin_links, "first");
    logout_a.innerHTML = 'Hide Bar';

    dojo.attr(logout_a, 'href', '#');

    dojo.connect(logout_a, 'onclick', function (event) {
      var anim = dojo.anim("swimAdminBar", {height: { end: 0, unit:'px'}});
      dojo.connect(anim, 'onEnd', function() {
        dojo.query("#swimAdminBar").orphan();
      });
      dojo.stopEvent(event);
      return false;
    });

    //--------------------------------------------------------------------------
    // Build the logout link
    var logout_a = document.createElement('a');
    dojo.attr(logout_a, 'id', 'swimAdminBarLogin');
    dojo.place(logout_a, admin_links, "first");
    logout_a.innerHTML = 'Logout';

    dojo.attr(logout_a, 'href', '/admin/logout/');

    dojo.connect(logout_a, 'onclick', function (event) {
      dojo.xhrGet({
        url: '/admin/logout/',
        handle: function() {
          window.location.reload();
        }
      });
      dojo.stopEvent(event);
      return false;
    });
  }

  dojo.place(admin_links, admin_bar, "first");
  dojo.place(admin_bar, document.body, "first");
  if (animate) {
    dojo.anim("swimAdminBar", {height: { end: 50, unit:'px'}});
  }
}
