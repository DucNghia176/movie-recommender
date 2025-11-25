# 🎬 Movie Recommendation System  
### Hybrid Collaborative Filtering + Matrix Factorization (SVD-like)

Dự án xây dựng hệ thống **gợi ý phim** sử dụng thuật toán:
- Collaborative Filtering (User-Based & Item-Based)
- Matrix Factorization (SVD-like)
- Hybrid Recommendation (kết hợp CF + MF)
- Flask Web UI để nhập UserID và xem danh sách phim được gợi ý

---

## 📁 Cấu trúc thư mục
movie-recommender/
│
├── data/
│ ├── raw/
│ │ ├── movies.csv
│ │ └── ratings.csv
│ └── processed/
│ ├── movies_processed.csv
│ └── ratings_processed.csv
│
├── src/
│ ├── collaborative_filtering.py
│ ├── data_preprocessing.py
│ ├── hybrid_model.py
│ ├── matrix_factorization.py
│ └── init.py
│
├── web_app/
│ ├── app.py
│ ├── utils.py
│ ├── static/
│ │ ├── css/style.css
│ │ └── js/main.js
│ └── templates/index.html
│
├── config.py
├── requirements.txt
└── README.md


## 🚀 **1. Cài đặt môi trường**

### Bước 1 — Tạo môi trường ảo
```cmd
python -m venv .venv

### Bước 2 — Kích hoạt môi trường
.venv\Scripts\activate

Bước 3 — Cài đặt thư viện
pip install -r requirements.txt


2. Chuẩn bị dữ liệu
Tải dataset từ Kaggle:
🔗 https://www.kaggle.com/datasets/parasharmanas/movie-recommendation-system

Giải nén và đặt 2 file sau vào đúng vị trí:
data/raw/movies.csv
data/raw/ratings.csv

3. Chạy ứng dụng web
python web_app/app.py
