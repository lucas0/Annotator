# Current Issues to be fixed/changed/added:

## save-source.py:

1) Change source_list after save_source is done to only include error-free links. Source_list is used in the annotator to show how many sources a page has.

## views.py:

1) Finish newOrigin function and ajax post functions.

2) Some source_lists give "ValueError: malformed node or string: None" when using ast.literal._eval(). Might be fixed by solving issue 3 in previous section.

3) Redirect when user is done annotating all.
