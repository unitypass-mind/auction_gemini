# 드롭다운 선택 버그 수정 완료

## 문제 상황
사용자가 "타경 402" 검색 시:
- 드롭다운에서 **2번째 항목** (대전지방법원) 선택
- 그러나 **1번째 항목** (목포지원) 결과가 표시됨

## 원인
`selectCaseNumber()` 함수가 사건번호 문자열만 받아서, 어떤 법원의 물건을 선택했는지 구분할 수 없었음.

```javascript
// 수정 전 (잘못된 코드)
onclick="selectCaseNumber('${item.case_no}')"  // 예: selectCaseNumber('2025타경402')

// 수정 후 (올바른 코드)
onclick="selectCaseNumber(${index})"  // 예: selectCaseNumber(1)
```

## 수정 내용

### 1. 드롭다운 클릭 이벤트 (static/index.html:831)
```javascript
// BEFORE: 사건번호 문자열만 전달
<div class="autocomplete-item" onclick="selectCaseNumber('${item.case_no}')">

// AFTER: 배열 인덱스 전달
<div class="autocomplete-item" onclick="selectCaseNumber(${index})">
```

### 2. selectCaseNumber() 함수 재작성 (static/index.html:854-887)
```javascript
function selectCaseNumber(index) {
    // 인덱스 유효성 검사
    if (typeof index !== 'number' || index < 0 || index >= searchResults.length) {
        console.error('Invalid index:', index);
        return;
    }

    // searchResults 배열에서 선택된 항목 가져오기
    const selectedItem = searchResults[index];
    const caseNo = selectedItem.case_no;

    // 연도와 번호 추출
    const match = caseNo.match(/(\d{4})타경(\d+)/);
    if (match) {
        document.getElementById('case_year').value = match[1];
        document.getElementById('case_no').value = match[2];

        // 선택된 법원 정보 로그
        console.log('선택된 물건:', caseNo, '법원:', selectedItem.site);
    }

    hideAutocomplete();
}
```

### 3. 키보드 네비게이션 수정 (static/index.html:905)
```javascript
// BEFORE
selectCaseNumber(searchResults[selectedIndex].case_no);

// AFTER
selectCaseNumber(selectedIndex);
```

## 테스트 방법

1. 전체분석 탭에서 사건번호 입력란에 "402" 입력
2. 드롭다운이 표시되면 **2번째 항목** (대전지방법원) 클릭
3. 브라우저 개발자도구 > Console에서 로그 확인:
   ```
   선택된 물건: 2025타경402 법원: 대전지방법원
   ```
4. 연도가 2025로, 사건번호가 402로 정확히 입력되었는지 확인

## 알려진 제한사항

**중복 사건번호 문제**:
- 같은 사건번호가 여러 법원에 존재할 경우, 백엔드 API는 첫 번째 매치만 반환함
- 예: "2025타경402"가 목포지원과 대전지방법원 모두에 있을 경우
- 드롭다운에서 대전지방법원을 선택해도, 백엔드는 목포지원 데이터를 반환할 수 있음

**향후 개선 방안**:
1. `/auction` API에 `site` 파라미터 추가
2. `get_auction_item()` 함수 수정하여 법원명으로도 필터링
3. UI에서 법원명을 더 명확하게 표시

## 수정 파일
- `static/index.html` (lines 831, 854-887, 905)

## 수정 날짜
2026-02-21
