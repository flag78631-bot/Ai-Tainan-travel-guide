import sqlite3
import random
from datetime import date
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attraction_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attraction_id INTEGER NOT NULL,
            opening_hours TEXT,
            address TEXT,
            ticket_info TEXT,
            official_url TEXT,
            tips TEXT,
            FOREIGN KEY (attraction_id) REFERENCES attractions(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attraction_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attraction_id INTEGER NOT NULL,
            event_name TEXT NOT NULL,
            event_date TEXT,
            event_description TEXT,
            FOREIGN KEY (attraction_id) REFERENCES attractions(id)
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


# 讀取單筆資料（連同關聯的詳細資訊與活動）
@app.route("/attractions/<int:id>", methods=["GET"])
def search_attractions(id):
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 先查主資料，確認景點是否存在
    cursor.execute(
        "SELECT id, name, district, category, image_url, description, created_at FROM attractions WHERE id=?",
        (id,),
    )
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400

    attraction = {
        "id": result[0],
        "name": result[1],
        "district": result[2],
        "category": result[3],
        "image_url": result[4],
        "description": result[5],
        "created_at": result[6],
    }

    # 查 attraction_details（1對1，用 fetchone）
    cursor.execute(
        "SELECT opening_hours, address, ticket_info, official_url, tips FROM attraction_details WHERE attraction_id=?",
        (id,),
    )
    detail_row = cursor.fetchone()
    details = None
    if detail_row:
        details = {
            "opening_hours": detail_row[0],
            "address": detail_row[1],
            "ticket_info": detail_row[2],
            "official_url": detail_row[3],
            "tips": detail_row[4],
        }

    # 查 attraction_events（1對多，用 fetchall）
    cursor.execute(
        "SELECT event_name, event_date, event_description FROM attraction_events WHERE attraction_id=?",
        (id,),
    )
    event_rows = cursor.fetchall()
    events = []
    for row in event_rows:
        events.append(
            {
                "event_name": row[0],
                "event_date": row[1],
                "event_description": row[2],
            }
        )

    conn.close()

    return (
        jsonify(
            {
                "message": "ok",
                "attraction": attraction,
                "details": details,
                "events": events,
            }
        ),
        200,
    )


# 讀取資料(名字)
@app.route("/attractions/<string:name>")
def find_name(name):
    # 連線資料庫
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 確認更新產品是否存在(id是否存在)
    cursor.execute(
        "SELECT id, name, district, category, image_url, description, created_at FROM attractions WHERE name=?",
        (name,),
    )
    # fetchone():找到第一筆符合的資料
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "景點名稱不存在，請使用其他id"}), 400
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


