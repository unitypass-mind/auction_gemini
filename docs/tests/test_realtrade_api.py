# -*- coding: utf-8 -*-
"""
국토교통부 실거래가 API 직접 테스트
필터링 전 원본 데이터 확인
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import xml.etree.ElementTree as ET

API_KEY = "db3f01f6817893034b78a84ac2a45cfd0b0a1ff1cf3bd29856bfbf7e92c24351"
BASE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"

# 테스트 파라미터 (인천 연수구, 롯데캐슬, 110.76㎡)
LAWD_CD = "28177"  # 인천 연수구
TARGET_APT = "롯데캐슬"
TARGET_AREA = 110.76

# 최근 4개월 테스트
MONTHS = ["202602", "202601", "202512", "202511"]

print("=" * 80)
print("국토교통부 실거래가 API 직접 테스트")
print("=" * 80)
print(f"\n대상: 인천 연수구 {TARGET_APT} {TARGET_AREA}㎡")
print(f"LAWD_CD: {LAWD_CD}")
print("-" * 80)

for deal_ymd in MONTHS:
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
        res = requests.get(url, timeout=30)
        print(f"  HTTP Status: {res.status_code}")

        if res.status_code != 200:
            print(f"  Error: {res.text[:200]}")
            continue

        root = ET.fromstring(res.text)

        # 응답 코드 확인
        result_code = root.findtext('.//resultCode', 'N/A')
        result_msg = root.findtext('.//resultMsg', 'N/A')
        total_count = root.findtext('.//totalCount', '0')

        print(f"  Result Code: {result_code} - {result_msg}")
        print(f"  Total Count: {total_count}")

        # 전체 아이템 조회
        items = root.findall('.//item')
        print(f"  Items Found: {len(items)}")

        if len(items) == 0:
            print("  -> 데이터 없음")
            continue

        # 모든 아파트명 목록 출력 (중복 제거)
        apt_names = set()
        for item in items:
            apt_name = item.findtext('aptNm', '').strip()
            if apt_name:
                apt_names.add(apt_name)

        print(f"\n  📋 이 월의 전체 아파트 목록 ({len(apt_names)}개):")
        for apt in sorted(apt_names):
            print(f"     - {apt}")

        # 타겟 아파트 필터링 (부분 매칭)
        target_matches = []
        for item in items:
            apt_name = item.findtext('aptNm', '').strip()
            if TARGET_APT in apt_name or apt_name in TARGET_APT:
                target_matches.append(item)

        print(f"\n  🎯 '{TARGET_APT}' 매칭 결과: {len(target_matches)}건")

        if target_matches:
            print(f"\n  상세 매칭 내역:")
            for idx, item in enumerate(target_matches[:10], 1):  # 최대 10건만 표시
                apt_name = item.findtext('aptNm', '').strip()
                area = item.findtext('excluUseAr', '').strip()
                price = item.findtext('dealAmount', '').strip()
                deal_day = item.findtext('dealDay', '').strip()
                floor = item.findtext('floor', '').strip()

                area_float = float(area) if area else 0.0
                area_diff = abs(area_float - TARGET_AREA)

                match_icon = "✅" if area_diff <= 10 else "❌"

                print(f"     {match_icon} [{idx}] {apt_name}")
                print(f"        전용면적: {area}㎡ (차이: {area_diff:.2f}㎡)")
                print(f"        거래금액: {price}만원")
                print(f"        거래일: {deal_ymd[:4]}-{deal_ymd[4:6]}-{deal_day}")
                print(f"        층: {floor}층")

        # 면적 필터까지 적용
        area_matches = []
        for item in target_matches:
            area = item.findtext('excluUseAr', '').strip()
            if area:
                area_float = float(area)
                if abs(area_float - TARGET_AREA) <= 10:
                    area_matches.append(item)

        print(f"\n  ✨ 최종 매칭 (아파트명 + 면적±10㎡): {len(area_matches)}건")

        if area_matches:
            print(f"\n  🎉 성공! 실거래가 데이터 발견!")
            break

    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
