import numpy as np
import joblib
import os
from typing import List, Optional

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

COLORS = ["red", "yellow", "green", "blue"]


def models_exist():
    """Check if trained models are saved on disk."""
    required = [
        "naive_bayes.joblib",
        "label_encoder.joblib",
        "decision_tree.joblib",
        "kmeans.joblib",
        "pca.joblib",
    ]
    return all(
        os.path.exists(os.path.join(MODELS_DIR, f)) for f in required
    )


def load_model(filename):
    """Load a single saved model file."""
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {filename}. Run POST /ml/train first.")
    return joblib.load(path)


def build_single_vector(answers: list, color_scores: dict) -> np.ndarray:
    """
    Build a feature vector for one user — same structure as trainer.py.
    Used to score a brand new quiz response in real time.
    """
    total = sum(color_scores.values()) or 1
    score_vector = [
        color_scores.get("red",    0) / total,
        color_scores.get("yellow", 0) / total,
        color_scores.get("green",  0) / total,
        color_scores.get("blue",   0) / total,
    ]
    return np.array(answers + score_vector, dtype=float).reshape(1, -1)


def score_response(answers: list, color_scores: dict) -> dict:
    """
    Score a single new quiz response using the trained Naive Bayes model.
    Returns a probability breakdown across all 4 colors.

    This is what powers the confidence display on the result page:
    e.g. { red: 0.68, blue: 0.21, green: 0.08, yellow: 0.03 }
    """
    if not models_exist():
        # fall back to raw score percentages if models not trained yet
        total = sum(color_scores.values()) or 1
        return {c: round(color_scores.get(c, 0) / total, 3) for c in COLORS}

    clf = load_model("naive_bayes.joblib")
    le  = load_model("label_encoder.joblib")
    X   = build_single_vector(answers, color_scores)

    proba       = clf.predict_proba(X)[0]
    class_names = le.inverse_transform(range(len(proba)))

    return {name: round(float(prob), 3) for name, prob in zip(class_names, proba)}


def get_analytics(responses: list, current_session_id: Optional[str] = None) -> dict:
    """
    Aggregate all stored responses into the full analytics payload.
    Called by GET /analytics endpoint.

    Returns everything the dashboard needs in one response:
    - color distribution counts
    - PCA scatter points (one dot per user)
    - K-Means cluster assignments
    - correlation heatmap data
    - model confidence stats
    """

    # ── 1. color distribution ─────────────────────────────────────────────────
    distribution = {c: 0 for c in COLORS}
    combinations = {}

    for r in responses:
        dominant  = r.dominant_color
        secondary = r.secondary_color
        distribution[dominant] = distribution.get(dominant, 0) + 1

        combo = f"{dominant}_{secondary}"
        combinations[combo] = combinations.get(combo, 0) + 1

    total             = len(responses)
    most_common_combo = max(combinations, key=combinations.get) if combinations else "unknown"
    rarest_color      = min(distribution, key=distribution.get)

    color_distribution = {
        **distribution,
        "total": total
    }

    # ── 2. build feature matrix for all responses ─────────────────────────────
    X_list = []
    for r in responses:
        scores = r.color_scores
        t      = sum(scores.values()) or 1
        row    = r.answers + [
            scores.get("red",    0) / t,
            scores.get("yellow", 0) / t,
            scores.get("green",  0) / t,
            scores.get("blue",   0) / t,
        ]
        X_list.append(row)

    X = np.array(X_list, dtype=float)

    # ── 3. PCA projection + K-Means clusters ──────────────────────────────────
    cluster_points  = []
    model_trained   = models_exist()

    if model_trained:
        try:
            pca = load_model("pca.joblib")
            km  = load_model("kmeans.joblib")

            X_2d     = pca.transform(X)
            clusters = km.predict(X)

            for i, r in enumerate(responses):
                x_coord = round(float(X_2d[i, 0]), 4)
                y_coord = round(float(X_2d[i, 1]), 4) if X_2d.shape[1] > 1 else 0.0

                cluster_points.append({
                    "x":               x_coord,
                    "y":               y_coord,
                    "cluster":         int(clusters[i]),
                    "dominant_color":  r.dominant_color,
                    "is_current_user": r.session_id == current_session_id
                })

        except Exception as e:
            print(f"PCA/KMeans scoring failed: {e}")
            model_trained = False

    # ── 4. correlation heatmap data ───────────────────────────────────────────
    correlation_data = []
    corr_path        = os.path.join(MODELS_DIR, "correlations.joblib")

    if os.path.exists(corr_path):
        correlation_data = joblib.load(corr_path)

    # ── 5. naive bayes confidence across all users ────────────────────────────
    confidence_stats = {}

    if model_trained:
        try:
            clf = load_model("naive_bayes.joblib")
            le  = load_model("label_encoder.joblib")

            all_proba   = clf.predict_proba(X)
            max_conf    = float(np.mean(np.max(all_proba, axis=1)))
            confidence_stats = {
                "mean_confidence": round(max_conf, 3),
                "high_confidence_pct": round(
                    float(np.mean(np.max(all_proba, axis=1) > 0.7)), 3
                )
            }
        except Exception as e:
            print(f"Confidence stats failed: {e}")

    # ── 6. decision tree feature importances ─────────────────────────────────
    feature_importances = []
    fi_path             = os.path.join(MODELS_DIR, "feature_importances.joblib")

    if os.path.exists(fi_path):
        feature_importances = joblib.load(fi_path)

    return {
        "total_responses":       total,
        "color_distribution":    color_distribution,
        "cluster_points":        cluster_points,
        "correlation_data":      correlation_data,
        "model_trained":         model_trained,
        "most_common_combination": most_common_combo.replace("_", " × "),
        "rarest_color":          rarest_color,
        "confidence_stats":      confidence_stats,
        "feature_importances":   feature_importances,
    }