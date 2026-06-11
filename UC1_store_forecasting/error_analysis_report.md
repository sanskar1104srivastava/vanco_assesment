Error Analysis Report

Scope

This report looks at the validation errors for the final model, exp_023.

Validation period:

July 31 2017 to August 15 2017

Overall Validation Score

Metric: Value
RMSLE: 0.39568465
MAE: 60.996766
Rows: 28,512

The model does not have a large overall bias. Most remaining error comes from specific segments.

Main Error Patterns

Area: Finding
Low sales rows: These rows are hardest for RMSLE because small misses matter more in log scale.
High sales rows: These rows create the largest MAE misses.
Promotions: Heavy promotion rows can create large unit errors.
Holidays: Holiday rows are harder than normal days.
Product family: SCHOOL AND OFFICE SUPPLIES was one of the weakest families in validation.
Stores: Some stores had higher error because demand moved differently from the general pattern.

Demand Level

Low volume rows drive the RMSLE risk. High volume rows are less risky for RMSLE but can have large unit misses.

This is why both RMSLE and MAE were tracked.

Promotions

Promotion count helps, but it does not explain everything. The data gives the number of promoted items, not the discount size or store placement.

This makes promotion heavy days harder to predict.

Holidays

Holiday flags helped, but holiday effects are sparse. Not every holiday repeats often enough for every store and product family.

Final View

The model is good enough for final submission, but the hardest areas are:

low volume products
school season products
holiday periods
high promotion days
stores with changing traffic patterns
