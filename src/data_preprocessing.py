# data_preprocessing.py
import pandas as pd
from config import data_config, model_config

MAX_RATINGS = 200_000

def load_datasets(cfg=data_config):
    movies = pd.read_csv(cfg.movies_file)
    ratings = pd.read_csv(cfg.ratings_file)

    # ⚡ GIẢM BỚT DỮ LIỆU RATING VỀ 1 TRIỆU DÒNG (RẤT QUAN TRỌNG)
    if len(ratings) > MAX_RATINGS:
        ratings = ratings.sample(MAX_RATINGS, random_state=42)

    return movies, ratings


def clean_data(movies, ratings):
    movies = movies.drop_duplicates(subset=["movieId"])
    ratings = ratings.dropna(subset=["userId", "movieId"])
    ratings = ratings[ratings["rating"] > 0]
    return movies, ratings


def filter_interactions(ratings, cfg=model_config):
    ucount = ratings["userId"].value_counts()
    icount = ratings["movieId"].value_counts()

    ratings = ratings[
        ratings["userId"].isin(ucount[ucount >= cfg.min_interactions_user].index)
        & ratings["movieId"].isin(icount[icount >= cfg.min_interactions_item].index)
    ]
    return ratings


def preprocess_pipeline():
    movies, ratings = load_datasets()
    movies, ratings = clean_data(movies, ratings)
    ratings = filter_interactions(ratings)

    # Lưu dữ liệu đã xử lý
    data_config.processed_dir.mkdir(parents=True, exist_ok=True)
    movies.to_csv(data_config.processed_dir / "movies_processed.csv", index=False)
    ratings.to_csv(data_config.processed_dir / "ratings_processed.csv", index=False)

    return movies, ratings
