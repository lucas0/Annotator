# Current Issues to be fixed/changed/added:

## save_source.py

1) Changing the overflow to scroll on the style tag and on the style attribute of <body> doesnt solve the problem. Every page doesnt scroll now.

2) Need to store the csrf_token sent by django so that the ajax jqEvnt function in the iframe can access it for POST requests.

## views.py:

1) TEST on some examples before commiting and make sure the commited version can be run without the need of any modifications, that is the point of having a repository.
