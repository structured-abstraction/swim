tinyMCE.init({
  mode : "none",
  theme : "advanced",
  theme_advanced_blockformats : "h1,h2,h3,p,address,div",
  //theme_advanced_blockformats : "p,div,h1,h2,h3,h4,h5,h6,blockquote,dt,dd,code,samp"
  //content_css : "/css/reset.css,/css/generic.css,/css/master.css",
  content_css : "/css/tinymce.css",
  theme_advanced_toolbar_location : "external",
  theme_advanced_toolbar_align : "left",

  theme_advanced_buttons1 : "formatselect,separator,bold,italic,separator,bullist,numlist,separator,outdent,indent,separator,image,link,unlink,separator,undo,redo,separator,pastetext,pasteword,separator,code,styleselect",
  theme_advanced_buttons2 : "",
  theme_advanced_buttons3 : "", 
  theme_advanced_statusbar_location: "bottom",
  theme_advanced_resizing : true,
  theme_advanced_path : false,
  remove_linebreaks : false,
  auto_resize : true,
  convert_urls : false,

  // layout
  width: 900,
  height: 20,

  auto_cleanup_word : true,
  plugins : "safari,table,save,advhr,advimage,advlink,emotions,iespell,insertdatetime,preview,zoom,flash,searchreplace,print,contextmenu,fullscreen,paste",
  paste_create_paragraphs : false,
  paste_create_linebreaks : false,
  paste_use_dialog : true,
  paste_auto_cleanup_on_paste : true,
  paste_convert_middot_lists : false,
  paste_unindented_list_class : "unindentedList",
  paste_convert_headers_to_strong : true,
  remove_trailing_nbsp : true,

  plugin_insertdate_dateFormat : "%m/%d/%Y",
  plugin_insertdate_timeFormat : "%H:%M:%S",
  valid_elements : "a[name|href|target|title],b,h1[class],h2[class],h3[class],h4[class],h5[class],i,p,br,ul,ol,li,strong,em,table[width:100%|border:1|cellspacing:0|cellpadding:5],tr,tbody,td[align:left|valign:top],object[width|height],param[name|value],embed[src|allowfullscreen|allowscriptaccess|width|height|type],img[src|style],div[class],iframe[style|id|name|src|width|height|marginwidth|align|frameborder|allowtransparency]"
  //invalid_elements: "script,object,applet,iframe,font,img,hr,style",
});

dojo.addOnLoad(function() {

    /* Convert all text areas explicitly marked as needing conversion. */
    var tinymceAreas = dojo.query('textarea');
    dojo.forEach(tinymceAreas, convertToTinyMCEArea);    

});

function convertToTinyMCEArea(textArea) {
  tinyMCE.execCommand('mceAddControl', false, textArea.id);
}
