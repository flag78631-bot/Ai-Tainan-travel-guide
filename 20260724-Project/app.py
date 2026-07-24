import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def init_db():
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attractions
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            district TEXT NOT NULL,
            category TEXT NOT NULL,
            image_url TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# 新增景點
@app.route("/attractions", methods=["POST"])
def add_attractions():
    try:
        data = request.get_json(force=False)
        if data is None:
            raise ValueError
    except Exception:
        return jsonify({"error": "請傳送正確的json格式"}), 400

    # 從資料中讀取產品資訊
    name = data.get("name")
    district = data.get("district")
    category = data.get("category")
    image_url = data.get("image_url")
    description = data.get("description")
    created_at = data.get("created_at")
    # 資料驗證
    if (
        not name
        or not district
        or not category
        or not image_url
        or not description
        or not created_at
    ):
        return jsonify({"error": "請傳送完整的景點資訊"}), 400
    if not isinstance(name, str):
        return jsonify({"error": "名稱必須是文字格式"}), 400
    if not isinstance(district, str):
        return jsonify({"error": "地區必須是文字格式"}), 400
    if not isinstance(category, str):
        return jsonify({"error": "類型必須是文字格式"}), 400
    if not isinstance(image_url, str):
        return jsonify({"error": "網址必須是文字格式"}), 400
    if not isinstance(description, str):
        return jsonify({"error": "簡介必須是文字格式"}), 400

    # 確認產品是否已經存在 (name, )參數右邊加上","
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM attractions WHERE name=?", (name,))
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    # 如果fetchone()沒有找到 ->if result為false
    if result:
        return jsonify({"error": "景點名稱已存在，請使用其他名稱"}), 400

    # 連線資料庫 寫入資料
    cursor.execute(
        "INSERT INTO attractions(name, district, category, image_url, description, created_at) VALUES(?, ?, ?, ?, ?, ?)",
        (name, district, category, image_url, description, created_at),
    )
    conn.commit()
    attractions_id = cursor.lastrowid
    conn.close()

    return (
        jsonify(
            {
                "message": "新增成功",
                "attractions": {
                    "id": attractions_id,
                    "name": name,
                    "district": district,
                    "category": category,
                    "image_url": image_url,
                    "description": description,
                    "created_at": created_at,
                },
            },
        ),
        200,
    )


# 讀取資料
@app.route("/attractions", methods=["GET"])
def get_attractions():
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attractions")
    # rows 長這個樣子{name:"xxx", price:10}不是json

    rows = cursor.fetchall()
    conn.close()
    # rows轉成陣列=>轉成json
    attractions = []
    for row in rows:
        attraction = {
            "id": row[0],
            "name": row[1],
            "district": row[2],
            "category": row[3],
            "image_url": row[4],
            "description": row[5],
            "created_at": row[6],
        }
        attractions.append(attraction)

    return jsonify({"message": "資料讀取成功", "attractions": attractions}), 200


@app.route("/test")
def test():
    return jsonify({"message": "sever is working"})


if __name__ == "__main__":
    init_db()
    print("SQLITE 資料庫已初始化")
    app.run(host="0.0.0.0", port=5000, debug=True)
