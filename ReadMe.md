# Commands

## Start service in port 5000

python3 manage.py runserver 0.0.0.0:5000

## Reset user database

Using ```python manage.py flush```

# Issues to be addressed

## Make sure ```save_source.py``` is running

## Deal with Snopes "Learn More" message width issue

## After ```save_source.py``` is done, run a script that removes all rows with a path from ```bad_links.csv```

Some links that were retrieved after stopping then resuming the ```save_source.py``` script are still recorded in ```bad_links.csv```. A small script should be run to check if there is a path for each row in ```bad_links.csv``` and if there is, remove that row. The script should also drop duplicates(not that important as this can be done in views.py, but might save time needed to remove duplicates every single time a datarframe is created).

## Figure out the ```data-specless-position``` attribute issue

Sometimes the row in the annotator containing the iframes and the form has its width reduced to about 20% of the screen while the rest of the screen remains empty. This is solved from the browser (from "inspect element") by removing an attribute called ```data-specless-position``` from the ```div``` tag surrounding the rows. This attribute, however, isnt in ```home.html```. Need to figure out when is it added to stop it from distorting the annotator.
