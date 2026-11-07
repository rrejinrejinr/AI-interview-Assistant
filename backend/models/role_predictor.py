import os
import pickle

PIPELINE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "trained_model", "role_prediction_pipeline.pkl"))
OLD_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "trained_model", "role_classifier.pkl"))
OLD_TFIDF_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "trained_model", "tfidf.pkl"))

pipeline = None
_pipeline_loaded = False

def get_pipeline():
    global pipeline, _pipeline_loaded

    if not _pipeline_loaded:
        _pipeline_loaded = True

        if os.path.exists(PIPELINE_PATH):
            try:
                with open(PIPELINE_PATH, "rb") as f:
                    pipeline = pickle.load(f)
            except Exception as e:
                print(f"Error loading role prediction pipeline: {e}")

    return pipeline
def get_confidence_level(top_prob, num_classes=25):
    uniform_chance = 1.0 / num_classes
    if top_prob >= 3 * uniform_chance or top_prob >= 0.15:
        return "High"
    elif top_prob >= 2 * uniform_chance or top_prob >= 0.08:
        return "Medium"
    else:
        return "Low"

def predict_role(resume_text: str) -> dict:
    if not resume_text or not resume_text.strip():
        return {
            "predicted_role": "Software Engineer", 
            "confidence_level": "None",
            "top_predictions": []
        }

        model_pipeline = get_pipeline()

    if model_pipeline:
        try:
            role = str(model_pipeline.predict([resume_text])[0])
            confidence_level = "None"
            top_predictions = []

            if hasattr(model_pipeline, "predict_proba"):
                probs = model_pipeline.predict_proba([resume_text])[0]
                pairs = sorted(zip(model_pipeline.classes_, probs), key=lambda x: x[1], reverse=True)

                top_prob = float(pairs[0][1])
                confidence_level = get_confidence_level(top_prob, len(model_pipeline.classes_))
                
                top_predictions = [
                    {"role": str(cp[0]), "probability": round(float(cp[1]), 4)}
                    for cp in pairs[:3]
                ]

            return {
                "predicted_role": role,
                "confidence_level": confidence_level,
                "top_predictions": top_predictions
            }
        except Exception as e:
            print(f"Pipeline prediction error: {e}")

    # Fallback to old classifier if present
    if os.path.exists(OLD_MODEL_PATH) and os.path.exists(OLD_TFIDF_PATH):
        try:
            with open(OLD_MODEL_PATH, "rb") as f:
                old_clf = pickle.load(f)
            with open(OLD_TFIDF_PATH, "rb") as f:
                old_vec = pickle.load(f)
            vec = old_vec.transform([resume_text])
            role = str(old_clf.predict(vec)[0])
            return {
                "predicted_role": role, 
                "confidence_level": "None",
                "top_predictions": []
            }
        except Exception:
            pass

    return {
        "predicted_role": "Software Engineer", 
        "confidence_level": "None",
        "top_predictions": []
    }
