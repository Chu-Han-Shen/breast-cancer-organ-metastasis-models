original_working_directory <- getwd()
on.exit(setwd(original_working_directory), add = TRUE)

setwd(file.path("distilled_models", "MetMap"))
source(file.path("scripts", "run_MetMap_prediction_and_plot.R"))
