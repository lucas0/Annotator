# Problems collected after 100+ annotations

## The scrolling and highligting functions (for link being displayed) wait for the entire window (both iframes and parent) to load before working. 

Sometimes one of the pages (more likely the source page) keep sending requests which prevents the window from fully loading (I am talking about the "load" event, the content is usually fully loaded). This means that the user might have to wait a very long time as, untill the window "loads", the link will not be highlighted.

**Proposed solution:** move both scroll and highlight functions to home.html and base.html instead of injecting them into the html in save_source.py. Will use ```<iframe onload="some_function(this)">``` to trigger the function (that will scroll and highlight). Passing ```this``` into the function allows us to reference the iframe's elements. I got it to work but I still need to test if that solves the issue or if it does the same exact thing as injecting the functions into the snopes html.

**Proposed improvement:** call the new function (that will scroll and highlight) from the body tag inside the iframe to avoid having to wait for any requests by the snopes page. Something like ```<body onload="some_function(this.parent)">```.

## Link being sent to change_origin() gets changed.

Happened once. I pressed a link with its src having the characters ```%20```, but when it was printed by Django (in ```change_origin()```) those characters were changed to ```+```.

**Proposed solution:** send a string instead of a JSON Object inside the ajax request. The reason this might work is because, when a JSON Object is sent to Django, it must be decoded first (as it is receieved as a byte-like Object) then data can be retrieved from it. So this change in characters might be due to the usage of ```.decode()``` in ```change_origin()```.

## In the source_html, some images are not found (due to src being improperly changed). 

In ```save_source.py```, why are we only adding the domain instead of the entire source_url to the src of the images/links/etc ?

## If you submit too fast, csrf token might not have enough time to load into form. 

Pretty unlikely to happen normally as users would take atleast a couple of seconds to look over the right-hand side iframe. But I thought it was worth mentioning.
