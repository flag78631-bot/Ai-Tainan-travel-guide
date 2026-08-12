import requests
from attraction_detail_data import attraction_detail_data

BASE_URL = "http://127.0.0.1:5000"


def seed():
    success = 0
    failed = 0

    for item in attraction_detail_data:
        attraction_id = item["attraction_id"]

        payload = {
            "opening_hours": item.get("opening_hours"),
            "address": item.get("address"),
            "ticket_info": item.get("ticket_info"),
            "official_url": item.get("official_url"),
            "tips": item.get("tips"),
        }

        try:
            response = requests.post(
                f"{BASE_URL}/attractions/{attraction_id}/details",
                json=payload,
                timeout=5,
            )

            if response.status_code == 200:
                print(f"✅ 景點 {attraction_id} 新增成功")
                success += 1
            else:
                print(
                    f"❌ 景點 {attraction_id} 失敗："
                    f"{response.status_code} {response.json()}"
                )
                failed += 1

        except Exception as e:
            print(f"❌ 景點 {attraction_id} 發生錯誤：{e}")
            failed += 1

    print("-" * 40)
    print(f"成功：{success}")
    print(f"失敗：{failed}")


if __name__ == "__main__":
    seed()
