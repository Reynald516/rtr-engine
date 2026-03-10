# app/clustering.py 

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

def cluster_user(feature_matrix: pd.DataFrame, n_clusters=4):
    if feature_matrix is None or feature_matrix.empty:
        return None, None

    if feature_matrix.shape[0] < n_clusters:
        return None, None

    if feature_matrix.isnull().any().any():
        feature_matrix = feature_matrix.fillna(0)

    if (feature_matrix.var() == 0).all():
        return None, None

    scaler = StandardScaler()
    X = scaler.fit_transform(feature_matrix)

    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    clusters = model.fit_predict(X)
    return clusters, model