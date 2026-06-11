Multi Fold Backtest Report

Purpose

The multi fold check was used to see whether the model was stable across more than one validation period.

This matters because a model can look good on one validation window and still perform worse on Kaggle.

Fold Results

Model  Mean RMSLE  RMSLE Std  Mean MAE  Notes
exp_023  0.390554  0.010860  56.848119  Final champion
exp_024  0.391361  0.011523  55.341961  Tuned LightGBM candidate
exp_025  0.389947  0.011431  55.772713  Robust blend, rejected after public score

Interpretation

exp_025 had the best local mean RMSLE, but it did not beat exp_023 on the Kaggle public leaderboard.

The final decision used both local validation and public leaderboard evidence.

Final Choice

exp_023 was selected because:

it had the best known Kaggle public score
it kept both LightGBM and XGBoost in the ensemble
it was simpler than the tuned heavy blend
it was less dependent on the final validation window

Final public score:

0.43992
