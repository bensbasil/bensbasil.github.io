import os
import glob
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")

class ModelLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance.model_primary = None
            cls._instance.le_primary = None
            cls._instance.model_stress = None
            cls._instance.le_stress = None
            cls._instance.primary_version = None
            cls._instance.stress_version = None
            cls._instance.load_latest_models()
        return cls._instance

    def load_latest_models(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        primary_files = glob.glob(os.path.join(MODELS_DIR, "model_primary_v*.pkl"))
        stress_files = glob.glob(os.path.join(MODELS_DIR, "model_stress_v*.pkl"))
        
        def extract_version(path):
            try:
                # e.g. "model_primary_v1.pkl"
                basename = os.path.basename(path)
                return int(basename.split("_v")[1].split(".pkl")[0])
            except (IndexError, ValueError):
                return -1

        if primary_files:
            latest_primary = max(primary_files, key=extract_version)
            data = joblib.load(latest_primary)
            self.model_primary = data["model"]
            self.le_primary = data["le"]
            self.primary_version = extract_version(latest_primary)
            
        if stress_files:
            latest_stress = max(stress_files, key=extract_version)
            data = joblib.load(latest_stress)
            self.model_stress = data["model"]
            self.le_stress = data["le"]
            self.stress_version = extract_version(latest_stress)

    def models_exist(self):
        return self.model_primary is not None and self.model_stress is not None

    def predict_primary(self, X):
        if not self.models_exist():
            return None
        proba = self.model_primary.predict_proba(X)[0]
        class_names = self.le_primary.inverse_transform(range(len(proba)))
        return {str(name): round(float(prob), 3) for name, prob in zip(class_names, proba)}

    def predict_stress(self, X):
        if not self.models_exist():
            return None, 0.0
        proba = self.model_stress.predict_proba(X)[0]
        best_idx = proba.argmax()
        label = self.le_stress.inverse_transform([best_idx])[0]
        confidence = round(float(proba[best_idx]), 3)
        return str(label), confidence

model_loader = ModelLoader()
