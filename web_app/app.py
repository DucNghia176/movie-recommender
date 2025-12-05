# ===== FIX IMPORT PATH =====
import sys, os, math, csv
from pathlib import Path
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

# Cache directory for precomputed recommendations
CACHE_DIR = Path(ROOT_DIR) / "data" / "processed" / "recommendations"


def _serialize(recs):
    output = []
    for r in recs:
        meta = r.get("metadata")
        title = r.get("title", None)
        if meta is None and title:
            meta = {"title": title}
        output.append({
            "movieId": r.get("movieId", None),
            "title": title,
            "score": r.get("score", 0),
            "metadata": meta,
        })
    return output


def _cache_file(algorithm: str, user_id: int) -> Path:
    return CACHE_DIR / f"{algorithm}_user{user_id}.csv"


def _save_cache(path: Path, recs: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["movieId", "title", "score"])
        writer.writeheader()
        for r in recs:
            title = r.get("title") or (r.get("metadata") or {}).get("title")
            writer.writerow({
                "movieId": r.get("movieId"),
                "title": title,
                "score": r.get("score", 0),
            })


def _load_cache(path: Path) -> list[dict]:
    recs = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                score = float(row.get("score", 0))
            except Exception:
                score = 0
            movie_id = row.get("movieId")
            recs.append({
                "movieId": int(movie_id) if movie_id not in (None, "") else None,
                "title": row.get("title") or None,
                "score": score,
                "metadata": {"title": row.get("title")} if row.get("title") else None,
            })
    return recs


def _build_recommendations(bundle, selected: str, user: int, page: int) -> list[dict]:
    cache_path = _cache_file(selected, user)

    if cache_path.exists():
        return _load_cache(cache_path)

    if selected == "user_cf":
        if bundle.user_cf is None:
            raise RuntimeError("User-Based CF is not available.")
        recs = bundle.user_cf.recommend(user, bundle.movies, top_n=None)
        recommendations_all = _serialize([
            {
                "movieId": r.movieId,
                "score": r.score,
                "title": r.metadata["title"] if r.metadata else None,
            } for r in recs
        ])

    elif selected == "item_cf":
        if bundle.item_cf is None:
            raise RuntimeError("Item-Based CF is not available.")
        recs = bundle.item_cf.recommend(user, bundle.movies, top_n=None)
        recommendations_all = _serialize([
            {
                "movieId": r.movieId,
                "score": r.score,
                "title": r.metadata["title"] if r.metadata else None,
            } for r in recs
        ])

    elif selected == "svd":
        cand = candidate_items(bundle, limit=None)
        recs = bundle.svd.recommend(
            userId=user,
            candidate_items=cand,
            top_n=None,
            movies=bundle.movies,
        )
        recommendations_all = _serialize(recs)

    else:
        recs = bundle.hybrid.recommend(
            user,
            bundle.movies,
            top_n=None,
        )
        recommendations_all = _serialize(recs)

    _save_cache(cache_path, recommendations_all)
    return recommendations_all


def _filter_search(recs: list[dict], query: str) -> list[dict]:
    if not query:
        return recs
    q = query.lower()
    filtered = []
    for r in recs:
        title = (r.get("metadata") or {}).get("title") or r.get("title") or ""
        mid = str(r.get("movieId", ""))
        if q in title.lower() or q in mid.lower():
            filtered.append(r)
    return filtered


@app.route("/", methods=["GET", "POST"])
def index():
    bundle = get_recommender_bundle()
    ready = bundle is not None
    recommendations = []
    recommendations_all = []
    error = None

    selected = request.form.get("algorithm", "hybrid")
    user_id = request.form.get("user_id", web_config.default_user_id)
    search_query = request.form.get("search", "").strip()
    try:
        page = max(1, int(request.form.get("page", 1)))
    except ValueError:
        page = 1
    per_page = 10
    total_pages = 1
    total_results = 0

    if request.method == "POST":
        if not ready:
            error = "Dataset not found. Please place movies.csv and ratings.csv into data/raw."
        else:
            try:
                user = int(user_id)
                recommendations_all = _build_recommendations(bundle, selected, user, page)
                recommendations_all = _filter_search(recommendations_all, search_query)

            except Exception as exc:
                error = str(exc)

    total_results = len(recommendations_all)
    if total_results:
        total_pages = max(1, math.ceil(total_results / per_page))
        page = min(page, total_pages)
        start = (page - 1) * per_page
        end = start + per_page
        recommendations = recommendations_all[start:end]
    else:
        page = 1
        total_pages = 1

    return render_template(
        "index.html",
        ready=ready,
        recommendations=recommendations,
        error=error,
        selected_algorithm=selected,
        default_user=user_id,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_results=total_results,
        search_query=search_query,
    )

@app.route("/api/users")
def api_users():
    bundle = get_recommender_bundle()
    if bundle is None:
        return jsonify([])

    user_ids = bundle.ratings["userId"].unique().tolist()
    user_ids = sorted(user_ids)
    return jsonify(user_ids)


@app.route("/api/recommendations")
def api_recommendations():
    bundle = get_recommender_bundle()
    if bundle is None:
        return jsonify({"error": "Dataset not found. Please place movies.csv and ratings.csv into data/raw."}), 400

    selected = request.args.get("algorithm", "hybrid")
    try:
        user = int(request.args.get("user_id", web_config.default_user_id))
    except Exception:
        return jsonify({"error": "Invalid user_id"}), 400

    try:
        page = max(1, int(request.args.get("page", 1)))
    except Exception:
        page = 1
    search_query = request.args.get("search", "").strip()

    per_page = 10
    try:
        recs_all = _build_recommendations(bundle, selected, user, page)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    recs_all = _filter_search(recs_all, search_query)

    total_results = len(recs_all)
    total_pages = max(1, math.ceil(total_results / per_page)) if total_results else 1
    page = min(page, total_pages)
    start = (page - 1) * per_page
    end = start + per_page
    data = recs_all[start:end]

    return jsonify({
        "algorithm": selected,
        "user_id": user,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "total_results": total_results,
        "data": data,
        "search": search_query,
    })


if __name__ == "__main__":
    app.run(debug=True)
