#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""입찰 전략 추천 기능 테스트"""
import sys
import requests
import json

# UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_bidding_strategy():
    url = "http://localhost:8000/auction"
    params = {"case_no": "2024타경579705"}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get('success'):
            print("✓ API 호출 성공")
            result = data.get('data', {})

            # 고급 분석 데이터 확인
            adv = result.get('advanced_analysis', {})
            if adv:
                print("✓ 고급 분석 데이터 존재")

                # 입찰 전략 확인
                strategy = adv.get('bidding_strategy', {})
                if strategy:
                    print("\n" + "="*60)
                    print("📊 입찰 전략 추천")
                    print("="*60)
                    print(f"현재 회차: {strategy.get('current_round')}회")
                    print(f"현재 최저입찰가: {strategy.get('current_minimum', 0):,}원")
                    print(f"AI 예측가: {strategy.get('predicted_price', 0):,}원")
                    print(f"추천 타입: {strategy.get('recommendation')}")

                    if strategy.get('wait_until_round'):
                        print(f"대기 권장 회차: {strategy.get('wait_until_round')}회")
                        print(f"예상 절감액: {strategy.get('potential_savings', 0):,}원")

                    print(f"\n💡 메시지: {strategy.get('message')}")
                    print("="*60)

                    print("\n✓ 입찰 전략 기능 정상 작동!")
                else:
                    print("✗ 입찰 전략 데이터 없음")
            else:
                print("✗ 고급 분석 데이터 없음")
        else:
            print("✗ API 호출 실패")
            print(f"메시지: {data.get('message')}")

    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bidding_strategy()
