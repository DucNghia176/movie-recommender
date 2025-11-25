# ===== FIX IMPORT PATH =====
import sys, os
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "src"))
# ============================

from flask import Flask, jsonify, render_template, request
from config import web_config
from utils import (
    RecommenderBundle,
    candidate_items,
    get_recommender_bundle,
)

app = Flask(__name__)


def _serialize(recs):
    output = []
    for r in recs:
        output.append({
            "movieId": r.get("movieId", None),
            "title": r.get("title", None),
            "score": r.get("score", 0),
            "metadata": r.get("metadata"),
        })
    return output


@app.route("/", methods=["GET", "POST"])
def index():
    bundle = get_recommender_bundle()
    ready = bundle is not None
    recommendations = []
    error = None

    selected = request.form.get("algorithm", "hybrid")
    user_id = request.form.get("user_id", web_config.default_user_id)

    if request.method == "POST":
        if not ready:
            error = "Dataset not found. Please place movies.csv and ratings.csv into data/raw."
        else:
            try:
                user = int(user_id)

                if selected == "user_cf":
                    recs = bundle.user_cf.recommend(user, bundle.movies)
                    recommendations = _serialize([
                        {
                            "movieId": r.movieId,
                            "score": r.score,
                            "title": r.metadata["title"] if r.metadata else None,
                        } for r in recs
                    ])

                elif selected == "item_cf":
                    recs = bundle.item_cf.recommend(user, bundle.movies)
                    recommendations = _serialize([
                        {
                            "movieId": r.movieId,
                            "score": r.score,
                            "title": r.metadata["title"] if r.metadata else None,
                        } for r in recs
                    ])

                elif selected == "svd":
                    cand = candidate_items(bundle)
                    recs = bundle.svd.recommend(
                        userId=user,
                        candidate_items=cand,
                        top_n=web_config.recommendations_limit,
                        movies=bundle.movies,
                    )
                    recommendations = _serialize(recs)

                else:
                    recs = bundle.hybrid.recommend(
                        user,
                        bundle.movies,
                        top_n=web_config.recommendations_limit,
                    )
                    recommendations = _serialize(recs)

            except Exception as exc:
                error = str(exc)

    return render_template(
        "index.html",
        ready=ready,
        recommendations=recommendations,
        error=error,
        selected_algorithm=selected,
        default_user=user_id,
    )

@app.route("/api/users")
def api_users():
    bundle = get_recommender_bundle()
    if bundle is None:
        return jsonify([])

    user_ids = bundle.ratings["userId"].unique().tolist()
    user_ids = sorted(user_ids)
    return jsonify(user_ids)


if __name__ == "__main__":
    app.run(debug=True)
