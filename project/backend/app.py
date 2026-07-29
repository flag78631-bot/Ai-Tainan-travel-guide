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


# 讀取單筆資料
@app.route("/attractions/<int:id>", methods=["GET"])
def search_attractions(id):
    # 連線資料庫
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 確認更新產品是否存在(id是否存在)
    cursor.execute(
        "SELECT id, name, district, category, image_url, description, created_at FROM attractions WHERE id=?",
        (id,),
    )
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "ok",
                "attraction": {
                    "id": result[0],
                    "name": result[1],
                    "district": result[2],
                    "category": result[3],
                    "image_url": result[4],
                    "description": result[5],
                    "created_at": result[6],
                },
            }
        ),
        200,
    )


# 修改資料
@app.route("/attractions/<int:id>", methods=["PUT"])
def update_attractions(id):
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

    # 連線資料庫
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 確認更新產品是否存在(id是否存在)
    cursor.execute("SELECT id FROM attractions WHERE id=?", (id,))
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400
    # 確認名稱是否存在
    cursor.execute(
        "SELECT name FROM attractions WHERE name=? AND id!=?",
        (
            name,
            id,
        ),
    )
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    if result:
        conn.close()
        return jsonify({"error": "景點名稱已存在，請使用其他名稱"}), 400
    # 執行更新
    cursor.execute(
        "UPDATE attractions SET name=?, district=?, category=?, image_url=?, description=?, created_at=? WHERE id=?",
        (name, district, category, image_url, description, created_at, id),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "更新成功",
                "attractions": {
                    "id": id,
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


# 修改資料(部分)
@app.route("/attractions/<int:id>", methods=["PATCH"])
def change_attractions(id):
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
    if name is not None and not isinstance(name, str):
        return jsonify({"error": "名稱必須是文字格式"}), 400
    if district is not None and not isinstance(district, str):
        return jsonify({"error": "地區必須是文字格式"}), 400
    if category is not None and not isinstance(category, str):
        return jsonify({"error": "類型必須是文字格式"}), 400
    if image_url is not None and not isinstance(image_url, str):
        return jsonify({"error": "網址必須是文字格式"}), 400
    if description is not None and not isinstance(description, str):
        return jsonify({"error": "簡介必須是文字格式"}), 400

    # 連線資料庫
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 確認更新產品是否存在(id是否存在)
    cursor.execute(
        "SELECT id, name, district, category, image_url, description, created_at FROM attractions WHERE id=?",
        (id,),
    )
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400
    final_name = name if name is not None else result[1]
    final_district = district if district is not None else result[2]
    final_category = category if category is not None else result[3]
    final_image_url = image_url if image_url is not None else result[4]
    final_description = description if description is not None else result[5]
    # 確認名稱是否存在
    cursor.execute(
        "SELECT name FROM attractions WHERE name=? AND id!=?",
        (
            final_name,
            id,
        ),
    )
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    if result:
        conn.close()
        return jsonify({"error": "景點名稱已存在，請使用其他名稱"}), 400

    # 執行更新
    cursor.execute(
        "UPDATE attractions SET name=?, district=?, category=?, image_url=?, description=?, created_at=? WHERE id=?",
        (
            final_name,
            final_district,
            final_category,
            final_image_url,
            final_description,
            created_at,
            id,
        ),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "更新成功",
                "attractions": {
                    "id": id,
                    "name": final_name,
                    "district": final_district,
                    "category": final_category,
                    "image_url": final_image_url,
                    "description": final_description,
                    "created_at": created_at,
                },
            }
        ),
        200,
    )


# 刪除資料
@app.route("/attractions/<int:id>", methods={"DELETE"})
def delete_attraction(id):
    # 連線資料庫
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 確認更新產品是否存在(id是否存在)
    cursor.execute(
        "SELECT id, name, district, category, image_url, description, created_at FROM attractions WHERE id=?",
        (id,),
    )
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400

    # 執行刪除
    cursor.execute("DELETE FROM attractions WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "刪除成功",
                "attractions": {
                    "id": result[0],
                    "name": result[1],
                    "district": result[2],
                    "category": result[3],
                    "image_url": result[4],
                    "description": result[5],
                    "created_at": result[6],
                },
            }
        ),
        200,
    )


@app.route("/test")
def test():
    return jsonify({"message": "sever is working"})


if __name__ == "__main__":
    init_db()
    print("SQLITE 資料庫已初始化")
    app.run(host="0.0.0.0", port=5000, debug=True)
