# Current Issues to be fixed/changed/added:

## save-source.py:

1) Deal with greyed-out images (img class == lazy-loading). Test to see if they always appear small, if so this can be ignored.

2) Broken html (same site can one time load fully, and other times load with no scrolling allowed).

3) Change source_list after save_source is done to only include error-free links. Source_list is used in the annotator to show how many sources a page has.

4) Encoding to utf-8 function (since beautifulsoup can best-guess the encoding, might just turn html to soup before being rendered, in views.py).

## views.py:

1) Finish newOrigin function and ajax post functions.

2) Some source_lists give "ValueError: malformed node or string: None" when using ast.literal._eval(). Can be fixed by solving issue 3 in previous section.