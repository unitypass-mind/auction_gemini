import requests
import json

response = requests.get('http://localhost:8000/auction?case_no=2025타경63180&site=고양지원')
d = response.json()

print('=== API 응답 구조 ===')
print('status:', d.get('status'))
print('message:', d.get('message'))

data = d.get('data', {})
info = data.get('auction_info', {})

print('\n=== auction_info 주요 키 ===')
for key in info.keys():
    if key != '원본데이터':
        print(f'  - {key}')

print('\n=== 원본데이터 확인 ===')
raw = info.get('원본데이터', {})
print('원본데이터 존재:', bool(raw))
if raw:
    print('원본데이터 타입:', type(raw).__name__)
    if isinstance(raw, dict):
        print('tags 필드 존재:', 'tags' in raw)
        tags = raw.get('tags', [])
        print('tags 값:', tags)
        print('tags 개수:', len(tags) if tags else 0)

        print('\nbadge 필드 존재:', 'badge' in raw)
        badge = raw.get('badge', {})
        if badge:
            print('badge.tags 존재:', 'tags' in badge)
            badge_tags = badge.get('tags', [])
            print('badge.tags 값:', badge_tags)
            print('badge.tags 개수:', len(badge_tags) if badge_tags else 0)

print('\n=== 실거래가 정보 ===')
print('실거래가:', data.get('market_price_formatted'))
