# -*- coding: utf-8 -*-
"""
포항시 북구 실거래가 API 직접 테스트
"""
import sys
import io
sys.stdout.reconfigure(encoding='utf-8')

import requests
import xml.etree.ElementTree as ET

API_KEY = "db3f01f6817893034b78a84ac2a45cfd0b0a1ff1cf3bd29856bfbf7e92c24351"
BASE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
LAWD_CD = "47113"  # 포항시 북구

print("=" * 80)
print(f"포항시 북구 (LAWD_CD={LAWD_CD}) 실거래가 조회")
print("=" * 80)

# 최근 3개월 데이터 조회
for deal_ymd in ["202602", "202601", "202512"]:
    print(f"\n[{deal_ymd}] 조회 중...")

    url = (
        f"{BASE_URL}"
        f"?serviceKey={API_KEY}"
        f"&LAWD_CD={LAWD_CD}"
        f"&DEAL_YMD={deal_ymd}"
        f"&numOfRows=100"
        f"&pageNo=1"
    )

    try:
        resp = requests.get(url, timeout=30)
        print(f"  HTTP Status: {resp.status_code}")

        if resp.status_code != 200:
            continue

        root = ET.fromstring(resp.text)
        result_code = root.findtext('.//resultCode', '')
        total_count = root.findtext('.//totalCount', '0')

        print(f"  Result Code: {result_code}")
        print(f"  Total Count: {total_count}")

        items = root.findall('.//item')
        print(f"  Items: {len(items)}건")

        if len(items) > 0:
            # 전체 아파트 목록
            apt_names = set()
            for item in items:
                apt_name = item.findtext('aptNm', '').strip()
                if apt_name:
                    apt_names.add(apt_name)

            print(f"\n  📋 아파트 목록 ({len(apt_names)}개):")
            for apt in sorted(apt_names):
                print(f"     - {apt}")

            # "폰토스" 포함 아파트 찾기
            pontos = [apt for apt in apt_names if '폰토스' in apt or 'pontos' in apt.lower()]
            if pontos:
                print(f"\n  🎯 '폰토스' 관련 아파트: {pontos}")
        else:
            print("  -> 데이터 없음")

    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "=" * 80)
print("완료")
print("=" * 80)
