import pandas as pd
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

data = pd.read_csv("../dataset/role_dataset (2).csv")

X = data["Resume"]
y= data["Category"]

vectorizer = TfidfVectorizer(max_features=5000)
X_vec = vectorizer.fit_transform(X)

model = LogisticRegression(max_iter=1000)

model.fit(X_vec, y)

pickle.dump(
    vectorizer,
    open("tfidf.pkl", "wb")
)

pickle.dump(
    model,
    open("role_classifier.pkl", "wb")
)

print("Model Trained Successfully")