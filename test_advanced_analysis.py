#!/usr/bin/env python3
"""고급 분석 API 테스트"""
import requests
import json

def test_advanced_analysis():
    url = "http://localhost:8000/auction"
    params = {"case_no": "2024타경578276"}

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

                # 리스크 분석
                risk = adv.get('risk_analysis', {})
                print(f"\n리스크 분석:")
                print(f"  - 점수: {risk.get('score')}")
                print(f"  - 레벨: {risk.get('level')}")
                print(f"  - 색상: {risk.get('color')}")
                print(f"  - 요인 수: {len(risk.get('factors', []))}개")

                for factor in risk.get('factors', []):
                    print(f"    * {factor.get('factor')}: {factor.get('level')} ({factor.get('impact')})")

                # 투자 시나리오
                scenarios = adv.get('scenarios', {})
                print(f"\n투자 시나리오: {len(scenarios)}개")
                for key, val in scenarios.items():
                    print(f"  - {key}:")
                    print(f"    비율: {val.get('ratio', 0):.2%}")
                    print(f"    가격: {val.get('price', 0):,}원")
                    print(f"    수익: {val.get('profit', 0):,}원")

                # AI 신뢰도
                ai_conf = adv.get('ai_confidence', {})
                print(f"\nAI 신뢰도:")
                print(f"  - 점수: {ai_conf.get('score')}")
                print(f"  - 별점: {ai_conf.get('stars')}")
                print(f"  - 훈련 샘플: {ai_conf.get('training_samples'):,}개")
                print(f"  - 평균 오차율: {ai_conf.get('avg_error_rate')}%")
                print(f"  - 모델 버전: {ai_conf.get('model_version')}")

                print("\n✓ 모든 고급 분석 데이터 정상 확인!")
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
    test_advanced_analysis()
