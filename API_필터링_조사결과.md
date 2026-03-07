# ValueAuction API 낙찰 필터링 조사 결과

## 질문
**"밸류옥션 웹사이트에서는 낙찰된 물건만 검색되는데, API를 사용하면 왜 낙찰되지 않은 데이터까지 포함되나요?"**

## 조사 결과

### 1. API 필터 테스트
다음 파라미터들을 테스트했지만, **모두 작동하지 않음**:

#### 테스트한 필터들:
- `{"status": ["낙찰"]}` → **422 오류** (지원 안 함)
- `{"status": ["매각"]}` → **422 오류** (지원 안 함)
- `{"status": ["sold"]}` → **422 오류** (지원 안 함)
- `{"soldOnly": true}` → 응답 성공하지만 **필터링 안 됨** (13,267건 모두 반환)
- `{"isSold": true}` → 응답 성공하지만 **필터링 안 됨**
- `{"badge": {"sold": true}}` → 응답 성공하지만 **필터링 안 됨**
- `{"filters": {"sold": true}}` → 응답 성공하지만 **필터링 안 됨**
- `{"saleStatus": "낙찰"}` → 응답 성공하지만 **필터링 안 됨**
- `{"bidStatus": "completed"}` → 응답 성공하지만 **필터링 안 됨**
- `{"tags": {"mode": "include", "values": ["낙찰"]}}` → 응답 성공하지만 **필터링 안 됨**

### 2. 결론

**ValueAuction의 공개 `/api/search` 엔드포인트는 낙찰 상태 필터를 지원하지 않습니다.**

- API는 항상 모든 상태의 물건을 반환 (진행중, 유찰, 낙찰 등 전체 13,267건)
- 웹사이트는 다음 중 하나의 방법을 사용:
  1. **프론트엔드(JavaScript)에서 필터링**: API 응답을 받은 후 브라우저에서 필터링
  2. **다른 내부 API 사용**: 우리가 접근할 수 없는 별도의 엔드포인트 사용

### 3. 현재 솔루션 (이미 구현됨)

API 레벨에서 필터링이 불가능하므로, **코드 레벨에서 필터링**하는 방법을 사용:

```python
# valueauction_collector.py lines 217-238

# 1. API에서 모든 물건을 가져옴
histories = item.get("histories", [])

# 2. winning_info 확인
winning_info = None
for hist in reversed(histories):
    if hist.get("winning_info"):
        winning_info = hist["winning_info"]
        break

# 3. winning_info가 없으면 건너뜀 (낙찰되지 않은 물건)
if not winning_info:
    selling_price = int(price_data.get("selling_price", 0))
    if selling_price <= 0:
        stats["not_sold"] += 1
        logger.debug(f"낙찰 미완료 건너뜀: {case_name}")
        continue

# 4. winning_info가 있는 물건만 처리 (낙찰 완료)
selling_price = int(winning_info.get("winning_price", 0))
# ... 데이터 저장
```

### 4. 효율성 개선

현재 구현은 이미 다음 최적화가 적용되어 있습니다:

1. **중복 체크**: DB에 이미 있는 case_no는 건너뜀
2. **조기 종료**: 연속 20건이 중복/미낙찰이면 수집 중단
3. **날짜 필터**: `--days` 옵션으로 오래된 데이터 제외
4. **최소 감정가 필터**: API 레벨에서 감정가 필터링 가능 (작동함)

### 5. 테스트 스크립트

- `test_status_filter.py`: 기본 상태 필터 테스트
- `test_status_filter2.py`: 추가 필터 파라미터 테스트
- `test_sold_items.py`: 낙찰 완료 물건 찾기
- `test_api_structure.py`: API 응답 구조 확인

## 요약

**질문에 대한 답변**:
- ValueAuction API는 낙찰 상태 필터를 지원하지 않습니다
- 웹사이트는 프론트엔드에서 필터링하거나 다른 API를 사용합니다
- 우리는 API에서 모든 데이터를 받은 후 코드에서 `winning_info` 존재 여부로 필터링합니다
- 이것이 현재 가능한 **최선의 방법**입니다

**현재 솔루션의 장점**:
- 낙찰된 물건만 정확하게 수집
- 중복 및 오래된 데이터 자동 제외
- API 제약 사항을 우회하는 효율적인 구현
