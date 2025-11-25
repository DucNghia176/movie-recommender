import numpy as np
from dataclasses import dataclass, field
from config import ModelConfig, model_config



@dataclass
class MFRecommender:
    cfg: ModelConfig = field(default_factory=lambda: model_config)

    def fit(self, ratings):
        # Chuẩn hóa rating (tránh overflow khi nhân nhiều)
        ratings = ratings.copy()
        ratings["rating"] = ratings["rating"].astype(float)
        ratings["rating"] /= ratings["rating"].max()

        users = ratings["userId"].astype(int).values
        items = ratings["movieId"].astype(int).values
        rates = ratings["rating"].astype(float).values

        n_users = users.max() + 1
        n_items = items.max() + 1

        # Ma trận latent factors
        self.P = np.random.normal(scale=0.1, size=(n_users, self.cfg.latent_factors))
        self.Q = np.random.normal(scale=0.1, size=(n_items, self.cfg.latent_factors))

        lr = self.cfg.learning_rate
        reg = self.cfg.reg
        batch = 8192  # Mini-batch size (tối ưu nhất)

        for epoch in range(self.cfg.epochs):
            idx = np.random.permutation(len(rates))

            for start in range(0, len(rates), batch):
                end = start + batch
                batch_idx = idx[start:end]

                u = users[batch_idx]
                i = items[batch_idx]
                r = rates[batch_idx]

                # Predict vectorized
                preds = np.sum(self.P[u] * self.Q[i], axis=1)

                # error
                err = r - preds

                # gradient descent vectorized
                dP = (err[:, None] * self.Q[i]) - reg * self.P[u]
                dQ = (err[:, None] * self.P[u]) - reg * self.Q[i]

                # update
                self.P[u] += lr * dP
                self.Q[i] += lr * dQ

            print(f"[MF] Epoch {epoch+1}/{self.cfg.epochs} done")

        return self

    def predict(self, userId, itemId):
        if userId >= len(self.P) or itemId >= len(self.Q):
            return 0
        return np.dot(self.P[userId], self.Q[itemId])

    def recommend(self, userId, candidate_items, top_n=10, movies=None):
        scores = []

        for m in candidate_items:
            if m < len(self.Q):
                score = self.predict(userId, m)
                scores.append((m, score))

        scores = sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]

        output = []
        for mid, sc in scores:
            meta = movies[movies["movieId"] == mid]
            title = meta.iloc[0]["title"] if len(meta) else None

            output.append({
                "movieId": mid,
                "score": float(sc),
                "title": title,
                "metadata": {"title": title},
            })

        return output
