class HybridRecommender:
    def __init__(self, user_cf, mf, w_cf=0.5, w_mf=0.5):
        # CF có thể None
        self.user_cf = user_cf

        # MF luôn có
        self.mf = mf

        # Trọng số hybrid
        self.w_cf = w_cf
        self.w_mf = w_mf

    def recommend(self, userId, movies, top_n=10):
        all_movieIds = movies["movieId"].tolist()
        scores = []

        for movieId in all_movieIds:

            # ----- CF score -----
            if self.user_cf is not None:
                try:
                    cf_score = self.user_cf.predict(userId, movieId)
                except Exception:
                    cf_score = 0
            else:
                cf_score = 0

            # ----- MF score (luôn có) -----
            mf_score = self.mf.predict(userId, movieId)

            # ----- Hybrid -----
            final = cf_score * self.w_cf + mf_score * self.w_mf

            scores.append((movieId, final))

        # Sắp xếp theo điểm
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        if top_n is not None:
            scores = scores[:top_n]

        # Build output
        results = []
        for movieId, score in scores:
            row = movies.loc[movies["movieId"] == movieId].iloc[0]
            results.append({
                "movieId": movieId,
                "title": row["title"],
                "score": float(score),
                "metadata": {"title": row["title"]},
            })

        return results
