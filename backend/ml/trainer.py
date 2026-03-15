import numpy as np
import joblib
import os
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# where trained models get saved
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def build_feature_matrix(responses):
    """
    Convert raw DB responses into a numpy feature matrix.

    Each row = one user.
    Each column = one answer index (0-3) for each question.
    Shape: (n_users, n_questions)
    """
    X = []
    y_dominant = []
    y_secondary = []

    for r in responses:
        answers = r.answers  # list like [0, 2, 1, 3, 0, ...]
        scores  = r.color_scores  # dict like {red:12, yellow:4, green:8, blue:6}

        # normalize scores into 4 float features (sum to 1.0)
        total = sum(scores.values()) or 1
        score_vector = [
            scores.get("red",    0) / total,
            scores.get("yellow", 0) / total,
            scores.get("green",  0) / total,
            scores.get("blue",   0) / total,
        ]

        # combine raw answers + normalized scores into one feature vector
        feature_row = answers + score_vector
        X.append(feature_row)
        y_dominant.append(r.dominant_color)
        y_secondary.append(r.secondary_color)

    return np.array(X, dtype=float), np.array(y_dominant), np.array(y_secondary)


def train_naive_bayes(X, y):
    """
    Gaussian Naive Bayes — gives probability distribution across all 4 colors.
    This is what powers the 'confidence score' on the result page.
    e.g. Red: 68%, Blue: 21%, Green: 8%, Yellow: 3%
    """
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    if len(X) < 10:
        # not enough data to split — train on everything
        clf = GaussianNB()
        clf.fit(X, y_encoded)
        accuracy = 1.0
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        clf = GaussianNB()
        clf.fit(X_train, y_train)
        y_pred    = clf.predict(X_test)
        accuracy  = accuracy_score(y_test, y_pred)

    joblib.dump(clf, os.path.join(MODELS_DIR, "naive_bayes.joblib"))
    joblib.dump(le,  os.path.join(MODELS_DIR, "label_encoder.joblib"))

    return {"model": "naive_bayes", "accuracy": round(accuracy, 3)}


def train_decision_tree(X, y):
    """
    Decision Tree — classifies dominant color from answer vector.
    max_depth=4 keeps it shallow enough to visualize on the dashboard.
    """
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    clf = DecisionTreeClassifier(
        max_depth       = 4,
        min_samples_leaf= 2,
        random_state    = 42
    )

    if len(X) < 10:
        clf.fit(X, y_encoded)
        accuracy = 1.0
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42
        )
        clf.fit(X_train, y_train)
        y_pred   = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

    joblib.dump(clf, os.path.join(MODELS_DIR, "decision_tree.joblib"))

    # also save feature importances — used in the heatmap on the dashboard
    importances = clf.feature_importances_.tolist()
    joblib.dump(importances, os.path.join(MODELS_DIR, "feature_importances.joblib"))

    return {"model": "decision_tree", "accuracy": round(accuracy, 3)}


def train_kmeans(X, n_clusters=4):
    """
    K-Means clustering — finds natural groupings in the data.
    We start with 4 clusters (matching our 4 colors) but the clusters
    the algorithm finds may not align perfectly — that's the interesting finding.
    """
    # cap clusters at number of samples
    k = min(n_clusters, len(X))

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X)

    joblib.dump(km, os.path.join(MODELS_DIR, "kmeans.joblib"))

    return {"model": "kmeans", "n_clusters": k, "inertia": round(km.inertia_, 2)}


def train_pca(X):
    """
    PCA — reduces the feature vector down to 2 dimensions so we can
    plot every user as a dot on a 2D scatter chart on the dashboard.
    """
    # need at least 2 samples and 2 features
    n_components = min(2, len(X), X.shape[1])

    pca = PCA(n_components=n_components)
    pca.fit(X)

    joblib.dump(pca, os.path.join(MODELS_DIR, "pca.joblib"))

    explained = pca.explained_variance_ratio_.tolist()
    return {"model": "pca", "explained_variance": [round(v, 3) for v in explained]}


def compute_correlations(X, y_dominant):
    """
    Pearson correlation between each question's answer and each color outcome.
    Returns a (n_questions, 4) matrix — used to draw the heatmap.
    """
    colors    = ["red", "yellow", "green", "blue"]
    n_questions = X.shape[1] - 4  # last 4 cols are score features, not questions

    correlations = []

    for q_idx in range(n_questions):
        row = {"question_index": q_idx}
        for c_idx, color in enumerate(colors):
            # binary: did this user's dominant color match this color?
            y_binary = (y_dominant == color).astype(float)
            col_vals = X[:, q_idx]

            if len(np.unique(col_vals)) < 2 or len(np.unique(y_binary)) < 2:
                row[color] = 0.0
            else:
                corr = np.corrcoef(col_vals, y_binary)[0, 1]
                row[color] = round(float(corr), 4) if not np.isnan(corr) else 0.0

        correlations.append(row)

    joblib.dump(correlations, os.path.join(MODELS_DIR, "correlations.joblib"))
    return correlations


def train_all(responses):
    """
    Master function — called by POST /ml/train endpoint.
    Runs all four algorithms in sequence and saves every model to disk.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    X, y_dominant, y_secondary = build_feature_matrix(responses)

    results = []
    results.append(train_naive_bayes(X, y_dominant))
    results.append(train_decision_tree(X, y_dominant))
    results.append(train_kmeans(X))
    results.append(train_pca(X))
    compute_correlations(X, y_dominant)

    # pick best accuracy from the supervised models
    supervised = [r for r in results if "accuracy" in r]
    best_accuracy = max(r["accuracy"] for r in supervised) if supervised else 0.0

    return {
        "models_trained": [r["model"] for r in results],
        "accuracy": best_accuracy
    }