import os
import json
import re
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

dataset_path = r"C:\Users\rreji\OneDrive\Documents\AI interview assistant\dataset\role_dataset (2).csv"
model_save_dir = r"C:\Users\rreji\OneDrive\Documents\AI interview assistant\trained_model"

print("==================== PHASE 3: ROLE PREDICTION MODEL TRAINING & EVALUATION ====================")

if not os.path.exists(dataset_path):
    print(f"Dataset missing at {dataset_path}")
    exit(1)

df = pd.read_csv(dataset_path, encoding='latin1')
print(f"1. Dataset Loaded: {len(df)} rows, {df['Category'].nunique()} categories")

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['clean_resume'] = df['Resume'].apply(clean_text)

# 2. Data Leakage Prevention — Deduplicate exact/normalized resume texts
df_dedup = df.drop_duplicates(subset=['clean_resume']).copy()
print(f"2. After Deduplication: {len(df_dedup)} unique resume samples (Removed {len(df) - len(df_dedup)} duplicates)")

# Filter categories with at least 2 samples for stratified splitting
cat_counts = df_dedup['Category'].value_counts()
valid_cats = cat_counts[cat_counts >= 2].index
df_filtered = df_dedup[df_dedup['Category'].isin(valid_cats)].copy()
print(f"3. Valid Categories (>=2 samples): {len(valid_cats)} categories, {len(df_filtered)} samples")

X = df_filtered['clean_resume']
y = df_filtered['Category']

# Stratified Train (70%), Test (30%) Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y
)
print(f"4. Stratified Split: Train={len(X_train)} samples, Test={len(X_test)} samples")


# 5. Evaluate Baseline Existing Model (if present)
baseline_metrics = {"model_name": "Existing Baseline (Logistic Regression)"}
existing_model_path = os.path.join(model_save_dir, "role_classifier.pkl")
existing_tfidf_path = os.path.join(model_save_dir, "tfidf.pkl")

if os.path.exists(existing_model_path) and os.path.exists(existing_tfidf_path):
    try:
        with open(existing_model_path, "rb") as f:
            old_clf = pickle.load(f)
        with open(existing_tfidf_path, "rb") as f:
            old_vec = pickle.load(f)

        X_test_vec = old_vec.transform(X_test)
        old_preds = old_clf.predict(X_test_vec)

        acc = accuracy_score(y_test, old_preds)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, old_preds, average='macro', zero_division=0)
        _, _, wf1, _ = precision_recall_fscore_support(y_test, old_preds, average='weighted', zero_division=0)

        baseline_metrics.update({
            "accuracy": round(float(acc), 4),
            "macro_precision": round(float(prec), 4),
            "macro_recall": round(float(rec), 4),
            "macro_f1": round(float(f1), 4),
            "weighted_f1": round(float(wf1), 4)
        })
        print("\n--- EXISTING MODEL PERFORMANCE ---")
        print(f"Accuracy:    {baseline_metrics['accuracy']}")
        print(f"Macro F1:    {baseline_metrics['macro_f1']}")
        print(f"Weighted F1: {baseline_metrics['weighted_f1']}")
    except Exception as e:
        print(f"Could not evaluate existing model: {e}")


# 6. Train New Model 1: Logistic Regression Pipeline
pipe_lr = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=3000, stop_words='english')),
    ('clf', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
])
pipe_lr.fit(X_train, y_train)
lr_preds = pipe_lr.predict(X_test)

lr_acc = accuracy_score(y_test, lr_preds)
lr_prec, lr_rec, lr_f1, _ = precision_recall_fscore_support(y_test, lr_preds, average='macro', zero_division=0)
_, _, lr_wf1, _ = precision_recall_fscore_support(y_test, lr_preds, average='weighted', zero_division=0)

lr_metrics = {
    "model_name": "New Logistic Regression (Balanced)",
    "accuracy": round(float(lr_acc), 4),
    "macro_precision": round(float(lr_prec), 4),
    "macro_recall": round(float(lr_rec), 4),
    "macro_f1": round(float(lr_f1), 4),
    "weighted_f1": round(float(lr_wf1), 4)
}

