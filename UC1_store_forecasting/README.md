UC1 Grocery Sales Forecasting

This folder contains the final files for the Vanco UC1 submission.

The task was to forecast daily sales for the Kaggle Store Sales dataset. The final submission uses the exp_023 model, a weighted LightGBM and XGBoost ensemble.

Final Result

Item: Value
Champion experiment: exp_023
Kaggle public score: 0.43992
Submission file: submission.csv
Validation RMSLE: 0.39568465
Validation MAE: 60.996766
Ensemble weights: 70% LightGBM, 30% XGBoost

Files

File: Purpose
store_sales_forecasting_final.ipynb: Main notebook with data loading, feature engineering, model training, validation, and submission creation.
submission.csv: Final Kaggle submission file.
feature_importance.csv: Feature importance from the final model.
uc1_final_report.md: Short final project report.
error_analysis_report.md: Main validation error findings.
multi_fold_backtest_report.md: Rolling validation fold comparison.
requirements.txt: Python dependencies.

How To Run

On Kaggle, upload store_sales_forecasting_final.ipynb and attach this Store Sales dataset:

```text
store-sales-time-series-forecasting
```

The notebook reads from:

```text
/kaggle/input/store-sales-time-series-forecasting
```

and writes:

```text
/kaggle/working/submission.csv
```

For local use on Windows, first download the Kaggle Store Sales dataset and place these files in UC1_store_forecasting/data/:

```text
train.csv
test.csv
stores.csv
oil.csv
holidays_events.csv
transactions.csv
```

Then open PowerShell from this folder and install the requirements:

```powershell
cd D:\vanco_assesment\UC1_store_forecasting
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install notebook
```

Start Jupyter and run the notebook from top to bottom:

```powershell
jupyter notebook store_sales_forecasting_final.ipynb
```

The notebook automatically uses the Kaggle input path above when it runs on Kaggle. When that path is not available, it uses the local data folder. The local run writes submission.csv in this folder.

Notes

The modeling phase is closed. The notebook is included to show the full workflow and to make the approach reproducible.

The leaderboard screenshot is included here:

screenshots/kaggle_leaderboard.png

The root repository diagram for this use case is:

../diagrams/UC1_architecture.png
