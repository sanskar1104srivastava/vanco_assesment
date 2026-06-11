AI Solution Architect Assessment Final Report

Executive Summary

This repository presents three use cases for an AI Solution Architect assessment.

Use Case 1 is grocery sales forecasting. It focuses on time aware validation, feature engineering, model comparison, Kaggle submission evidence, and clear error analysis.

Use Case 2 is ASL hand sign detection. It includes a YOLO dataset, a trained model, metric curves, confusion matrices, and a webcam demo path.

Use Case 3 is Hybrid RAG over an NCERT Physics PDF. It combines semantic retrieval, keyword retrieval, and graph retrieval to produce grounded answers with citations.

The repository is organized for review. The working project folders are preserved, and the root diagrams folder now contains the three architecture diagrams requested in the assessment prompt.

Use Case 1 Grocery Forecasting

Problem

The forecasting task predicts daily sales for every store, product family, and date in the Kaggle Store Sales problem. The forecast horizon has 16 days. The main metric is RMSLE, which is sensitive to relative error on low volume rows.

Architecture

The final solution is a residual forecasting pipeline. A deterministic baseline first estimates sales from historical demand, day patterns, promotions, holidays, store cluster behavior, and transaction proxies. LightGBM and XGBoost then learn residual corrections in log space. The final submission blends the two model families.

The retained champion is experiment exp_023. It gives more weight to LightGBM and keeps XGBoost for model diversity.

The root architecture diagram is diagrams/UC1_architecture.png.

Feature Engineering

The feature set includes store and family identifiers, calendar features, promotion features, scoped holiday signals, historical sales means, deterministic forecast values, and historical transaction proxies.

The approach is conservative. Features were kept only when they improved validation or helped generalization. Oil features and richer holiday distance features were tested but not used in the final champion.

Validation Strategy

Validation is time based. The final holdout window is from July 31 2017 to August 15 2017. Feature generation is anchored before the validation window starts. This prevents leakage from future sales and future transaction counts.

Rolling backtests were also used to compare candidate stability. This helped show that a later tuned model improved one validation window but did not generalize as well as the simpler two model blend.

Results

The final model achieved validation RMSLE 0.39568465 and validation MAE 60.996766. The public Kaggle score for the retained champion is 0.43992. The official submission has 28512 rows.

The official submission file is UC1_store_forecasting/submission.csv.

Error Analysis

The model does not show a large global bias. The main errors are concentrated in specific segments.

Low volume rows create the highest RMSLE risk. High volume promotion rows create the largest unit errors. The school and office supplies family is the clearest underprediction segment. Some stores show higher relative error while others show higher absolute error.

Limitations

The private leaderboard is unseen. Sparse demand, seasonal spikes, and promotion intensity remain difficult. Transaction features are historical proxies and not true future traffic forecasts.

Future Improvements

Future work should add more rolling folds, school season features, low demand calibration, promotion elasticity features, and monitoring by store, family, promotion status, and holiday status.

Use Case 2 ASL Detection

Problem

The ASL use case detects hand signs for letters A through J from webcam frames. The goal is a simple local demo where a reviewer can show a hand sign and see an annotated detection.

Dataset Collection

The dataset is a Roboflow YOLOv8 export created on June 6 2026. It contains 306 images across 10 classes. The source export contains 256 training images and 50 test images.

Annotation Process

Labels use YOLOv8 bounding box format with a class id and normalized box coordinates. The dataset has 309 bounding box annotations. The class distribution is balanced enough for an assessment demo. Dataset metadata, summary, and annotation samples are included in the repository.

Model Architecture

The trained detector is saved as UC2_ASL_detection/best.pt. The inference script loads the model, opens the webcam with OpenCV, runs detection on each frame, and displays annotated output with class labels and confidence.

The root architecture diagram is diagrams/UC2_architecture.png.

Evaluation

The ASL evaluation artifacts are stored in UC2_ASL_detection/reports. They include training results, metric curves, raw confusion matrix, normalized confusion matrix, precision curve, recall curve, F1 curve, and precision recall curve.

The best observed strict localization metric occurred at epoch 54. Precision was 0.92037, recall was 0.91934, mAP50 was 0.96833, and the stricter mAP range score was 0.65328.

The confusion matrix shows strong performance for classes C, F, and G. Some classes such as H and J are weaker in the available test examples.

Live Demo

The live demo is run from the UC2_ASL_detection folder after installing requirements. The script is UC2_ASL_detection/run_webcam_inference.py. A webcam window opens and shows bounding boxes, predicted class, confidence, and frame rate.

Limitations

The dataset is small and covers only letters A through J. The model is best suited to a controlled demo with clear lighting and centered hand signs. A production system would need more users, more lighting conditions, more backgrounds, more devices, and a separate holdout set.

Future Improvements

Future work should expand the class set, collect more diverse examples, add a true validation split, evaluate on unseen users, and package the webcam demo with a simple user interface.

Use Case 3 Hybrid RAG

Problem

The Hybrid RAG use case answers questions from a configured NCERT Physics PDF. The main requirement is grounding. Answers should be based on retrieved document evidence and should include citations.

Architecture

The system has a FastAPI backend, Streamlit frontend, PDF ingestion pipeline, ChromaDB vector store, BM25 keyword index, Neo4j graph store, and Ollama with Qwen3 for answer generation.

The root architecture diagram is diagrams/UC3_architecture.png.

Ingestion Pipeline

The ingestion pipeline reads UC3_hybrid_RAG/data/physics.pdf, extracts text and metadata, creates chunks, generates embeddings, builds the keyword index, and writes concept and formula relationships into Neo4j.

Hybrid Retrieval Design

The retrieval layer combines semantic search through ChromaDB, keyword search through BM25, and graph retrieval through Neo4j. The hybrid retriever merges evidence, removes duplicates, and passes grounded context to the answer step.

Grounding Strategy

The language model receives the user question and retrieved context. Citations are preserved from metadata and returned with the answer. Unsupported questions return a fixed refusal instead of a guessed answer.

Results

Evaluation examples include Coulombs Law, Electric Field, Electric Potential, and Amperes Circuital Law. Supported questions return cited evidence from the PDF. Unsupported questions return the fixed refusal response.

Limitations

The system is tuned for one PDF. Formula extraction depends on text extraction quality. The graph is heuristic and not expert curated. There is no reranker layer. Production deployment would need monitoring, access control, latency controls, and a larger evaluation set.

Future Improvements

Future work should add reranking, improve formula parsing, add OCR fallback, build a citation benchmark, and harden ingestion validation checks.

Overall Learnings

The three use cases show different architecture concerns.

Forecasting depends on leakage safe validation, careful feature design, and generalization checks.

Computer vision depends on dataset quality, visible evaluation artifacts, and a fast demo path.

RAG depends on retrieval observability, citations, and refusal behavior when evidence is missing.

Conclusion

The repository is now easier for reviewers to inspect. The root diagrams folder contains the architecture images requested by the prompt. The root README and final report have been simplified so they read more like human documentation and less like raw markdown.
