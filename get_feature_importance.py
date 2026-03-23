import requests
import json
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = "https://auction-ai.kr/model/features"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    if data.get('success'):
        print(f"=== AI 모델 변수별 가중치 (총 {data['total_features']}개 특성) ===\n")

        print("=" * 80)
        print("상위 20개 주요 변수:")
        print("=" * 80)

        for i, feature in enumerate(data['top_20_features'], 1):
            bar = '█' * int(feature['importance_percent'] * 2)
            print(f"{i:2d}. {feature['feature_name']:30s} : {feature['importance_percent']:6.2f}% {bar}")

        print("\n" + "=" * 80)
        print("전체 변수 목록:")
        print("=" * 80)

        for i, feature in enumerate(data['features'], 1):
            bar = '█' * int(feature['importance_percent'] * 2)
            print(f"{i:2d}. {feature['feature_name']:30s} : {feature['importance_percent']:6.2f}% {bar}")

        # 카테고리별 집계
        print("\n" + "=" * 80)
        print("카테고리별 중요도 분석:")
        print("=" * 80)

        categories = {
            '감정가/가격': ['감정가', '최저입찰가', 'start_price'],
            '경매회차': ['경매회차', 'round', 'auction_round'],
            '입찰자수': ['입찰자수', 'bidders'],
            '물건종류': ['property_', '아파트', '다세대', '단독', '상가', '토지', '오피스텔'],
            '지역': ['region_', '서울', '경기', '인천', '부산', '대구', '광주', '대전'],
            '면적': ['면적', 'area'],
            '권리분석': ['권리', '복잡도', '태그'],
            '공유지분': ['공유지분'],
            '청구금액': ['청구금액']
        }

        category_importance = {}
        for cat_name, keywords in categories.items():
            total = 0
            count = 0
            for feature in data['features']:
                fname = feature['feature_name']
                if any(keyword in fname for keyword in keywords):
                    total += feature['importance_percent']
                    count += 1
            if count > 0:
                category_importance[cat_name] = {'total': total, 'count': count, 'avg': total/count}

        for cat_name in sorted(category_importance.keys(), key=lambda x: category_importance[x]['total'], reverse=True):
            cat_data = category_importance[cat_name]
            bar = '█' * int(cat_data['total'] / 5)
            print(f"{cat_name:15s} : 합계 {cat_data['total']:6.2f}% ({cat_data['count']:2d}개 변수) {bar}")

    else:
        print(f"Error: {data.get('message')}")
else:
    print(f"HTTP Error: {response.status_code}")
    print(response.text)
