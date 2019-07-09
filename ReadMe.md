# Issues to be addressed

## ~~Reset User Database~~

Using ```python manage.py flush```


## ~~Skip ```save_annotation()``` if username has "test" in it~~

## Make sure ```save_source.py``` is running

## ~~Change radiobuttons to buttons~~

Also add function to take care of setting value of op and submitting form

## ~~Add print to see which rows are selected an if they are found~~

## ~~Use shuffled samples dataframe in ```get_least_annotated_page()```~~

Change shufling so that a new row is retrieved each time (to avoid infinite loops)

## ~~Remove automatic annotation~~

Instead just call the function again using ```aPage = none```

## Deal with Snopes "Learn More" message width issue

## After ```save_source.py``` is done, run a script that removes all rows with a path from ```bad_links.csv```

Some links that were retrieved after stopping then resuming the ```save_source.py``` script are still recorded in ```bad_links.csv```. A small script should be run to check if there is a path for each row in ```bad_links.csv``` and if there is, remove that row. The script should also drop duplicates(not that important as this can be done in views.py, but might save time needed to remove duplicates every single time a datarframe is created).

## Figure out the ```data-specless-position``` attribute issue

Sometimes the row in the annotator containing the iframes and the form has its width reduced to about 20% of the screen while the rest of the screen remains empty. This is solved from the browser (from "inspect element") by removing an attribute called ```data-specless-position``` from the ```div``` tag surrounding the rows. This attribute, however, isnt in ```home.html```. Need to figure out when is it added to stop it from distorting the annotator.