print("\n--- NEW LOGISTIC REGRESSION PERFORMANCE ---")
print(f"Accuracy:    {lr_metrics['accuracy']}")
print(f"Macro F1:    {lr_metrics['macro_f1']}")
print(f"Weighted F1: {lr_metrics['weighted_f1']}")


# 7. Train New Model 2: Calibrated Linear SVM Pipeline (cv=2 for small dataset classes)
base_svc = LinearSVC(class_weight='balanced', max_iter=2000, random_state=42)
calibrated_svc = CalibratedClassifierCV(estimator=base_svc, cv=2)

pipe_svm = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=3000, stop_words='english')),
    ('clf', calibrated_svc)
])
pipe_svm.fit(X_train, y_train)
svm_preds = pipe_svm.predict(X_test)

svm_acc = accuracy_score(y_test, svm_preds)
svm_prec, svm_rec, svm_f1, _ = precision_recall_fscore_support(y_test, svm_preds, average='macro', zero_division=0)
_, _, svm_wf1, _ = precision_recall_fscore_support(y_test, svm_preds, average='weighted', zero_division=0)

svm_metrics = {
    "model_name": "New Calibrated Linear SVM (Balanced)",
    "accuracy": round(float(svm_acc), 4),
    "macro_precision": round(float(svm_prec), 4),
    "macro_recall": round(float(svm_rec), 4),
    "macro_f1": round(float(svm_f1), 4),
    "weighted_f1": round(float(svm_wf1), 4)
}

print("\n--- NEW CALIBRATED LINEAR SVM PERFORMANCE ---")
print(f"Accuracy:    {svm_metrics['accuracy']}")
print(f"Macro F1:    {svm_metrics['macro_f1']}")
print(f"Weighted F1: {svm_metrics['weighted_f1']}")


# 8. Model Comparison & Selection
models_comparison = [lr_metrics, svm_metrics]
if "accuracy" in baseline_metrics:
    models_comparison.insert(0, baseline_metrics)

print("\n==================== MODEL COMPARISON TABLE ====================")
print(f"{'Model Name':<40} | {'Accuracy':<10} | {'Macro F1':<10} | {'Weighted F1':<10}")
print("-" * 77)
for m in models_comparison:
    print(f"{m['model_name']:<40} | {m['accuracy']:<10} | {m['macro_f1']:<10} | {m['weighted_f1']:<10}")

# Select best model based on Macro F1
best_model_info = lr_metrics if lr_metrics["macro_f1"] >= svm_metrics["macro_f1"] else svm_metrics
winning_pipeline = pipe_lr if best_model_info == lr_metrics else pipe_svm

print(f"\nWinning Model Selected: {best_model_info['model_name']}")

# Save winning pipeline & metadata metrics
pipeline_path = os.path.join(model_save_dir, "role_prediction_pipeline.pkl")
metrics_path = os.path.join(model_save_dir, "role_model_metrics.json")

with open(pipeline_path, "wb") as f:
    pickle.dump(winning_pipeline, f)

metrics_export = {
    "dataset": "role_dataset (2).csv",
    "total_rows": len(df),
    "unique_dedup_rows": len(df_dedup),
    "train_rows": len(X_train),
    "test_rows": len(X_test),
    "categories_count": len(valid_cats),
    "winning_model": best_model_info["model_name"],
    "accuracy": best_model_info["accuracy"],
    "macro_precision": best_model_info["macro_precision"],
    "macro_recall": best_model_info["macro_recall"],
    "macro_f1": best_model_info["macro_f1"],
    "weighted_f1": best_model_info["weighted_f1"],
    "comparison_all_models": models_comparison
}

with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics_export, f, indent=2)

print(f"Saved winning pipeline to: {pipeline_path}")
print(f"Saved metadata metrics to: {metrics_path}")
