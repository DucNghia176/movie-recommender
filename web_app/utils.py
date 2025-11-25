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
from src.data_preprocessing import preprocess_pipeline
from src.matrix_factorization import MFRecommender
from src.hybrid_model import HybridRecommender

logger = logging.getLogger(__name__)


@dataclass
class RecommenderBundle:
    movies: pd.DataFrame
    ratings: pd.DataFrame
    user_cf: object     # bỏ kiểu cứng UserBasedCF để tránh lỗi
    item_cf: object
    svd: MFRecommender
    hybrid: HybridRecommender


def _prepare():
    try:
        movies, ratings = preprocess_pipeline()
    except Exception as exc:
        logger.warning("Dataset missing: %s", exc)
        return None

    # ====== CF QUÁ NẶNG → TẮT ĐỂ TRÁNH CRASH ======
    user_cf = None
    item_cf = None

    # ====== MF chạy tốt trên 300k dòng ======
    mf = MFRecommender().fit(ratings)

    # ====== Hybrid (chỉ MF vì CF = None) ======
    hybrid = HybridRecommender(
        user_cf=user_cf,
        mf=mf,
        w_cf=0.0,   # tắt CF hoàn toàn
        w_mf=1.0
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
    return bundle.movies["movieId"].tolist()[:limit]
