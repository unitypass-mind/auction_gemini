"""
v2 모델 통합 테스트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from main import predict_price_advanced, model
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_v2_prediction():
    """v2 모델 예측 테스트"""

    print("=" * 60)
    print("v2 모델 통합 테스트")
    print("=" * 60)

    # 모델 로드 확인
    print(f"\n모델 로드 상태: {'✅ 성공' if model is not None else '❌ 실패'}")

    # 테스트 케이스 1: 기본 예측 (신규 변수 기본값)
    print("\n테스트 1: 기본 예측")
    print("-" * 60)

    start_price = 300_000_000
    property_type = "아파트"
    region = "서울"
    area = 85.0

    predicted = predict_price_advanced(
        start_price=start_price,
        property_type=property_type,
        region=region,
        area=area,
        auction_round=1,
        bidders=10
    )

    print(f"감정가: {start_price:,}원")
    print(f"물건종류: {property_type}")
    print(f"지역: {region}")
    print(f"면적: {area}㎡")
    print(f"예측 낙찰가: {predicted:,}원")
    print(f"낙찰률: {predicted/start_price*100:.2f}%")

    # 테스트 케이스 2: 신규 변수 포함 예측
    print("\n테스트 2: 신규 변수 포함 예측")
    print("-" * 60)

    predicted2 = predict_price_advanced(
        start_price=start_price,
        property_type=property_type,
        region=region,
        area=area,
        auction_round=1,
        bidders=10,
        bidders_actual=8,
        second_price=int(start_price * 0.7),
        is_hard=1,  # 권리분석 복잡
        tag_count=5,  # 권리사항 태그 5개
        share_floor=0,
        share_land=0,
        debt_ratio=0.3
    )

    print(f"감정가: {start_price:,}원")
    print(f"실제 입찰자: 8명")
    print(f"2등 입찰가: {int(start_price * 0.7):,}원")
    print(f"권리분석: 복잡")
    print(f"권리태그: 5개")
    print(f"청구금액비율: 30%")
    print(f"예측 낙찰가: {predicted2:,}원")
    print(f"낙찰률: {predicted2/start_price*100:.2f}%")

    # 비교
    print("\n결과 비교")
    print("-" * 60)
    print(f"기본 예측: {predicted:,}원")
    print(f"신규변수 예측: {predicted2:,}원")
    print(f"차이: {abs(predicted2 - predicted):,}원")

    print("\n✅ 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_v2_prediction()
