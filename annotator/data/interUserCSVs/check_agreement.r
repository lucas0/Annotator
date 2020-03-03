install.packages("ellipsis")
install.packages(c('devtools','curl'))
devtools::install_github("jmgirard/agreement")
path = "/var/www/Annotator/annotator/data/interUserCSVs"
setwd(path)
library(agreement)
files = list.files(path, pattern=NULL, all.files=FALSE,full.names=FALSE)
for (mydata in files){
	library(naniar)
	na_strings <- c("NA", "N A", "N / A", "N/A", "N/ A", "Not Available", "NOt available", "<NA>")
	mydata %>% replace_with_na_all(condition = ~.x %in% na_strings)

	results1 <- cat_adjusted(mydata)
	summary(results1, ci = TRUE)

	results3 <- cat_specific(mydata)
	summary(results3, ci = TRUE)
}
