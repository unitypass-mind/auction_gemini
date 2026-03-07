"""
빠른 API 테스트 스크립트
"""
import requests
import json

api_url = "https://valueauction.co.kr/api/search"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://valueauction.co.kr/search",
    "Origin": "https://valueauction.co.kr"
}

# Test 1: gyungmae (court auction)
payload_gyungmae = {
    "auctionType": "gyungmae",
    "status": "낙찰",
    "limit": 5,
    "offset": 0,
    "order": "bidding_date",
    "direction": "desc",
    "category": {
        "residential": ["전체"],
        "commercial": [],
        "land": []
    },
    "priceRange": {
        "min_ask_price": {"min": 0, "max": None},
        "appraisal_price": {"min": 0, "max": None}
    },
    "areaRange": {
        "land_area": {"min": 0, "max": None},
        "building_area": {"min": 0, "max": None}
    },
    "addresses": {
        "pnu1": [],
        "pnu2": [],
        "pnu3": [],
        "address1": [],
        "address2": [],
        "address3": []
    },
    "all": False,
    "courts": [],
    "tags": {"mode": "exclude"}
}

print("=" * 60)
print("Test 1: gyungmae (court auction)")
print("=" * 60)

try:
    response = requests.post(api_url, json=payload_gyungmae, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Total: {data.get('estimateTotal')}")

        results = data.get('results', [])
        print(f"Results count: {len(results)}")

        if results:
            first = results[0]
            print("\nFirst item:")
            print(f"  Case: {first.get('case', {}).get('name')}")
            price = first.get('price', {})
            print(f"  Appraised: {price.get('appraised_price'):,}")
            print(f"  Selling: {price.get('selling_price'):,}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Exception: {e}")

print("\n" + "=" * 60)
print("Test 2: No auctionType (let's see default)")
print("=" * 60)

# Test 2: Without auctionType
payload_no_type = {
    "status": "낙찰",
    "limit": 5,
    "offset": 0,
    "order": "bidding_date",
    "direction": "desc",
    "category": {
        "residential": ["전체"],
        "commercial": [],
        "land": []
    },
    "priceRange": {
        "min_ask_price": {"min": 0, "max": None},
        "appraisal_price": {"min": 0, "max": None}
    },
    "areaRange": {
        "land_area": {"min": 0, "max": None},
        "building_area": {"min": 0, "max": None}
    },
    "addresses": {
        "pnu1": [],
        "pnu2": [],
        "pnu3": [],
        "address1": [],
        "address2": [],
        "address3": []
    },
    "all": False,
    "courts": [],
    "tags": {"mode": "exclude"}
}

try:
    response = requests.post(api_url, json=payload_no_type, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Total: {data.get('estimateTotal')}")

        results = data.get('results', [])
        print(f"Results count: {len(results)}")

        if results:
            first = results[0]
            print("\nFirst item:")
            print(f"  Case: {first.get('case', {}).get('name')}")
            price = first.get('price', {})
            print(f"  Appraised: {price.get('appraised_price'):,}")
            print(f"  Selling: {price.get('selling_price'):,}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Exception: {e}")
