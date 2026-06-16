#!/usr/bin/env python3
"""
ULE Multilingual Demo - Natural Language in 9 Languages

Run: python examples/02_multilingual.py
"""

from ule import connect
from ule.ai import NaturalLanguageQuery

# Setup database
db = connect("multilingual.udb", create_if_missing=True)

# Create sample data
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT, age INTEGER, city TEXT)")
db.execute("INSERT INTO users VALUES (1, 'Ali', 25, 'Lahore')")
db.execute("INSERT INTO users VALUES (2, 'Sara', 30, 'Karachi')")
db.execute("INSERT INTO users VALUES (3, 'Ahmed', 28, 'Islamabad')")
db.execute("INSERT INTO users VALUES (4, 'Fatima', 24, 'Peshawar')")

nlq = NaturalLanguageQuery(db._conn)

print("=" * 60)
print("ULE Multilingual Demo - Natural Language in 9 Languages")
print("=" * 60)

# Define queries in different languages
queries = {
    "en": {
        "name": "English",
        "queries": [
            "show all users",
            "count all users",
            "show users older than 25",
        ]
    },
    "ur": {
        "name": "Urdu (اردو)",
        "queries": [
            "تمام صارفین دکھائیں",
            "صارفین کی تعداد دکھائیں",
            "25 سال سے بڑی عمر کے صارفین دکھائیں",
        ]
    },
    "zh": {
        "name": "Chinese (中文)",
        "queries": [
            "显示所有用户",
            "计算用户总数",
            "显示 25 岁以上的用户",
        ]
    },
    "es": {
        "name": "Spanish (Español)",
        "queries": [
            "mostrar todos los usuarios",
            "contar todos los usuarios",
            "mostrar usuarios mayores de 25 años",
        ]
    },
    "fr": {
        "name": "French (Français)",
        "queries": [
            "afficher tous les utilisateurs",
            "compter tous les utilisateurs",
            "afficher les utilisateurs de plus de 25 ans",
        ]
    },
    "ru": {
        "name": "Russian (Русский)",
        "queries": [
            "показать всех пользователей",
            "подсчитать всех пользователей",
            "показать пользователей старше 25 лет",
        ]
    },
    "ja": {
        "name": "Japanese (日本語)",
        "queries": [
            "すべてのユーザーを表示",
            "ユーザーの総数を数える",
            "25 歳以上のユーザーを表示",
        ]
    },
    "ko": {
        "name": "Korean (한국어)",
        "queries": [
            "모든 사용자 표시",
            "모든 사용자 수 계산",
            "25 세 이상 사용자 표시",
        ]
    },
    "pt": {
        "name": "Portuguese (Português)",
        "queries": [
            "mostrar todos os usuários",
            "contar todos os usuários",
            "mostrar usuários com mais de 25 anos",
        ]
    },
}

# Run queries for each language
for lang_code, lang_data in queries.items():
    print(f"\n{'=' * 60}")
    print(f"Language: {lang_data['name']}")
    print(f"{'=' * 60}")
    
    for query in lang_data['queries']:
        print(f"\n   Query: '{query}'")
        try:
            results = nlq.ask(query, language=lang_code)
            if isinstance(results, list):
                print(f"   Result: {len(results)} rows returned")
            else:
                print(f"   Result: {results}")
        except Exception as e:
            print(f"   Error: {e}")

db.close()

print("\n" + "=" * 60)
print("✓ Multilingual Demo Complete!")
print("=" * 60)
