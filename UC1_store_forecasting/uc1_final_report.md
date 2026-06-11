UC1 Final Report

Objective

The goal was to forecast daily sales for each store and product family in the Kaggle Store Sales dataset.

The forecast horizon is 16 days, from August 16 2017 to August 31 2017.

Final Model

The final model is exp_023.

It is a weighted ensemble:

```text
sales = 0.7 * LightGBM + 0.3 * XGBoost
```

Both models use the same feature set and are trained around a time based validation setup.

Main Features

The model uses:

store number
product family
store cluster
calendar features
promotion features
holiday flags
historical store family sales patterns
historical transaction proxy features

Only information available before the forecast period is used for historical features.

Validation

Validation was done on the final 16 days of the training data:

July 31 2017 to August 15 2017

Metric: Value
RMSLE: 0.39568465
MAE: 60.996766
Rows: 28,512

RMSLE was treated as the main metric because it is the Kaggle scoring metric.

Kaggle Result

Item: Value
Public score: 0.43992
Submission file: submission.csv

exp_023 was kept as the champion because it had the best known public leaderboard score.

Why Not The Later Model

A later model, exp_025, looked better on local validation but scored worse on the public leaderboard.

That was a sign that the later blend was less reliable on unseen data. For the final submission, the simpler exp_023 ensemble was used.

Final Files

store_sales_forecasting_final.ipynb
submission.csv
feature_importance.csv
forecasting_architecture.png
forecasting_pipeline.png
error_analysis_report.md
multi_fold_backtest_report.md
