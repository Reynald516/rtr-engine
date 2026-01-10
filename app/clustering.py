# app/clustering.py
from sklearn.cluster import KMeans
import pandas as pd

def cluster_user(feature_matrix: pd.DataFrame, n_clusters=4):
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(feature_matrix)
    return clusters, kmeans