# backend/ml/clustering.py

import numpy as np
from sklearn.cluster import KMeans
from backend.ml.features import CATEGORIES

class SpendingClusterer:
    """
    Fits K-Means on user spending vectors and predicts which cluster
    a new user belongs to.
    """

    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self._kmeans: KMeans | None = None

    @property
    def is_fitted(self) -> bool:
        return self._kmeans is not None

    def _to_matrix(self, profiles: list) -> np.ndarray:
        return np.array([[p["vector"][cat] for cat in CATEGORIES] for p in profiles])

    def fit(self, profiles: list) -> None:
        """Train on a list of {user_id, vector} dicts."""
        X = self._to_matrix(profiles)
        self._kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init="auto")
        self._kmeans.fit(X)

    def predict(self, vector: dict) -> int:
        """Return the cluster ID for a single spending vector."""
        if not self.is_fitted:
            raise RuntimeError("Clusterer must be fitted before predicting.")
        row = np.array([[vector.get(cat, 0.0) for cat in CATEGORIES]])
        return int(self._kmeans.predict(row)[0])

    def cluster_centers(self) -> list[dict]:
        """Return each cluster center as a normalized spending vector dict."""
        if not self.is_fitted:
            raise RuntimeError("Clusterer must be fitted before accessing centers.")
        centers = []
        for row in self._kmeans.cluster_centers_:
            row = np.clip(row, 0, None)
            total = row.sum() or 1.0
            centers.append({cat: float(row[i] / total) for i, cat in enumerate(CATEGORIES)})
        return centers
