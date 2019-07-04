# Problems collected after 100+ annotations

~~## The scrolling and highligting functions (for link being displayed) wait for the entire window (both iframes and parent) to load before working.~~

Sometimes one of the pages (more likely the source page) keep sending requests which prevents the window from fully loading (I am talking about the "load" event, the content is usually fully loaded). This means that the user might have to wait a very long time as, untill the window "loads", the link will not be highlighted.

**Solution:** Highlight link in ```views.py``` and scroll using ```iframe onload```

~~## Link being sent to change_origin() gets changed.~~

Happened once. I pressed a link with its src having the characters ```%20```, but when it was printed by Django (in ```change_origin()```) those characters were changed to ```+```.

**Solution:** If link pressed isnt in source_list of corresponding snopes page, just treat it as an Invalid (ie broken) link. The link is being changed while being sent since ```console.log()``` in the ajax onclick event prints the correct link but ```change_origin()``` doesnt.

~~## In the source_html, some images are not found (due to src being improperly changed).~~

**Solution:** Start from domain and try to request the assest (img/link/etc) from the root of the source_url path (ie domain) untill your reach the entire source_url. Break loop at first 200 response status code and add that url to the src of the asset.

## If you submit too fast, csrf token might not have enough time to load into form. 

Pretty unlikely to happen normally as users would take atleast a couple of seconds to look over the right-hand side iframe. But I thought it was worth mentioning.
