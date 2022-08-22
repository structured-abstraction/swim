dojo.require("dijit.form.FilteringSelect");
dojo.require("dojox.data.QueryReadStore");

autocompletes = {};
function swim_autocomplete(url, name) {
  var autocomplete_store = new dojox.data.QueryReadStore({url:url});
  autocompletes[url] = {};
  autocompletes[url]['store'] = autocomplete_store;
  autocompletes[url]['name'] = name;
  autocompletes[url]['url'] = url;

  var lookup_id = "lookup_" + name;

  dojo.query("body").addClass("tundra");
  var current_val = dojo.query("#" + lookup_id).attr("value")[0];

  var filteringSelect = new dijit.form.FilteringSelect(
    {
      id: lookup_id,
      store: autocomplete_store,
      searchAttr: "name",
      pageSize: 10,
      queryExpr: '*${0}*',
      highlightMatch: "all",
      promptMessage: "Start typing - we'll autocomplete the list based on your input.",
      autoComplete: false

    },
    lookup_id
  );
  filteringSelect.attr('displayedValue', current_val);
  autocompletes[url]['select'] = filteringSelect;

  function update_input_element() {
    var store = this.store;
    var select = this.select;
    if (select.item) {
      var id = select.store.getValue(select.item, "id");
      dojo.byId("id_" + name).value = id;
    }
  }
  var listener = dojo.hitch(autocompletes[url], update_input_element); 
  dojo.connect(filteringSelect.domNode, "onkeyup", listener);
  dojo.connect(filteringSelect, "onBlur", listener);
  dojo.connect(filteringSelect, "onChange", listener);

}
