# -*- coding: utf-8 -*-
"""
송도 지역 아파트 검색
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import xml.etree.ElementTree as ET

API_KEY = "db3f01f6817893034b78a84ac2a45cfd0b0a1ff1cf3bd29856bfbf7e92c24351"
BASE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"

# 송도동의 법정동 코드는 28185 (인천 연수구 송도동)
LAWD_CODES = {
    "28177": "인천 연수구",
    "28185": "인천 연수구 송도동"
}

TARGET_AREA = 110.76

print("=" * 80)
print("송도 지역 '롯데' 아파트 검색")
print("=" * 80)

for lawd_cd, name in LAWD_CODES.items():
    print(f"\n\n[{name} - {lawd_cd}]")
    print("-" * 80)

    url = (
        f"{BASE_URL}"
        f"?serviceKey={API_KEY}"
        f"&LAWD_CD={lawd_cd}"
        f"&DEAL_YMD=202601"
        f"&numOfRows=100"
        f"&pageNo=1"
    )

    try:
        res = requests.get(url, timeout=30)
        if res.status_code != 200:
            print(f"Error: {res.status_code}")
            continue

        root = ET.fromstring(res.text)
        items = root.findall('.//item')

        print(f"총 {len(items)}건 조회")

        # 롯데 관련 아파트
        lotte_apts = []
        for item in items:
            apt_name = item.findtext('aptNm', '').strip()
            if '롯데' in apt_name or 'lotte' in apt_name.lower():
                lotte_apts.append(apt_name)

        lotte_unique = sorted(set(lotte_apts))

        if lotte_unique:
            print(f"\n🏢 '롯데' 포함 아파트 ({len(lotte_unique)}개):")
            for apt in lotte_unique:
                print(f"   - {apt}")

                # 해당 아파트의 면적별 거래 확인
                for item in items:
                    item_apt = item.findtext('aptNm', '').strip()
                    if item_apt == apt:
                        area = item.findtext('excluUseAr', '').strip()
                        price = item.findtext('dealAmount', '').strip()
                        area_float = float(area) if area else 0.0
                        area_diff = abs(area_float - TARGET_AREA)

                        if area_diff <= 15:  # ±15㎡
                            print(f"      → {area}㎡ ({price}만원) [차이: {area_diff:.2f}㎡]")
        else:
            print("   → '롯데' 포함 아파트 없음")

    except Exception as e:
        print(f"Exception: {e}")

print("\n" + "=" * 80)
print("완료")
print("=" * 80)
