AI Solution Architect Assessment

Project Overview

This repository contains three assessment use cases prepared for review.

Use Case 1 is grocery sales forecasting.

Use Case 2 is ASL hand sign detection.

Use Case 3 is Hybrid RAG over an NCERT Physics PDF.

The repository root is D:\vanco_assesment. The existing working folders are kept in place so code, models, notebooks, and evidence are not duplicated.

Assessment Overview

The submission shows three solution types.

The forecasting use case demonstrates time aware validation, feature engineering, model comparison, Kaggle submission evidence, and error analysis.

The ASL use case demonstrates a computer vision detector with a trained YOLO model, dataset documentation, confusion matrices, metric curves, and webcam demo instructions.

The Hybrid RAG use case demonstrates grounded document question answering with semantic retrieval, keyword retrieval, graph retrieval, citations, and a reviewer friendly interface.

Repository Structure

Root README
README.md

Final report
reports/Final_Report.md

Root architecture diagrams
diagrams/UC1_architecture.png
diagrams/UC2_architecture.png
diagrams/UC3_architecture.png

Submission checklist
submission_assets/submission_checklist.md

Use Case 1 folder
UC1_store_forecasting

Use Case 2 folder
UC2_ASL_detection

Use Case 3 folder
UC3_hybrid_RAG

Use Case 1 Summary

Use Case 1 forecasts daily grocery sales for the Kaggle Store Sales problem. The final model is experiment exp_023. It blends LightGBM and XGBoost residual predictions.

Important review files are listed below.

Final submission
UC1_store_forecasting/submission.csv

Final notebook
UC1_store_forecasting/store_sales_forecasting_final.ipynb

Final report
UC1_store_forecasting/uc1_final_report.md

Validation strategy
UC1_store_forecasting/uc1_final_report.md

Error analysis
UC1_store_forecasting/error_analysis_report.md

Feature importance
UC1_store_forecasting/feature_importance.csv

Architecture diagram
diagrams/UC1_architecture.png

Kaggle leaderboard screenshot
UC1_store_forecasting/screenshots/kaggle_leaderboard.png

Use Case 2 Summary

Use Case 2 detects ASL letters A through J from webcam frames. The trained model is saved as UC2_ASL_detection/best.pt. The demo script opens a webcam and shows detected signs with bounding boxes and confidence scores.

Important review files are listed below.

Dataset configuration
UC2_ASL_detection/dataset/data.yaml

Trained model
UC2_ASL_detection/best.pt

Webcam demo script
UC2_ASL_detection/run_webcam_inference.py

Training notebook folder
UC2_ASL_detection/training

Dataset summary
UC2_ASL_detection/reports/dataset_summary.md

Annotation samples
UC2_ASL_detection/reports/annotation_samples.md

Model evaluation
UC2_ASL_detection/reports/model_evaluation.md

Live demo guide
UC2_ASL_detection/reports/live_demo_guide.md

Confusion matrix
UC2_ASL_detection/reports/confusion_matrix.png

Training results
UC2_ASL_detection/reports/training_results.csv

Architecture diagram
diagrams/UC2_architecture.png

Use Case 3 Summary

Use Case 3 is a Hybrid RAG application for answering questions from UC3_hybrid_RAG/data/physics.pdf. It combines vector retrieval, BM25 keyword search, and Neo4j graph retrieval before generating grounded answers with citations.

Important review files are listed below.

Backend
UC3_hybrid_RAG/backend

Frontend
UC3_hybrid_RAG/frontend

Ingestion code
UC3_hybrid_RAG/backend/ingest.py

Evaluation examples
UC3_hybrid_RAG/evaluation_results.md

System design
UC3_hybrid_RAG/reports/system_design.md

Live demo guide
UC3_hybrid_RAG/reports/live_demo_guide.md

Limitations and next steps
UC3_hybrid_RAG/reports/limitations_and_next_steps.md

Architecture diagram
diagrams/UC3_architecture.png

Setup Instructions

Use a separate Python virtual environment for each use case. Open the folder for the use case, create a virtual environment, activate it, and install the packages from its requirements file.

Dependencies

Use Case 1 uses pandas, numpy, scikit learn, LightGBM, XGBoost, and joblib.

Use Case 2 uses Ultralytics, OpenCV, and numpy.

Use Case 3 uses FastAPI, Streamlit, ChromaDB, Neo4j, sentence transformers, BM25 search, and Ollama.

How Reviewers Can Run Each Use Case

Detailed local run commands are kept inside each use case folder.

For Use Case 1, open UC1_store_forecasting/store_sales_forecasting_final.ipynb and inspect UC1_store_forecasting/submission.csv.

For local Use Case 1 execution, download the Kaggle Store Sales CSV files into the UC1_store_forecasting data folder before running the notebook.

For Use Case 2, open UC2_ASL_detection/reports/live_demo_guide.md and run UC2_ASL_detection/run_webcam_inference.py after installing the requirements.

For Use Case 3, open UC3_hybrid_RAG/setup_instructions.md and UC3_hybrid_RAG/reports/live_demo_guide.md. Start Neo4j and Ollama, run ingestion, start the FastAPI backend, and then launch the Streamlit frontend.

Contact Information

Prepared by Sanskar for the AI Solution Architect assessment.
