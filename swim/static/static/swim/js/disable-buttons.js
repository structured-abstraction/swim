
dojo.addOnLoad(function() {
    var submitButtons = dojo.query("input[type=\"submit\"]");
    dojo.forEach(submitButtons, disableOnClick);
});

function disableOnClick(button) {
  dojo.connect(button, "onclick", function(element) {
      var target = dojo.byId(element.target);
      //target.disabled = true;
    });
}
