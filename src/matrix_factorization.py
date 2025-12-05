import numpy as np
from dataclasses import dataclass, field
from config import ModelConfig, model_config


@dataclass
class MFRecommender:
    cfg: ModelConfig = field(default_factory=lambda: model_config)

    def fit(self, ratings):
        # Normalize ratings to avoid overflow during training
        ratings = ratings.copy()
        ratings["rating"] = ratings["rating"].astype(float)
        ratings["rating"] /= ratings["rating"].max()

        users = ratings["userId"].astype(int).values
        items = ratings["movieId"].astype(int).values
        rates = ratings["rating"].astype(float).values

        n_users = users.max() + 1
        n_items = items.max() + 1

        # Latent factors matrices
        self.P = np.random.normal(scale=0.1, size=(n_users, self.cfg.latent_factors))
        self.Q = np.random.normal(scale=0.1, size=(n_items, self.cfg.latent_factors))

        print(
            f"[MF] Start training: users={n_users}, items={n_items}, "
            f"factors={self.cfg.latent_factors}, epochs={self.cfg.epochs}"
        )
        lr = self.cfg.learning_rate
        reg = self.cfg.reg
        batch = 8192  # mini-batch size

        for epoch in range(self.cfg.epochs):
            idx = np.random.permutation(len(rates))

            for start in range(0, len(rates), batch):
                end = start + batch
                batch_idx = idx[start:end]

                u = users[batch_idx]
                i = items[batch_idx]
                r = rates[batch_idx]

                preds = np.sum(self.P[u] * self.Q[i], axis=1)
                err = r - preds

                dP = (err[:, None] * self.Q[i]) - reg * self.P[u]
                dQ = (err[:, None] * self.P[u]) - reg * self.Q[i]

                self.P[u] += lr * dP
                self.Q[i] += lr * dQ

            print(f"[MF] Epoch {epoch+1}/{self.cfg.epochs} done")

        print("[MF] Training completed")
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

        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        if top_n is not None:
            scores = scores[:top_n]

        output = []
        for mid, sc in scores:
            meta = movies[movies["movieId"] == mid] if movies is not None else None
            title = meta.iloc[0]["title"] if meta is not None and len(meta) else None

            output.append({
                "movieId": mid,
                "score": float(sc),
                "title": title,
                "metadata": {"title": title} if title else None,
            })

        return output
