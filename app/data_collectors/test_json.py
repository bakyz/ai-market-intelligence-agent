import json
import os
from app.config.settings import get_settings

settings = get_settings()

def test_json(file_name):
    path = os.path.join(settings.paths.RAW_DATA, file_name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"{file_name} is valid JSON with {len(data)} records")
    except Exception as e:
        print(f"{file_name} is invalid JSON! Error: {e}")

if __name__ == "__main__":
    test_json("reddit.json")
    test_json("hn.json")
