import requests

# ValueAuction API 직접 호출
url = "https://valueauction.co.kr/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://valueauction.co.kr/search",
    "Origin": "https://valueauction.co.kr"
}
params = {
    "page": 1,
    "size": 50,
    "sort": "recent",
    "tags": {"mode": "include", "values": []},
    "filters": {"status": [], "priceRange": []},
}

response = requests.post(url, json=params, headers=headers)
results = response.json().get("results", [])

# 2025타경63180 찾기
target_case = "2025타경63180"
found = None

for item in results:
    case_no = item.get('case', {}).get('name', '')
    if target_case in case_no:
        found = item
        break

if found:
    print(f"물건 발견: {found.get('case', {}).get('name')}")
    print(f"\ntags 필드 존재: {'tags' in found}")
    if 'tags' in found:
        print(f"tags 값: {found['tags']}")

    print(f"\nbadge 필드: {found.get('badge', {})}")
    print(f"\n모든 필드:")
    for key in found.keys():
        print(f"  - {key}")
else:
    print(f"{target_case} 물건을 찾지 못함")
    print(f"첫 번째 물건 구조:")
    if results:
        first = results[0]
        print(f"case: {first.get('case', {}).get('name')}")
        print(f"tags 존재: {'tags' in first}")
        if 'tags' in first:
            print(f"tags: {first['tags']}")