# 新增景點詳細資訊
@app.route("/attractions/<int:id>/details", methods=["POST"])
def add_attraction_details(id):
    try:
        data = request.get_json(force=False)
        if data is None:
            raise ValueError
    except Exception:
        return jsonify({"error": "請傳送正確的json格式"}), 400

    opening_hours = data.get("opening_hours")
    address = data.get("address")
    ticket_info = data.get("ticket_info")
    official_url = data.get("official_url")
    tips = data.get("tips")

    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 確認景點是否存在
    cursor.execute("SELECT id FROM attractions WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400

    # 確認是否已經有詳細資訊（1對1，避免重複新增）
    cursor.execute("SELECT id FROM attraction_details WHERE attraction_id=?", (id,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "這個景點已經有詳細資訊了，請改用PUT/PATCH更新"}), 400

    cursor.execute(
        """INSERT INTO attraction_details
           (attraction_id, opening_hours, address, ticket_info, official_url, tips)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (id, opening_hours, address, ticket_info, official_url, tips),
    )
    conn.commit()
    detail_id = cursor.lastrowid
    conn.close()

    return (
        jsonify(
            {
                "message": "新增成功",
                "details": {
                    "id": detail_id,
                    "attraction_id": id,
                    "opening_hours": opening_hours,
                    "address": address,
                    "ticket_info": ticket_info,
                    "official_url": official_url,
                    "tips": tips,
                },
            }
        ),
        200,
    )


# 讀取單一景點的詳細資訊
@app.route("/attractions/<int:id>/details", methods=["GET"])
def get_attraction_details(id):
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM attractions WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400

    cursor.execute(
        "SELECT id, opening_hours, address, ticket_info, official_url, tips FROM attraction_details WHERE attraction_id=?",
        (id,),
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({"error": "這個景點還沒有詳細資訊"}), 400

    return (
        jsonify(
            {
                "message": "ok",
                "details": {
                    "id": result[0],
                    "attraction_id": id,
                    "opening_hours": result[1],
                    "address": result[2],
                    "ticket_info": result[3],
                    "official_url": result[4],
                    "tips": result[5],
                },
            }
        ),
        200,
    )


# 修改景點詳細資訊(整筆覆蓋)
@app.route("/attractions/<int:id>/details", methods=["PUT"])
def update_attraction_details(id):
    try:
        data = request.get_json(force=False)
        if data is None:
            raise ValueError
    except Exception:
        return jsonify({"error": "請傳送正確的json格式"}), 400

    opening_hours = data.get("opening_hours")
    address = data.get("address")
    ticket_info = data.get("ticket_info")
    official_url = data.get("official_url")
    tips = data.get("tips")

    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM attraction_details WHERE attraction_id=?", (id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "這個景點還沒有詳細資訊，請先用POST新增"}), 400

    cursor.execute(
        """UPDATE attraction_details
           SET opening_hours=?, address=?, ticket_info=?, official_url=?, tips=?
           WHERE attraction_id=?""",
        (opening_hours, address, ticket_info, official_url, tips, id),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "更新成功",
                "details": {
                    "id": result[0],
                    "attraction_id": id,
                    "opening_hours": opening_hours,
                    "address": address,
                    "ticket_info": ticket_info,
                    "official_url": official_url,
                    "tips": tips,
                },
            }
        ),
        200,
    )


# 修改景點詳細資訊(部分欄位)
@app.route("/attractions/<int:id>/details", methods=["PATCH"])
def change_attraction_details(id):
    try:
        data = request.get_json(force=False)
        if data is None:
            raise ValueError
    except Exception:
        return jsonify({"error": "請傳送正確的json格式"}), 400

    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, opening_hours, address, ticket_info, official_url, tips FROM attraction_details WHERE attraction_id=?",
        (id,),
    )
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "這個景點還沒有詳細資訊，請先用POST新增"}), 400

    final_opening_hours = data.get("opening_hours", result[1])
    final_address = data.get("address", result[2])
    final_ticket_info = data.get("ticket_info", result[3])
    final_official_url = data.get("official_url", result[4])
    final_tips = data.get("tips", result[5])

    cursor.execute(
        """UPDATE attraction_details
           SET opening_hours=?, address=?, ticket_info=?, official_url=?, tips=?
           WHERE attraction_id=?""",
        (
            final_opening_hours,
            final_address,
            final_ticket_info,
            final_official_url,
            final_tips,
            id,
        ),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "更新成功",
                "details": {
                    "id": result[0],
                    "attraction_id": id,
                    "opening_hours": final_opening_hours,
                    "address": final_address,
                    "ticket_info": final_ticket_info,
                    "official_url": final_official_url,
                    "tips": final_tips,
                },
            }
        ),
        200,
    )


# 刪除景點詳細資訊
@app.route("/attractions/<int:id>/details", methods=["DELETE"])
def delete_attraction_details(id):
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, opening_hours, address, ticket_info, official_url, tips FROM attraction_details WHERE attraction_id=?",
        (id,),
    )
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "這個景點還沒有詳細資訊"}), 400

    cursor.execute("DELETE FROM attraction_details WHERE attraction_id=?", (id,))
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "刪除成功",
                "details": {
                    "id": result[0],
                    "attraction_id": id,
                    "opening_hours": result[1],
                    "address": result[2],
                    "ticket_info": result[3],
                    "official_url": result[4],
                    "tips": result[5],
                },
            }
        ),
        200,
    )


# 新增景點活動
@app.route("/attractions/<int:id>/events", methods=["POST"])
def add_attraction_event(id):
    try:
        data = request.get_json(force=False)
        if data is None:
            raise ValueError
    except Exception:
        return jsonify({"error": "請傳送正確的json格式"}), 400

    event_name = data.get("event_name")
    event_date = data.get("event_date")
    event_description = data.get("event_description")

    if not event_name:
        return jsonify({"error": "請傳送完整的活動資訊(event_name必填)"}), 400
    if not isinstance(event_name, str):
        return jsonify({"error": "活動名稱必須是文字格式"}), 400

    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    # 確認景點是否存在
    cursor.execute("SELECT id FROM attractions WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400

    cursor.execute(
        """INSERT INTO attraction_events
           (attraction_id, event_name, event_date, event_description)
           VALUES (?, ?, ?, ?)""",
        (id, event_name, event_date, event_description),
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()

    return (
        jsonify(
            {
                "message": "新增成功",
                "event": {
                    "id": event_id,
                    "attraction_id": id,
                    "event_name": event_name,
                    "event_date": event_date,
                    "event_description": event_description,
                },
            }
        ),
        200,
    )


# 讀取單一景點底下的所有活動
@app.route("/attractions/<int:id>/events", methods=["GET"])
def get_attraction_events(id):
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM attractions WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "景點id不存在，請使用其他id"}), 400

    cursor.execute(
        "SELECT id, event_name, event_date, event_description FROM attraction_events WHERE attraction_id=?",
        (id,),
    )
    rows = cursor.fetchall()
    conn.close()

    events = [
        {
            "id": row[0],
            "attraction_id": id,
            "event_name": row[1],
            "event_date": row[2],
            "event_description": row[3],
        }
        for row in rows
    ]

    return jsonify({"message": "ok", "events": events}), 200


# 修改單一活動(整筆覆蓋)
@app.route("/attractions/<int:id>/events/<int:event_id>", methods=["PUT"])
def update_attraction_event(id, event_id):
    try:
        data = request.get_json(force=False)
        if data is None:
            raise ValueError
    except Exception:
        return jsonify({"error": "請傳送正確的json格式"}), 400

    event_name = data.get("event_name")
    event_date = data.get("event_date")
    event_description = data.get("event_description")

    if not event_name:
        return jsonify({"error": "請傳送完整的活動資訊(event_name必填)"}), 400
    if not isinstance(event_name, str):
        return jsonify({"error": "活動名稱必須是文字格式"}), 400

    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM attraction_events WHERE id=? AND attraction_id=?",
        (event_id, id),
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "活動不存在，請確認id"}), 400

    cursor.execute(
        """UPDATE attraction_events
           SET event_name=?, event_date=?, event_description=?
           WHERE id=? AND attraction_id=?""",
        (event_name, event_date, event_description, event_id, id),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "更新成功",
                "event": {
                    "id": event_id,
                    "attraction_id": id,
                    "event_name": event_name,
                    "event_date": event_date,
                    "event_description": event_description,
                },
            }
        ),
        200,
    )


# 修改單一活動(部分欄位)
@app.route("/attractions/<int:id>/events/<int:event_id>", methods=["PATCH"])
def change_attraction_event(id, event_id):
    try:
        data = request.get_json(force=False)
        if data is None:
            raise ValueError
    except Exception:
        return jsonify({"error": "請傳送正確的json格式"}), 400

    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, event_name, event_date, event_description FROM attraction_events WHERE id=? AND attraction_id=?",
        (event_id, id),
    )
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "活動不存在，請確認id"}), 400

    event_name = data.get("event_name")
    if event_name is not None and not isinstance(event_name, str):
        conn.close()
        return jsonify({"error": "活動名稱必須是文字格式"}), 400

    final_event_name = event_name if event_name is not None else result[1]
    final_event_date = data.get("event_date", result[2])
    final_event_description = data.get("event_description", result[3])

    cursor.execute(
        """UPDATE attraction_events
           SET event_name=?, event_date=?, event_description=?
           WHERE id=? AND attraction_id=?""",
        (final_event_name, final_event_date, final_event_description, event_id, id),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "更新成功",
                "event": {
                    "id": event_id,
                    "attraction_id": id,
                    "event_name": final_event_name,
                    "event_date": final_event_date,
                    "event_description": final_event_description,
                },
            }
        ),
        200,
    )


# 刪除單一活動
@app.route("/attractions/<int:id>/events/<int:event_id>", methods=["DELETE"])
def delete_attraction_event(id, event_id):
    conn = sqlite3.connect("attractions.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, event_name, event_date, event_description FROM attraction_events WHERE id=? AND attraction_id=?",
        (event_id, id),
    )
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "活動不存在，請確認id"}), 400

    cursor.execute(
        "DELETE FROM attraction_events WHERE id=? AND attraction_id=?", (event_id, id)
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": "刪除成功",
                "event": {
                    "id": result[0],
                    "attraction_id": id,
                    "event_name": result[1],
                    "event_date": result[2],
                    "event_description": result[3],
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
