import os
import json
import re
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, log_loss
)

dataset_path = r"C:\Users\rreji\OneDrive\Documents\AI interview assistant\dataset\role_dataset (2).csv"
model_save_dir = r"C:\Users\rreji\OneDrive\Documents\AI interview assistant\trained_model"

print("==================== PHASE 4: ML RELIABILITY & CALIBRATION ANALYSIS ====================")

df = pd.read_csv(dataset_path, encoding='latin1')

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['clean_resume'] = df['Resume'].apply(clean_text)
df_dedup = df.drop_duplicates(subset=['clean_resume']).copy()

cat_counts = df_dedup['Category'].value_counts()
valid_cats = cat_counts[cat_counts >= 2].index
df_filtered = df_dedup[df_dedup['Category'].isin(valid_cats)].copy()

X = df_filtered['clean_resume']
y = df_filtered['Category']
classes = sorted(list(y.unique()))
num_classes = len(classes)

# Stratified Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y
)

# Train Original and Calibrated Sigmoid LR
pipe_calibrated = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=3000, stop_words='english')),
    ('clf', CalibratedClassifierCV(
        estimator=LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42),
        method='sigmoid', cv=2
    ))
])
pipe_calibrated.fit(X_train, y_train)

winning_pipe = pipe_calibrated

# Evaluate Winning Pipeline
preds = winning_pipe.predict(X_test)
probs = winning_pipe.predict_proba(X_test)
acc = accuracy_score(y_test, preds)
prec, rec, f1, _ = precision_recall_fscore_support(y_test, preds, average='macro', zero_division=0)
_, _, wf1, _ = precision_recall_fscore_support(y_test, preds, average='weighted', zero_division=0)
l_loss = log_loss(y_test, probs, labels=winning_pipe.classes_)

# Cross-Validation of BASE model to show stability (min class size is 2, so inner CV for calibration fails)
skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
cv_accs, cv_macro_f1s, cv_weighted_f1s = [], [], []

for train_idx, val_idx in skf.split(X, y):
    X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
    y_tr, y_va = y.iloc[train_idx], y.iloc[val_idx]

    pipe_cv = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=3000, stop_words='english')),
        ('clf', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
    ])
    pipe_cv.fit(X_tr, y_tr)
    p_va = pipe_cv.predict(X_va)
    cv_accs.append(accuracy_score(y_va, p_va))
    _, _, f1_m, _ = precision_recall_fscore_support(y_va, p_va, average='macro', zero_division=0)
    _, _, f1_w, _ = precision_recall_fscore_support(y_va, p_va, average='weighted', zero_division=0)
    cv_macro_f1s.append(f1_m)
    cv_weighted_f1s.append(f1_w)

# Top 5 Demonstration
sample_resumes = {
    "Data Scientist": "Passionate Data Scientist skilled in Python, Machine Learning, Deep Learning, scikit-learn, TensorFlow, PyTorch, Pandas, NumPy.",
    "Java Developer": "Enterprise Java Developer proficient in Java, J2EE, Spring Boot, Hibernate, SQL, MySQL, and REST APIs.",
    "Web Designer": "Creative Web Designer skilled in HTML, CSS, JavaScript, Web Designing, Figma, Photoshop, Bootstrap."
}
top_predictions_demo = {}
for label, r_text in sample_resumes.items():
    p = winning_pipe.predict_proba([r_text])[0]
    pairs = sorted(zip(winning_pipe.classes_, p), key=lambda x: x[1], reverse=True)
    top_predictions_demo[label] = [{"role": cp[0], "probability": round(float(cp[1]), 4)} for cp in pairs[:5]]

# Save Artifacts
pipeline_path = os.path.join(model_save_dir, "role_prediction_pipeline.pkl")
metrics_path = os.path.join(model_save_dir, "role_model_metrics.json")

with open(pipeline_path, "wb") as f:
    pickle.dump(winning_pipe, f)

metrics_export = {
    "dataset": "role_dataset (2).csv",
    "raw_samples": len(df),
    "unique_samples": len(df_filtered),
    "categories_count": num_classes,
    "selected_model": "Calibrated Sigmoid LR (class_weight='balanced')",
    "calibration_method": "sigmoid",
    "test_accuracy": round(float(acc), 4),
    "test_macro_f1": round(float(f1), 4),
    "test_weighted_f1": round(float(wf1), 4),
    "test_log_loss": round(float(l_loss), 4),
    "cross_validation": {
        "n_splits": 2,
        "mean_accuracy": round(float(np.mean(cv_accs)), 4),
        "std_accuracy": round(float(np.std(cv_accs)), 4),
        "mean_macro_f1": round(float(np.mean(cv_macro_f1s)), 4),
        "std_macro_f1": round(float(np.std(cv_macro_f1s)), 4),
        "mean_weighted_f1": round(float(np.mean(cv_weighted_f1s)), 4),
        "std_weighted_f1": round(float(np.std(cv_weighted_f1s)), 4)
    },
    "top_predictions_demo": top_predictions_demo
}

with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics_export, f, indent=2)

print("Saved Calibrated Sigmoid LR pipeline.")
