# config.py
from dataclasses import dataclass
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


@dataclass
class DataConfig:
    raw_dir: pathlib.Path = DATA_DIR / "raw"
    processed_dir: pathlib.Path = DATA_DIR / "processed"

    movies_file: pathlib.Path = None
    ratings_file: pathlib.Path = None

    def __post_init__(self):
        self.movies_file = self.raw_dir / "movies.csv"
        self.ratings_file = self.raw_dir / "ratings.csv"


@dataclass
class ModelConfig:
    user_based_neighbors: int = 25
    item_based_neighbors: int = 20
    min_interactions_user: int = 5
    min_interactions_item: int = 5

    latent_factors: int = 40
    learning_rate: float = 0.01
    reg: float = 0.02
    epochs: int = 10


@dataclass
class WebConfig:
    default_user_id: int = 1
    recommendations_limit: int = 10


data_config = DataConfig()
model_config = ModelConfig()
web_config = WebConfig()
