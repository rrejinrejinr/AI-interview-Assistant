import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import spearmanr

dataset_path = r"C:\Users\rreji\OneDrive\Documents\AI interview assistant\dataset\resume_dataset.csv"
model_save_dir = r"C:\Users\rreji\OneDrive\Documents\AI interview assistant\trained_model"
os.makedirs(model_save_dir, exist_ok=True)

print("==================== SUPERVISED ATS MODEL TRAINING & EVALUATION ====================")

if not os.path.exists(dataset_path):
    print(f"Dataset path missing: {dataset_path}")
    exit(1)

df = pd.read_csv(dataset_path, encoding='latin1')
print(f"Loaded dataset: {len(df)} rows")

# Drop rows missing target or essential columns
df = df.dropna(subset=['matched_score'])
df['skills'] = df['skills'].fillna('')
df['skills_required'] = df['skills_required'].fillna('')
df['career_objective'] = df['career_objective'].fillna('')

print(f"Rows after target cleanup: {len(df)}")

# Feature Engineering
print("\nEngineering features...")

# 1. TF-IDF Similarity between resume skills + objective vs required skills
df['resume_combined'] = df['skills'] + " " + df['career_objective']
df['jd_combined'] = df['skills_required']

vectorizer = TfidfVectorizer(max_features=3000, stop_words='english')
resume_vecs = vectorizer.fit_transform(df['resume_combined'])
jd_vecs = vectorizer.transform(df['jd_combined'])

# Compute cosine similarity per pair
sim_scores = []
for i in range(len(df)):
    sim = cosine_similarity(resume_vecs[i], jd_vecs[i])[0][0]
    sim_scores.append(sim)

df['tfidf_similarity'] = sim_scores

# 2. Skill count features
def count_items(text):
    if not text:
        return 0
    return len([x.strip() for x in str(text).split(',') if x.strip()])

df['resume_skill_count'] = df['skills'].apply(count_items)
df['jd_skill_count'] = df['skills_required'].apply(count_items)

# 3. Simple exact match overlap count
def calculate_overlap_count(row):
    r_skills = set([x.strip().lower() for x in str(row['skills']).split(',') if x.strip()])
    j_skills = set([x.strip().lower() for x in str(row['skills_required']).split(',') if x.strip()])
    if not j_skills:
        return 0, 0, 1.0
    matched = r_skills.intersection(j_skills)
    missing = j_skills - r_skills
    match_ratio = len(matched) / len(j_skills)
    return len(matched), len(missing), match_ratio

overlaps = df.apply(calculate_overlap_count, axis=1)
df['matched_count'] = [o[0] for o in overlaps]
df['missing_count'] = [o[1] for o in overlaps]
df['skill_match_ratio'] = [o[2] for o in overlaps]

X = df[['tfidf_similarity', 'skill_match_ratio', 'matched_count', 'missing_count', 'resume_skill_count', 'jd_skill_count']]
y = df['matched_score']

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"\nTrain set: {len(X_train)} samples, Test set: {len(X_test)} samples")

# Evaluate Baseline Rule (50/50 weighted combination scaled to 0-1)
baseline_pred = (df.loc[X_test.index, 'tfidf_similarity'] * 0.50) + (df.loc[X_test.index, 'skill_match_ratio'] * 0.50)
b_mae = mean_absolute_error(y_test, baseline_pred)
b_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
b_r2 = r2_score(y_test, baseline_pred)
b_spearman, _ = spearmanr(y_test, baseline_pred)

print("\n--- 1. BASELINE ATS (50/50 Deterministic Weighting) ---")
print(f"MAE:  {b_mae:.4f}")
print(f"RMSE: {b_rmse:.4f}")
print(f"R²:   {b_r2:.4f}")
print(f"Spearman Correlation: {b_spearman:.4f}")

# Train Supervised Models
models = {
    "Ridge Regression": Ridge(alpha=1.0),
    "Linear Regression": LinearRegression(),
    "Random Forest Regressor": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
}

best_model = None
best_r2 = -999

for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    spearman, _ = spearmanr(y_test, preds)

    print(f"\n--- Supervised Model: {name} ---")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²:   {r2:.4f}")
    print(f"Spearman Correlation: {spearman:.4f}")

    if r2 > best_r2:
        best_r2 = r2
        best_model = (name, model)

# Save best supervised model
if best_model:
    model_path = os.path.join(model_save_dir, "ats_ranking_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": best_model[1], "vectorizer": vectorizer, "model_name": best_model[0]}, f)
    print(f"\nSaved best supervised model ({best_model[0]}) to {model_path}")
