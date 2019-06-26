# Current Issues to be fixed/changed/added:

## save_source.py

1)Broken html problem is back. Avoid global style changes as not to mess up positioning of other elements.

2) Need to store the csrf_token sent by django so that the ajax jqEvnt function in the iframe can access it for POST requests.

## views.py:

1) Redirect when user is done annotating all.
