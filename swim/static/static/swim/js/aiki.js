dojo.require("dojo.fx");
dojo.require("dijit.dijit");
dojo.require("dojo.NodeList-fx");

dojo.provide("aiki.Smoke");
dojo.declare("aiki.Smoke", null, {
  constructor: function(image) {
    this.options = {
      image: 'aiki.png',
      title: 'Aiki - a dojo implementation of growl',
      text: 'http://www.structuredabstraction.com',
      duration: 3,
      gravity: "right",
      edge: 10
    }
    this.image = new Image();
    this.image.src = '/static/swim/images/smoke.png';

    this.queue = [];
    var styles = {
      div:
        {
          'width':'298px',
          'height':'73px',
          'padding-bottom': '10px',
        },
      img:
        {
          'float':'left',
          'margin':'12px'
        },
      h3:
        {
          'margin':'0',
          'padding':'10px 0px',
          'font-size':'13px',
          'color': 'white'
        },
      
      p:
        {
          'margin':'0px 10px 10px 60px',
          'font-size':'10px'  
        }
    };
    
    this.block = document.createElement('div');
    dojo.style(this.block, {
        'position': 'absolute',
        'color':'#fff',
        'font': '12px/14px "Lucida Grande", Arial, Helvetica, Verdana, sans-serif',
        'backgroundColor': '#226688',
        'borderBottom': '2px solid #999',
        'borderRight': '2px solid #999',
        'paddingBottom': '10px',
      });
    dojo.style(this.block, styles.div);
    dojo.style(this.block, 'opacity', '0.75');
    dojo.place(this.block, document.body, "last");

    var img = document.createElement('img');
    dojo.style(img, styles.img);
    dojo.place(img, this.block, "last");

    var h3 = document.createElement('h3');
    dojo.style(h3, styles.h3);
    dojo.place(h3, this.block, "last");

    var p = document.createElement('p');
    dojo.style(p, styles.p);
    dojo.place(p, this.block, "last");
  },
  
  show: function(options) {
    // Calculate the position we'll show in.
    var options = dojo.mixin(this.options, options)
    var last = 0;
    if (this.queue.length > 0) {
      last = this.queue[this.queue.length-1];
    }
    var viewport = dijit.getViewport();
    this.queue.push(last+1);

    if (options.gravity == "topleft") {
      delta = viewport.t+options.edge+(last*83);
      options.position = {'top':delta+'px', "left":'10px', 'display':'block'};

    } else if (options.gravity == "bottomleft") {
      delta = (viewport.h)-(options.edge + 83)-(last*83)
      options.position = {'top':delta+'px', "left":'10px', 'display':'block'};

    } else if (options.gravity == "bottomright") {
      delta = (viewport.h)-(options.edge + 83)-(last*83)
      options.position = {'top':delta+'px', "right":'10px', 'display':'block'};

    } else { /* topright */
      delta = viewport.t+options.edge+(last*83);
      options.position = {'top':delta+'px', "right":'10px', 'display':'block'};
    }

    var elements = [dojo.clone(this.image), dojo.clone(this.block)];
    dojo.forEach(elements, function(element, index) {
      dojo.place(element, document.body, "last");
      dojo.style(element, this.options.position);
    }, this);
   
    dojo.query("img", elements[1]).attr('src', this.options.image); 
    dojo.query("h3", elements[1]).addContent(this.options.title);
    dojo.query("p", elements[1]).addContent(this.options.text);


    // Create the animation for fading all of the elements in.
    var show_list = [];
    dojo.forEach(elements, function(element, index) {
      var show_and_hide = dojo.fx.wipeIn({ 
                node: element,
                duration: 400
              });
        show_list.push(show_and_hide);
    }, this);
    // Combine them (run them in parallel) and start the fade.
    var full_show = dojo.fx.combine(show_list).play();

    // Create the animation for fading out all of the elements.
    var hide_list = [];
    dojo.forEach(elements, function(element, index) {
        var show_and_hide = dojo.fx.wipeOut({
              node: element,
              duration: 400
            });
          hide_list.push(show_and_hide);
        },
        this
    );
    // Combine them (run them in parallel), but don't start it yet.
    var hide_animation = dojo.fx.combine(hide_list);

    // Create an object to store some instance specific data.
    var hide_timeout = null;
    var smoke_instance = {
      parent: this,
      elements: elements,
      hide_animation: hide_animation,
      hide_timeout: hide_timeout,
      options: options
    };

    // When they have finally finished fading out, remove them from the dom.
    dojo.connect(hide_animation,"onEnd", dojo.hitch(smoke_instance, function() {
        this.parent.queue.shift(); // TODO: this isn't correct.
        dojo.forEach(this.elements, function (element) {
          dojo._destroyElement(element);
        })
      })
    );

    // Schedule them to be removed in a few seconds.
    smoke_instance.hide_timeout = setTimeout(dojo.hitch(smoke_instance, function() {
          this.hide_animation.play();
      }),
      this.options.duration*1000
    );

    // If someone mouses over - don't hide them, in other words clear
    // the timeout schedule.
    dojo.connect(elements[1], "onmouseover",
      dojo.hitch(smoke_instance, function() {
        clearTimeout(this.hide_timeout);
        this.hide_timeout = null;
      })
    );

    // Once the mouse has left, reschedule them for fading out.
    // the timeout schedule.
    dojo.connect(elements[1], "onmouseout",
      dojo.hitch(smoke_instance, function() {
        if (!this.hide_timeout) {
          this.hide_timeout = setTimeout(dojo.hitch(smoke_instance, function() {
                this.hide_animation.play();
            }),
            options.duration*1000
          );
        }
      })
    );
  }
});

