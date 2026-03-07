# ⚡ 빠른 시작 가이드

## 🚀 서버 실행 (1분)

```bash
cd C:\Users\unity\auction_gemini
python main.py
```

접속: http://localhost:8000

---

## 📋 현재 상태 체크리스트

### ✅ 완료된 것
- [x] 데이터 2000건 생성
- [x] AI 모델 훈련 (R² 0.9982)
- [x] FastAPI 서버 구축
- [x] 웹 UI (담당법원 드롭다운)
- [x] 예측 API 작동

### ⚠️ 알려진 이슈
- [ ] 물건번호 검색 → 더미 데이터만 반환
- [ ] 간단 예측 → 기본 계산식(75%) 사용

---

## 🔧 다음 작업

### 옵션 1: 물건번호 검색 수정 (추천)
샘플 DB에서 실제 데이터 검색하도록 수정

### 옵션 2: 그대로 사용
더미 데이터로도 시연 가능

---

## 📞 빠른 명령어

```bash
# 서버 실행
python main.py

# 데이터 재생성
python collect_auction_data.py

# 모델 재훈련
python train_model_advanced.py

# 전체 파이프라인
python run_full_pipeline.py

# API 테스트
curl "http://localhost:8000/predict?start_price=300000000&bidders=10"
```

---

## 📁 중요 파일

- `PROJECT_SUMMARY.md` - 전체 요약
- `README_ADVANCED.md` - 상세 가이드
- `models/auction_model.pkl` - 훈련된 모델
- `data/auction_data.csv` - 샘플 데이터 2000건

---

## 🎯 성능

- **정확도**: R² 0.9982 (99.82%)
- **오차**: 평균 1,095만원 (3%)
- **응답**: < 100ms

---

상세 내용: `PROJECT_SUMMARY.md` 참고
