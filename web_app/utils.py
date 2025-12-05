# utils.py
# ===== FIX IMPORT PATH =====
import sys, os
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "src"))
# ============================

import logging
from dataclasses import dataclass
from functools import lru_cache
import pandas as pd

from config import web_config
from src.collaborative_filtering import ItemBasedCF, UserBasedCF
from src.data_preprocessing import preprocess_pipeline
from src.hybrid_model import HybridRecommender
from src.matrix_factorization import MFRecommender

logger = logging.getLogger(__name__)


@dataclass
class RecommenderBundle:
    movies: pd.DataFrame
    ratings: pd.DataFrame
    user_cf: object     # không ép kiểu cứng để tránh lỗi import vòng lặp
    item_cf: object
    svd: MFRecommender
    hybrid: HybridRecommender


def _prepare():
    try:
        movies, ratings = preprocess_pipeline()
    except Exception as exc:
        logger.warning("Dataset missing: %s", exc)
        return None

    user_cf = None
    item_cf = None
    try:
        user_cf = UserBasedCF().fit(ratings)
        item_cf = ItemBasedCF().fit(ratings)
    except Exception as exc:
        logger.warning("CF initialization failed: %s", exc)

    mf = MFRecommender().fit(ratings)

    hybrid = HybridRecommender(
        user_cf=user_cf,
        mf=mf,
        w_cf=0.5 if user_cf is not None else 0.0,
        w_mf=0.5 if user_cf is not None else 1.0,
    )

    return RecommenderBundle(
        movies=movies,
        ratings=ratings,
        user_cf=user_cf,
        item_cf=item_cf,
        svd=mf,
        hybrid=hybrid,
    )


@lru_cache(maxsize=1)
def get_recommender_bundle():
    return _prepare()


def candidate_items(bundle: RecommenderBundle, limit=500):
    items = bundle.movies["movieId"].tolist()
    if limit is None:
        return items
    return items[:limit]
