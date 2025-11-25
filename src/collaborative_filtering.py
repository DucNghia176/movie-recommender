# collaborative_filtering.py
import numpy as np
import pandas as pd
from dataclasses import dataclass
from config import model_config


def cosine_similarity_manual(matrix):
    norm = np.linalg.norm(matrix, axis=1, keepdims=True)
    norm_matrix = matrix / (norm + 1e-10)
    return norm_matrix @ norm_matrix.T


@dataclass
class Recommendation:
    movieId: int
    score: float
    metadata: dict | None = None


class UserBasedCF:
    def __init__(self, cfg=model_config):
        self.k = cfg.user_based_neighbors

    def fit(self, ratings):
        matrix = ratings.pivot_table(index="userId", columns="movieId", values="rating").fillna(0)
        self.matrix = matrix
        self.similarity = pd.DataFrame(
            cosine_similarity_manual(matrix.to_numpy()),
            index=matrix.index,
            columns=matrix.index,
        )
        return self

    def predict(self, userId, movieId):
        if movieId not in self.matrix.columns:
            return 0

        sims = self.similarity.loc[userId].drop(userId, errors="ignore")
        neighbors = sims.nlargest(self.k)
        neigh_ratings = self.matrix.loc[neighbors.index, movieId]

        mask = neigh_ratings > 0
        if mask.sum() == 0:
            return float(self.matrix.loc[userId].replace(0, np.nan).mean())

        return float((neigh_ratings[mask] * neighbors[mask]).sum() / neighbors[mask].abs().sum())

    def recommend(self, userId, movies, top_n=10):
        user_vector = self.matrix.loc[userId]
        unseen = user_vector[user_vector == 0]

        preds = [(movieId, self.predict(userId, movieId)) for movieId in unseen.index]

        preds = sorted(preds, key=lambda x: x[1], reverse=True)[:top_n]

        recs = []
        for movieId, score in preds:
            movie = movies.loc[movies["movieId"] == movieId]
            meta = {"title": movie["title"].iloc[0]} if not movie.empty else None
            recs.append(Recommendation(movieId, score, meta))

        return recs
