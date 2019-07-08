# Issues to be addressed

## ~~Reset User Database~~

Using ```python manage.py flush```


## ~~Skip ```save_annotation()``` if username has "test" in it~~

## ~~Use shuffled samples dataframe in ```get_least_annotated_page()```~~

Also remember to change the other functions that are called from it

## Find a way to prevent ```get_least_annotetd_page()``` from being stuck in an infinite loop

1) ~~Try using ```random_state=time.time()``` in ```.frac()``` for both samples and not_done_count dataframes~~

2) Add bad-row removal to ```save_source.py``` for future runs (if any)

3) Write a script to remove "bad rows", stored in bad_rows.csv, from samples.csv then overwrite. This will reduce the chance of "Gateway Timeout" error happening as a result of successive "bad rows" getting retrieved by ```get_least_annotated_page()```

## ~~Remove automatic annotation~~

Instead just call the function again using ```aPage = none```

## Deal with Snopes "Learn More" message width issue

## ~~Replace radio buttons in form with checkboxes~~