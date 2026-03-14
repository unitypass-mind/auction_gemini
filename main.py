"""
AI 기반 경매 낙찰가 예측 시스템
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, HTTPException, Query, Request, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, EmailStr
import requests
from bs4 import BeautifulSoup
import joblib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import re
import pandas as pd
import numpy as np
import random
import json
import asyncio
import threading

from config import settings
from database import db, DB_PATH
from rate_limit import setup_rate_limiting, limiter
from error_handlers import (
    APIError, create_error_response, handle_validation_error,
    handle_not_found_error, handle_server_error, handle_external_api_error,
    handle_model_error, log_api_call
)
import auth
import notifications
import sqlite3
import hashlib
from time import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 예측 결과 캐싱 (메모리 기반, 1시간 유효)
prediction_cache = {}
CACHE_EXPIRY_SECONDS = 3600  # 1시간

def get_cache_key(*args, **kwargs) -> str:
    """캐시 키 생성 (모든 입력 파라미터 기반)"""
    cache_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(cache_str.encode()).hexdigest()

def get_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """캐시에서 데이터 조회"""
    if cache_key in prediction_cache:
        cached_data, cached_time = prediction_cache[cache_key]
        if time() - cached_time < CACHE_EXPIRY_SECONDS:
            logger.info(f"캐시 히트: {cache_key[:8]}...")
            return cached_data
        else:
            # 만료된 캐시 삭제
            del prediction_cache[cache_key]
    return None

def set_to_cache(cache_key: str, data: Dict[str, Any]):
    """캐시에 데이터 저장"""
    prediction_cache[cache_key] = (data, time())
    logger.info(f"캐시 저장: {cache_key[:8]}... (총 {len(prediction_cache)}개)")

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="법원 경매 물건의 낙찰가를 AI로 예측하는 시스템"
)

# 캐싱 미들웨어
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """브라우저 캐싱 헤더 추가"""
    response = await call_next(request)

    path = request.url.path

    # 정적 파일 (CSS, JS, 이미지 등) - 1년 캐싱
    if path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    # HTML 파일 - 5분 캐싱
    elif path == "/" or path.endswith(".html"):
        response.headers["Cache-Control"] = "public, max-age=300"
    # API 엔드포인트 - 캐싱 안함
    elif path.startswith("/predict") or path.startswith("/search") or path.startswith("/verify"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    # 헬스체크 - 캐싱 안함
    elif path == "/health":
        response.headers["Cache-Control"] = "no-cache"

    return response

# CORS 설정 (환경변수 기반)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # 환경변수에서 읽기
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 필요한 메소드만 허용
    allow_headers=["*"],
)

# GZip 압축 설정 (응답 크기 1KB 이상일 때 압축)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate Limiting 설정
setup_rate_limiting(app)

# Static 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# AI 모델 로드 (v3 모델 우선)
model = None
model_v3_path = Path("models/auction_model_v3.pkl")
model_v4_path = Path("models/auction_model_v4.pkl")

# 패턴 테이블 경로
pattern_property_round = None
pattern_region = None
pattern_complex = None
PATTERN_PROPERTY_ROUND_PATH = Path("models/pattern_property_round.pkl")
PATTERN_REGION_PATH = Path("models/pattern_region.pkl")
PATTERN_COMPLEX_PATH = Path("models/pattern_complex.pkl")
model_v2_path = Path("models/auction_model_v2.pkl")
model_v1_path = Path(settings.MODEL_PATH)
model_load_time = None

def load_model():
    """AI 모델을 로드하는 함수"""
    global model, model_load_time

    # v4 모델 먼저 시도
    if model_v4_path.exists():
        try:
            model = joblib.load(model_v4_path)
            model_load_time = datetime.now()
            logger.info(f"AI 모델 v4 로드 성공: {model_v4_path}")
            return True, "v4"
        except Exception as e:
            logger.error(f"AI 모델 v4 로드 실패: {e}")

    # v3 모델 시도
    if model_v3_path.exists():
        try:
            model = joblib.load(model_v3_path)
            model_load_time = datetime.now()
            logger.info(f"AI 모델 v3 로드 성공: {model_v3_path}")
            return True, "v3"
        except Exception as e:
            logger.error(f"AI 모델 v3 로드 실패: {e}")

    # v2 모델 먼저 시도
    if model_v2_path.exists():
        try:
            model = joblib.load(model_v2_path)
            model_load_time = datetime.now()
            logger.info(f"AI 모델 v2 로드 성공: {model_v2_path}")
            return True, "v2"
        except Exception as e:
            logger.error(f"AI 모델 v2 로드 실패: {e}")

    # v2가 없으면 v1 시도
    if model_v1_path.exists():
        try:
            model = joblib.load(model_v1_path)
            model_load_time = datetime.now()
            logger.info(f"AI 모델 v1 로드 성공: {model_v1_path}")
            return True, "v1"
        except Exception as e:
            logger.error(f"AI 모델 v1 로드 실패: {e}")

    logger.warning(f"AI 모델 파일이 없습니다")
    return False, None


def load_pattern_tables():
    """패턴 테이블을 로드하는 함수"""
    global pattern_property_round, pattern_region, pattern_complex

    try:
        if PATTERN_PROPERTY_ROUND_PATH.exists():
            pattern_property_round = joblib.load(PATTERN_PROPERTY_ROUND_PATH)
            logger.info(f"패턴 테이블 로드 성공: {len(pattern_property_round)}개 (물건×회차)")

        if PATTERN_REGION_PATH.exists():
            pattern_region = joblib.load(PATTERN_REGION_PATH)
            logger.info(f"패턴 테이블 로드 성공: {len(pattern_region)}개 (지역)")

        if PATTERN_COMPLEX_PATH.exists():
            pattern_complex = joblib.load(PATTERN_COMPLEX_PATH)
            logger.info(f"패턴 테이블 로드 성공: {len(pattern_complex)}개 (복합)")

        return True
    except Exception as e:
        logger.error(f"패턴 테이블 로드 실패: {e}")
        return False

# 초기 모델 로드
load_model()
load_pattern_tables()


# -----------------------------
# 유틸리티 함수
# -----------------------------
def clean_number(text: str) -> int:
    """
    숫자 문자열을 정수로 변환
    예: "300,000,000원" -> 300000000
    """
    try:
        cleaned = re.sub(r'[^\d]', '', text)
        return int(cleaned) if cleaned else 0
    except Exception as e:
        logger.error(f"숫자 변환 실패: {text}, 에러: {e}")
        return 0


def format_case_number(case_input: str) -> str:
    """
    사건번호 형식 변환 (유연한 입력 지원)

    입력 예시:
    - "2024타경579705" → "2024타경579705" (그대로 반환)
    - "202457970" → "2024타경57970" (숫자만 → 변환)
    - "2024타경00001" → "2024타경00001" (그대로)
    - "579705" → "2024타경579705" (연도 추가)
    """
    try:
        case_input = case_input.strip()

        # 이미 "타경" 또는 "타단" 등이 포함되어 있으면 그대로 반환
        if "타경" in case_input or "타단" in case_input or "타가" in case_input:
            logger.info(f"사건번호 형식 유지: {case_input}")
            return case_input

        # 숫자만 추출
        numbers = re.sub(r'[^\d]', '', case_input)

        if not numbers:
            logger.warning(f"유효한 숫자가 없음: {case_input}")
            return case_input

        # 연도 추출 또는 기본값 설정
        if len(numbers) >= 4:
            # 앞 4자리가 2000년대면 연도로 간주
            year_candidate = numbers[:4]
            if year_candidate.startswith('20'):
                year = year_candidate
                case_num = numbers[4:] if len(numbers) > 4 else "00001"
            else:
                # 연도가 아니면 현재 연도 사용
                year = "2024"
                case_num = numbers
        else:
            # 너무 짧으면 현재 연도 + 전체를 사건번호로
            year = "2024"
            case_num = numbers

        # 사건번호가 비어있으면 기본값
        if not case_num or case_num == "0":
            case_num = "00001"

        # 자릿수 그대로 유지 (불필요한 패딩 제거)
        result = f"{year}타경{case_num}"
        logger.info(f"사건번호 변환: {case_input} → {result}")
        return result

    except Exception as e:
        logger.error(f"사건번호 변환 실패: {case_input}, 에러: {e}")
        # 실패시 원본 반환
        return case_input


# -----------------------------
# ValueAuction API 실시간 검색
# -----------------------------
def get_auction_from_valueauction(case_no: str, site: str = None) -> Optional[Dict[str, Any]]:
    """
    ValueAuction API로 실시간 경매 정보 검색

    Args:
        case_no: 법원 사건번호 (예: "2025타경32075")
        site: 담당법원명 (선택, 중복 사건번호 구분용, 예: "대전지방법원")

    Returns:
        경매 물건 정보 딕셔너리 또는 None
    """
    try:
        logger.info(f"ValueAuction API 검색 시작: {case_no}" + (f", 법원: {site}" if site else ""))

        api_url = "https://valueauction.co.kr/api/search"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Content-Type": "application/json",
            "Referer": "https://valueauction.co.kr/",
            "Origin": "https://valueauction.co.kr"
        }

        # 정확한 사건번호로 직접 검색 (auctionType + case 파라미터 사용)
        payload = {
            "auctionType": "auction",
            "case": case_no
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.warning(f"ValueAuction API 오류: {response.status_code}")
            return None

        data = response.json()
        results = data.get('results', [])

        if not results:
            logger.warning(f"ValueAuction에서 사건번호를 찾을 수 없음: {case_no}")
            return None

        # 정확히 일치하는 사건번호 찾기 (site가 지정된 경우 site도 확인)
        matched_item = None
        for item in results:
            item_case_no = item.get('case', {}).get('name', '')
            item_site = item.get('case', {}).get('site', '')

            # 사건번호 일치 확인
            if item_case_no == case_no:
                # site가 지정되지 않았거나, site가 일치하면 선택
                if not site or site in item_site or item_site in site:
                    matched_item = item
                    logger.info(f"ValueAuction에서 사건번호 정확 일치: {case_no}, 법원: {item_site}")
                    break
                else:
                    # 사건번호는 같지만 다른 법원 - 로깅만 하고 계속 검색
                    logger.debug(f"사건번호 일치하지만 법원 불일치: {case_no} (요청: {site}, 검색결과: {item_site})")

        # 정확 일치 없으면 공백/특수문자 제거 후 비교
        if not matched_item:
            case_no_norm = re.sub(r'[^\d타경가단]', '', case_no)
            for item in results:
                item_case_no = item.get('case', {}).get('name', '')
                if re.sub(r'[^\d타경가단]', '', item_case_no) == case_no_norm:
                    matched_item = item
                    logger.info(f"ValueAuction 유사 일치: {item_case_no} ≈ {case_no}")
                    break

        if not matched_item:
            logger.warning(f"ValueAuction 매칭 실패: {case_no}, 검색된 사건: {[r.get('case', {}).get('name') for r in results[:3]]}")
            return None

        # 데이터 추출
        price_data = matched_item.get('price', {})
        badge_data = matched_item.get('badge', {})
        case_data = matched_item.get('case', {})

        appraisal_price = int(price_data.get('appraised_price', 0) or 0)
        raw_selling = price_data.get('selling_price', -1)
        selling_price = int(raw_selling) if raw_selling and raw_selling > 0 else None
        lowest_price = int(price_data.get('lowest_selling_price', 0) or 0)
        if lowest_price == 0:
            lowest_price = appraisal_price

        category = badge_data.get('category', '기타')
        # 건물 전용면적 우선, 없으면 badge.area
        area = float(badge_data.get('area_buildings', 0) or badge_data.get('area', 0) or 0.0)
        failure_count = int(badge_data.get('failure_count', 0))

        address = matched_item.get('address', '정보 없음')

        # 매각예정일 (Unix timestamp → YYYY-MM-DD)
        bidding_ts = matched_item.get('bidding_date', 0)
        if bidding_ts and bidding_ts > 0:
            from datetime import datetime as _dt
            try:
                auction_date_fmt = _dt.fromtimestamp(bidding_ts).strftime('%Y-%m-%d')
            except Exception:
                auction_date_fmt = ''
        else:
            auction_date_fmt = ''

        # 법원명
        court_name = case_data.get('site', 'ValueAuction')

        # 지역 추출
        region_map = {
            "서울": "서울", "경기": "경기", "인천": "인천", "부산": "부산",
            "대구": "대구", "대전": "대전", "광주": "광주", "울산": "울산"
        }
        region = "기타"
        for key in region_map:
            if key in address:
                region = region_map[key]
                break

        # 물건종류 매핑
        property_map = {
            "아파트": "아파트", "다세대": "다세대", "단독주택": "단독주택",
            "오피스텔": "오피스텔", "상가": "상가", "근린": "상가",
            "토지": "토지", "공장": "공장"
        }
        property_type = "기타"
        for key, value in property_map.items():
            if key in category:
                property_type = value
                break

        # 입찰자 수 (과거 낙찰 이력에서 추출)
        bidders_count = 1
        histories = matched_item.get('histories', [])
        for hist in reversed(histories):
            winning_info = hist.get('winning_info')
            if winning_info and winning_info.get('bidders_count'):
                bidders_count = int(winning_info['bidders_count'])
                break

        # ✅ 권리분석 정보 추출 (ValueAuction API)
        auction_data = matched_item.get('auction', {})
        claim_amount = int(auction_data.get('claim_amount', 0) or 0)
        has_share_floor = matched_item.get('has_share_floor', False)
        has_share_land = matched_item.get('has_share_land', False)
        notes = matched_item.get('notes', '')

        # 청구금액 비율 계산
        claim_ratio = (claim_amount / appraisal_price) if appraisal_price > 0 else 0

        # 권리관계 정보 정리
        rights_info = {
            "청구금액": claim_amount,
            "청구금액비율": round(claim_ratio, 4),
            "공유지분_건물": has_share_floor,
            "공유지분_토지": has_share_land,
            "권리분석_원문": notes[:500] if notes else ""  # 최대 500자
        }

        # 감정가 0이면 유효하지 않은 데이터
        if appraisal_price == 0:
            logger.warning(f"ValueAuction 감정가 0 - 유효하지 않은 데이터: {case_no}")
            return None

        logger.info(f"ValueAuction 데이터 추출 성공: {case_no}, 감정가={appraisal_price:,}원, 면적={area}㎡")

        note = f"법원 경매 실시간 데이터. 법원: {court_name}"
        if auction_date_fmt:
            note += f", 매각예정일: {auction_date_fmt}"

        return {
            "물건번호": case_data.get('id', 'VA-UNKNOWN'),
            "사건번호": case_no,
            "물건종류": property_type,
            "소재지": address,
            "감정가": f"{appraisal_price:,}원",
            "감정가_숫자": appraisal_price,
            "최저입찰가": lowest_price,
            "낙찰가": selling_price if selling_price else 0,
            "입찰자수": bidders_count,
            "면적": f"{area:.2f}㎡",
            "경매회차": failure_count + 1,
            "지역": region,
            "낙찰률": (selling_price / appraisal_price) if selling_price and appraisal_price > 0 else 0,
            "데이터소스": f"법원경매정보 ({court_name}) - 실시간",
            "note": note,
            "매각예정일": auction_date_fmt,
            "권리분석": rights_info,  # ✅ 권리분석 정보 추가
            "원본데이터": matched_item
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"ValueAuction API 요청 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"ValueAuction 검색 중 오류: {e}", exc_info=True)
        return None


# -----------------------------
# 법원 경매 사이트 크롤러 (Playwright)
# -----------------------------
def _parse_court_data(data: dict, case_no: str) -> Optional[Dict[str, Any]]:
    """
    법원 경매 API 응답을 표준 형식으로 변환.
    감정가가 0이면 None 반환 (데이터 없음으로 처리).
    """
    cs_bas_inf = data.get('dma_csBasInf', {})
    dspsl_list = data.get('dlt_dspslGdsDspslObjctLst', [])
    location_list = data.get('dlt_dstrtDemnLstprdDts', [])

    # 감정가 / 최저입찰가 / 용도코드 / 매각일 / 면적
    appraisal_price = 0
    lowest_price = 0
    auction_date = ''
    usage_code = ''
    area_m2 = 0.0
    full_address = ''
    bld_detail = ''

    if dspsl_list:
        first = dspsl_list[0]
        appraisal_price = int(first.get('aeeEvlAmt', 0) or 0)
        auction_date = first.get('dspslDxdyYmd', '')
        usage_code = first.get('auctnGdsUsgCd', '')
        # 최저입찰가: 1회차 공고 최저입찰가 우선
        lowest_price = int(first.get('fstPbancLwsDspslPrc', 0) or 0)
        if lowest_price == 0:
            lowest_price = appraisal_price

        # 면적: 법원 기본 API에는 없는 경우가 많으나 혹시 있으면 사용
        for field in ['bldAra', 'lndAra', 'totAra', 'pnstArea']:
            val = first.get(field, 0)
            if val and float(val) > 0:
                area_m2 = float(val)
                break

        # 주소: userSt(도로명 전체주소) 우선, 없으면 행정동 조합
        full_address = first.get('userSt', '').strip()
        bld_detail = first.get('bldDtlDts', '').strip()

    # 감정가 0이면 데이터 없음으로 처리
    if appraisal_price == 0:
        logger.warning(f"법원 응답에 감정가 없음 (빈 데이터): {case_no}")
        return None

    # 소재지 조합: userSt 없으면 행정동 조합
    if not full_address:
        address_parts = []
        # dspsl_list에서 행정동 추출 시도 (더 풍부한 필드 보유)
        src = dspsl_list[0] if dspsl_list else (location_list[0] if location_list else {})
        for field in ['adongSdNm', 'adongSggNm', 'adongEmdNm']:
            val = src.get(field, '')
            if val:
                address_parts.append(val)
        bld_nm = src.get('bldNm', '')
        if bld_nm:
            address_parts.append(bld_nm)
        full_address = ' '.join(address_parts) if address_parts else '정보 없음'

    # 동/호수 등 상세 정보 추가
    if bld_detail and bld_detail not in full_address:
        full_address = f"{full_address} {bld_detail}".strip()

    # 지역 추출 (행정동 필드 직접 참조, 더 정확)
    sd_nm = ''
    if dspsl_list:
        sd_nm = dspsl_list[0].get('adongSdNm', '')
    if not sd_nm and location_list:
        sd_nm = location_list[0].get('adongSdNm', '')

    region_map = {
        "서울": "서울", "경기": "경기", "인천": "인천", "부산": "부산",
        "대구": "대구", "대전": "대전", "광주": "광주", "울산": "울산",
        "세종": "기타", "강원": "기타", "충북": "기타", "충남": "기타",
        "전북": "기타", "전남": "기타", "경북": "기타", "경남": "기타",
        "제주": "기타"
    }
    region = "기타"
    for key, val in region_map.items():
        if key in sd_nm or key in full_address:
            region = val
            break

    # 물건종류 (용도코드 → 한국어)
    usage_map = {
        "01": "아파트", "02": "다세대", "03": "단독주택",
        "04": "오피스텔", "05": "상가", "06": "토지",
        "07": "공장", "08": "창고", "09": "기타"
    }
    property_type = usage_map.get(usage_code, "기타")

    # 청구금액
    clm_amt = int(cs_bas_inf.get('clmAmt', 0) or 0)

    # 법원명
    court_name = cs_bas_inf.get('cortOfcNm', '법원경매')

    # 매각예정일 형식 변환 (20260309 → 2026-03-09)
    if auction_date and len(auction_date) == 8:
        auction_date_fmt = f"{auction_date[:4]}-{auction_date[4:6]}-{auction_date[6:]}"
    else:
        auction_date_fmt = auction_date

    note = f"법원 경매 사이트 실시간 데이터. 법원: {court_name}"
    if clm_amt > 0:
        note += f", 청구금액: {clm_amt:,}원"
    if auction_date_fmt:
        note += f", 매각예정일: {auction_date_fmt}"

    return {
        "물건번호": cs_bas_inf.get('csNo', 'COURT-UNKNOWN'),
        "사건번호": case_no,
        "물건종류": property_type,
        "소재지": full_address,
        "감정가": f"{appraisal_price:,}원",
        "감정가_숫자": appraisal_price,
        "최저입찰가": lowest_price,
        "낙찰가": 0,   # 진행 중 - 낙찰 전
        "입찰자수": 0,
        "면적": f"{area_m2:.1f}㎡",
        "경매회차": 1,
        "지역": region,
        "낙찰률": 0.0,
        "데이터소스": f"법원경매정보 ({court_name}) - 실시간",
        "note": note,
        "매각예정일": auction_date_fmt,
        "청구금액": clm_amt,
        "원본데이터": data
    }


async def _court_site_search_async(case_no: str) -> Optional[Dict[str, Any]]:
    """
    법원 경매 사이트(courtauction.go.kr)에서 하이브리드 방식으로 사건 검색
    - 법원 목록: API 직접 호출로 코드 획득 (IP 차단 없음)
    - 사건 검색: 폼 버튼 클릭 + expect_response 캡처 (IP 차단 우회)
    - 주요 법원 코드 우선 검색 후 나머지 법원 추가 시도
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("playwright가 설치되지 않았습니다. pip install playwright && playwright install chromium")
        return None

    # 사건번호에서 연도/번호 추출
    m = re.match(r'(\d{4})타경(\d+)', case_no)
    if not m:
        logger.warning(f"[법원크롤러] 사건번호 형식 오류: {case_no}")
        return None
    case_year = m.group(1)
    case_number = m.group(2)

    BASE_URL = "https://www.courtauction.go.kr"

    # 주요 법원 코드 (케이스가 많은 법원 우선 / API 실패 시 폴백)
    # 실제 법원 경매 사이트 API 기준 코드 (B000xxx 형식)
    MAJOR_COURT_CODES = [
        "B000210",  # 서울중앙지방법원
        "B000211",  # 서울동부지방법원
        "B000212",  # 서울남부지방법원
        "B000213",  # 서울북부지방법원
        "B000215",  # 서울서부지방법원
        "B000214",  # 의정부지방법원
        "B000240",  # 인천지방법원
        "B000241",  # 부천지원
        "B000250",  # 수원지방법원
        "B000280",  # 대전지방법원
        "B000310",  # 대구지방법원
        "B000410",  # 부산지방법원
        "B000411",  # 울산지방법원
        "B000420",  # 창원지방법원
        "B000510",  # 광주지방법원
    ]
    # API 실패 시 드롭다운에서 직접 사용할 이름 폴백 (value = 이름)
    MAJOR_COURT_NAMES_FALLBACK = [
        "서울중앙지방법원", "서울동부지방법원", "서울남부지방법원",
        "서울북부지방법원", "서울서부지방법원", "의정부지방법원",
        "인천지방법원", "부천지원", "수원지방법원", "대전지방법원",
        "대구지방법원", "부산지방법원", "울산지방법원",
        "창원지방법원", "광주지방법원",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()

        try:
            # 1단계: 세션 초기화
            logger.info(f"[법원크롤러] 세션 초기화: {case_no}")
            await page.goto(f"{BASE_URL}/pgj/index.on",
                            wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # 2단계: 법원 목록 API 호출 (코드 + 이름 획득 - IP 차단 없음)
            logger.info("[법원크롤러] 법원 목록 조회 중...")
            court_list_result = await page.evaluate("""
                async () => {
                    try {
                        const resp = await fetch('/pgj/pgj002/selectCortOfcLst.on', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            body: JSON.stringify({"cortExecrOfcDvsCd": "00079B"})
                        });
                        if (!resp.ok) return null;
                        return await resp.json();
                    } catch(e) {
                        return null;
                    }
                }
            """)

            # 법원 코드+이름 매핑 생성
            court_code_to_name = {}
            all_court_codes = []
            use_name_fallback = False
            if court_list_result and court_list_result.get('data'):
                courts_data = court_list_result['data'].get('cortOfcLst', [])
                for c in courts_data:
                    code = c.get('code', '')
                    name = c.get('name', '')
                    if code:
                        court_code_to_name[code] = name
                        all_court_codes.append(code)
                logger.info(f"[법원크롤러] API로 {len(all_court_codes)}개 법원 코드 획득")
            else:
                logger.warning("[법원크롤러] 법원 목록 API 실패 → 이름 기반 폴백 사용")
                use_name_fallback = True

            if use_name_fallback:
                # API 실패 시: 이름 목록을 직접 courts_to_try에 사용 (드롭다운 value=이름)
                courts_to_try = MAJOR_COURT_NAMES_FALLBACK
                court_code_to_name = {n: n for n in MAJOR_COURT_NAMES_FALLBACK}  # name→name 매핑
            else:
                # 주요 법원 우선, 나머지 추가 (중복 제거)
                major_first = [c for c in MAJOR_COURT_CODES if c in all_court_codes]
                if not major_first:
                    major_first = list(all_court_codes)  # 모두 시도
                remaining = [c for c in all_court_codes if c not in major_first]
                courts_to_try = major_first + remaining

            logger.info(f"[법원크롤러] {len(courts_to_try)}개 법원 순차 검색 시작")

            # 3단계: 경매사건검색 탭 클릭 후 폼 로드
            await page.evaluate("""
                () => {
                    for (const a of document.querySelectorAll('a')) {
                        if (a.textContent.trim() === '경매사건검색') { a.click(); return; }
                    }
                }
            """)
            await asyncio.sleep(4)

            # 입력 필드 대기
            try:
                await page.wait_for_selector(
                    '#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo',
                    state='visible', timeout=10000
                )
            except Exception:
                logger.warning("[법원크롤러] 입력 필드 로드 실패 - 탭 클릭 재시도")
                await browser.close()
                return None

            # 연도 + 번호 입력 (year change 이벤트 필수: 사이트 JS 내부 상태 업데이트)
            # year change → AJAX → court SELECT 재구성 (wait_for_selector로 완료 대기)
            await page.evaluate("""
                (args) => {
                    const yr = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                    if (yr) {
                        for (const opt of yr.options) {
                            if (opt.text === args.year || opt.value === args.year) {
                                opt.selected = true;
                                yr.dispatchEvent(new Event('change', {bubbles: true}));
                                break;
                            }
                        }
                    }
                    const no = document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo');
                    if (no) {
                        no.value = args.number;
                        no.dispatchEvent(new Event('input', {bubbles: true}));
                    }
                }
            """, {"year": case_year, "number": case_number})

            # year change AJAX 완료 후 court SELECT 재등장 대기
            try:
                await page.wait_for_selector(
                    '#mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc',
                    state='visible', timeout=8000
                )
            except Exception:
                logger.warning("[법원크롤러] 법원 SELECT 요소 없음 - 폼 로드 실패")
                await browser.close()
                return None

            court_select_count = await page.evaluate("""
                () => {
                    const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                    return sel ? sel.options.length : 0;
                }
            """)
            logger.info(f"[법원크롤러] 법원 SELECT 확인: {court_select_count}개 옵션")

            # 4단계: 각 법원을 선택하고 폼 제출 + 응답 캡처
            # 검색 후 페이지가 결과 화면으로 전환되어 폼이 사라지므로,
            # i > 0 이면 탭을 다시 클릭하여 폼을 복구하고 연도/번호 재입력
            for i, court_code in enumerate(courts_to_try):
                court_name = court_code_to_name.get(court_code, court_code)

                if i > 0:
                    # 이전 검색 후 폼이 사라졌으므로 탭 재클릭하여 폼 복구
                    await page.evaluate("""
                        () => {
                            for (const a of document.querySelectorAll('a')) {
                                if (a.textContent.trim() === '경매사건검색') { a.click(); return; }
                            }
                        }
                    """)
                    try:
                        await page.wait_for_selector(
                            '#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo',
                            state='visible', timeout=8000
                        )
                    except Exception:
                        logger.warning(f"[법원크롤러] 검색 폼 재로드 실패 - 중단 ({i+1}번째 시도)")
                        break

                    # 연도/번호 재입력 (year change 이벤트 포함)
                    await page.evaluate("""
                        (args) => {
                            const yr = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                            if (yr) {
                                for (const opt of yr.options) {
                                    if (opt.text === args.year || opt.value === args.year) {
                                        opt.selected = true;
                                        yr.dispatchEvent(new Event('change', {bubbles: true}));
                                        break;
                                    }
                                }
                            }
                            const no = document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo');
                            if (no) {
                                no.value = args.number;
                                no.dispatchEvent(new Event('input', {bubbles: true}));
                            }
                        }
                    """, {"year": case_year, "number": case_number})

                    # year change AJAX 완료 후 court SELECT 재등장 대기
                    try:
                        await page.wait_for_selector(
                            '#mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc',
                            state='visible', timeout=8000
                        )
                    except Exception:
                        logger.warning(f"[법원크롤러] 법원 SELECT 재로드 실패 - 중단 ({i+1}번째 시도)")
                        break

                # 법원 선택 + change 이벤트 (사이트 JS 내부 court 상태 업데이트)
                select_result = await page.evaluate("""
                    (name) => {
                        const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                        if (!sel) return 'SELECT_NOT_FOUND';
                        for (const opt of sel.options) {
                            if (opt.value === name || opt.text === name) {
                                opt.selected = true;
                                sel.dispatchEvent(new Event('change', {bubbles: true}));
                                return 'OK';
                            }
                        }
                        return 'NOT_FOUND:' + sel.options.length;
                    }
                """, court_name)

                if select_result == 'SELECT_NOT_FOUND':
                    logger.warning("[법원크롤러] 법원 SELECT 요소 없음 - 검색 종료")
                    break
                if select_result.startswith('NOT_FOUND'):
                    logger.debug(f"[법원크롤러] {court_name}({court_code}): 드롭다운에 없음 ({select_result}), 건너뜀")
                    continue

                # 폼 제출 + 응답 캡처 (별도 evaluate - 페이지 자체 JS가 API 호출 → IP 차단 우회)
                try:
                    async with page.expect_response(
                        lambda r: 'selectAuctnCsSrchRslt' in r.url,
                        timeout=10000
                    ) as resp_info:
                        await page.evaluate("""
                            () => {
                                const btn = document.getElementById('mf_wfm_mainFrame_btn_auctnCsSrchBtn');
                                if (btn) btn.click();
                            }
                        """)

                    resp = await resp_info.value
                    body = await resp.text()
                    resp_data = json.loads(body)
                    case_data = resp_data.get('data', {})

                    # IP 차단 감지
                    if case_data and case_data.get('ipcheck') is False:
                        logger.warning("[법원크롤러] IP 차단 감지 - 검색 중단")
                        await browser.close()
                        return None

                    # 사건 데이터 확인
                    if case_data and case_data.get('dma_csBasInf') is not None:
                        logger.info(f"[법원크롤러] 성공! {court_name}({court_code}) - {i+1}번째 시도")
                        await browser.close()
                        return _parse_court_data(case_data, case_no)

                    logger.debug(f"[법원크롤러] {court_name}({court_code}) ({i+1}/{len(courts_to_try)}): 해당 사건 없음")

                except json.JSONDecodeError as e:
                    logger.debug(f"[법원크롤러] {court_name}: JSON 파싱 실패 - {e}")
                except Exception as e:
                    logger.debug(f"[법원크롤러] {court_name}: 타임아웃 또는 오류 - {type(e).__name__}")

            await browser.close()
            logger.info(f"[법원크롤러] {len(courts_to_try)}개 법원 검색 완료 - 사건 없음: {case_no}")
            return None

        except Exception as e:
            logger.error(f"[법원크롤러] 오류: {e}", exc_info=True)
            try:
                await browser.close()
            except Exception:
                pass
            return None


def get_auction_from_court_site(case_no: str) -> Optional[Dict[str, Any]]:
    """
    법원 경매 사이트 크롤러 동기 래퍼
    새 스레드 + 새 이벤트 루프로 실행 (FastAPI 이벤트 루프와 충돌 방지)
    타임아웃: 90초
    """
    result_container = [None]
    error_container = [None]

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_container[0] = loop.run_until_complete(
                _court_site_search_async(case_no)
            )
        except Exception as e:
            error_container[0] = e
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    thread.join(timeout=90)

    if thread.is_alive():
        logger.error(f"[법원크롤러] 타임아웃 (90초): {case_no}")
        return None

    if error_container[0]:
        logger.error(f"[법원크롤러] 스레드 오류: {error_container[0]}")
        return None

    return result_container[0]


# -----------------------------
# 1. 샘플 DB에서 경매 물건 조회
# -----------------------------
def get_auction_item(case_no: str, site: str = None) -> Dict[str, Any]:
    """
    경매 물건 정보 조회 (사건번호로 검색)
    1순위: 로컬 CSV DB
    2순위: ValueAuction API (실시간)
    3순위: 유사 물건 추천

    Args:
        case_no: 사건번호 (예: 2025타경402)
        site: 담당법원명 (선택, 중복 사건번호 구분용, 예: 대전지방법원)
    """
    try:
        logger.info(f"경매 물건 조회 시작: {case_no}" + (f", 법원: {site}" if site else ""))

        # 1단계: CSV 파일에서 검색
        csv_path = Path("data/auction_data.csv")

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            result = df[df['사건번호'] == case_no]

            if not result.empty:
                # CSV에서 데이터 찾음
                row = result.iloc[0]
                logger.info(f"✓ 로컬 DB에서 찾음: {case_no}")

                return {
                    "물건번호": row['물건번호'],
                    "사건번호": row['사건번호'],
                    "물건종류": row['물건종류'],
                    "소재지": row['소재지'],
                    "감정가": f"{int(row['감정가']):,}원",
                    "감정가_숫자": int(row['감정가']),
                    "최저입찰가": int(row['최저입찰가']),
                    "낙찰가": int(row['낙찰가']),
                    "입찰자수": int(row['입찰자수']),
                    "면적": f"{row['면적']}㎡",
                    "경매회차": int(row['경매회차']),
                    "지역": row['지역'],
                    "낙찰률": float(row['낙찰률']),
                    "데이터소스": "로컬 DB (검증된 데이터)",
                    "note": "로컬 데이터베이스에서 가져온 검증된 데이터입니다."
                }

        # 2단계: ValueAuction API로 실시간 검색
        logger.info(f"로컬 DB에 없음 → ValueAuction API로 검색 중...")
        valueauction_data = get_auction_from_valueauction(case_no, site)

        if valueauction_data:
            logger.info(f"✓ ValueAuction API에서 찾음: {case_no}")
            return valueauction_data

        # 3단계: 법원 경매 사이트 크롤링 (Playwright)
        logger.info(f"ValueAuction에도 없음 → 법원 경매 사이트 크롤링 중... (최대 90초)")
        court_data = get_auction_from_court_site(case_no)

        if court_data:
            logger.info(f"✓ 법원 경매 사이트에서 찾음: {case_no}")
            return court_data

        # 4단계: 모두 실패 - 명확한 에러 반환
        logger.warning(f"어디서도 찾을 수 없음: {case_no}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "사건번호를 찾을 수 없습니다",
                "case_no": case_no,
                "message": f"사건번호 '{case_no}'에 해당하는 경매 물건을 찾을 수 없습니다. 사건번호를 다시 확인해주세요.",
                "suggestions": [
                    "사건번호 형식을 확인하세요 (예: 2025타경12345)",
                    "법원 경매 사이트에서 정확한 사건번호를 확인하세요",
                    "최근 등록된 경매만 조회 가능합니다"
                ]
            }
        )

    except HTTPException:
        # HTTPException은 그대로 전파
        raise
    except Exception as e:
        # 다른 예외만 에러 로깅 후 500 반환
        logger.error(f"경매 물건 조회 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"경매 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


def search_similar_item(df: pd.DataFrame, case_no: str) -> Dict[str, Any]:
    """
    유사한 물건 검색 (사건번호를 찾지 못한 경우)
    """
    try:
        # 랜덤으로 하나 선택
        random_row = df.sample(n=1).iloc[0]

        logger.info(f"유사 물건 반환: {random_row['사건번호']}")

        return {
            "물건번호": random_row['물건번호'],
            "사건번호": case_no,
            "물건종류": random_row['물건종류'],
            "소재지": random_row['소재지'],
            "감정가": f"{int(random_row['감정가']):,}원",
            "감정가_숫자": int(random_row['감정가']),
            "최저입찰가": int(random_row['최저입찰가']),
            "낙찰가": int(random_row['낙찰가']),
            "입찰자수": int(random_row['입찰자수']),
            "면적": f"{random_row['면적']}㎡",
            "경매회차": int(random_row['경매회차']),
            "지역": random_row['지역'],
            "낙찰률": float(random_row['낙찰률']),
            "데이터소스": "샘플 DB - 유사 물건",
            "note": f"입력하신 사건번호 '{case_no}'를 찾을 수 없어 유사한 물건 정보를 표시합니다. 이 데이터는 샘플 데이터입니다."
        }
    except Exception as e:
        logger.error(f"유사 물건 검색 실패: {e}")
        return create_dummy_data(case_no)


def create_dummy_data(case_no: str) -> Dict[str, Any]:
    """
    기본 더미 데이터 생성
    """
    return {
        "물건번호": "SAMPLE-000001",
        "사건번호": case_no,
        "물건종류": "아파트",
        "소재지": "서울 강남구",
        "감정가": "300,000,000원",
        "감정가_숫자": 300000000,
        "최저입찰가": 300000000,
        "낙찰가": 240000000,
        "입찰자수": 5,
        "면적": "85.0㎡",
        "경매회차": 1,
        "지역": "서울",
        "낙찰률": 0.8,
        "데이터소스": "기본 더미 데이터",
        "note": "샘플 DB 조회 실패로 기본 데이터를 표시합니다."
    }


# -----------------------------
# 2. AI 낙찰가 예측
# -----------------------------


# =============================
# v3 Model Functions
# =============================

def calc_lowest_price_by_round(appraisal_price: int, auction_round: int) -> int:
    """
    경매회차에 따른 최저입찰가 계산
    1회: 100%
    2회: 80%  (0.8)
    3회: 64%  (0.8 * 0.8)
    4회: 51.2% (0.8 * 0.8 * 0.8)
    """
    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8
    return int(appraisal_price * ratio)


def create_features_v3(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int = None,
    share_floor: float = 0,
    share_land: float = 0,
    debt_ratio: float = 0,
    second_price: int = 0,
    lowest_bid_price: int = None,  # ValueAuction API에서 받은 실제 최저입찰가
) -> np.ndarray:
    """
    v3 특성 생성 - 정확한 최저입찰가 반영

    Args:
        lowest_bid_price: ValueAuction API에서 받은 법원의 실제 최저입찰가
                         (None이면 경매회차에 따라 자동 계산)
    """
    features = []

    # ✅ 핵심 개선: ValueAuction API에서 받은 실제 최저입찰가 사용
    if lowest_bid_price is None or lowest_bid_price == 0:
        # fallback: API에서 못 받았을 경우에만 계산
        lowest_bid_price = calc_lowest_price_by_round(start_price, auction_round)

    lowest_price_ratio = lowest_bid_price / start_price if start_price > 0 else 0.8

    if bidders_actual is None:
        bidders_actual = bidders

    # 1. 기본 가격 특성 (로그 변환 포함)
    features.extend([
        start_price,
        np.log1p(start_price),
        lowest_bid_price,          # ✅ 정확한 최저입찰가
        np.log1p(lowest_bid_price),
        lowest_price_ratio,        # ✅ 실제 비율 (0.8, 0.64, 0.512 등)
    ])

    # 2. 물건 종류 (원-핫 인코딩)
    property_types = ['아파트', '다세대', '단독주택', '오피스텔', '토지', '상가', '기타']
    for ptype in property_types:
        features.append(1 if ptype in property_type else 0)

    # 3. 지역 (원-핫 인코딩 - 주요 지역만)
    regions = ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '기타']
    region_matched = False
    for reg in regions[:-1]:
        if reg in region:
            features.append(1)
            region_matched = True
        else:
            features.append(0)
    features.append(0 if region_matched else 1)  # 기타

    # 4. 면적 관련 특성
    features.extend([
        area,
        np.log1p(area),
        start_price / area if area > 0 else 0,  # 평당가
        np.log1p(start_price / area) if area > 0 else 0,
    ])

    # 5. 경매 진행 상황
    features.extend([
        auction_round,
        np.log1p(auction_round),
        bidders,
        bidders_actual,
        np.log1p(bidders_actual),
    ])

    # 6. 공유지분 & 부채
    features.extend([
        share_floor,
        share_land,
        debt_ratio,
        np.log1p(debt_ratio),
    ])

    # 7. 2순위 가격 (음수 처리)
    second_price_safe = max(0, second_price)  # 음수 방지
    features.extend([
        second_price_safe,
        np.log1p(second_price_safe),
        second_price_safe / start_price if start_price > 0 and second_price_safe > 0 else 0,
    ])

    # 8. ✅ 최저입찰가 상호작용 특성 (NEW)
    features.extend([
        lowest_price_ratio * auction_round,           # 가율 x 회차
        lowest_price_ratio * bidders_actual,          # 가율 x 입찰자
        lowest_bid_price * bidders_actual,            # 최저가 x 입찰자
        np.log1p(lowest_price_ratio * auction_round),
    ])

    # 9. 고급 상호작용 특성
    features.extend([
        start_price * auction_round,
        start_price * bidders_actual,
        area * auction_round,
        (start_price / area if area > 0 else 0) * auction_round,  # 평당가 x 회차
        bidders_actual / auction_round if auction_round > 0 else bidders_actual,  # 회차당 입찰자
        share_floor + share_land,  # 총 공유지분
        debt_ratio * auction_round,
    ])

    # 10. 다항 특성
    features.extend([
        start_price ** 2,
        area ** 2,
        auction_round ** 2,
        bidders_actual ** 2,
    ])

    # NaN, Inf 값 처리
    features_array = np.array(features, dtype=np.float64)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)

    return features_array


def load_training_data():
    """데이터베이스에서 훈련 데이터 로드"""
    logger.info(f"데이터베이스 로드: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    # 낙찰 데이터만 조회 (actual_price > 0)
    query = """
        SELECT
            감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
            입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
            second_price, actual_price
        FROM predictions
        WHERE actual_price IS NOT NULL AND actual_price > 0
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    logger.info(f"로드된 데이터: {len(df)}건")

    # 결측치 처리
    df['입찰자수_실제'] = df['입찰자수_실제'].fillna(df['입찰자수'])
    df['공유지분_건물'] = df['공유지분_건물'].fillna(0)
    df['공유지분_토지'] = df['공유지분_토지'].fillna(0)
    df['청구금액비율'] = df['청구금액비율'].fillna(0)
    df['second_price'] = df['second_price'].fillna(0)

    # 이상치 제거 (감정가 대비 낙찰가가 너무 비정상적인 경우)
    df = df[(df['actual_price'] > df['감정가'] * 0.1) & (df['actual_price'] < df['감정가'] * 2)]

    logger.info(f"이상치 제거 후: {len(df)}건")

    return df


# =============================
# Legacy Model Functions (v1, v2)
# =============================


# =============================
# v4 모델 전용 함수 (v3 + 패턴 특성)
# =============================

def create_features_v4(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int = None,
    share_floor: float = 0,
    share_land: float = 0,
    debt_ratio: float = 0,
    second_price: int = 0,
    pattern_property_round: dict = None,
    pattern_region: dict = None,
    pattern_complex: dict = None,
    lowest_bid_price: int = None,  # ValueAuction API에서 받은 실제 최저입찰가
) -> np.ndarray:
    """
    v4 특성 생성 - v3 + 과거 패턴 특성 추가
    특성 개수: 53 (v3) + 5 (패턴) = 58개

    Args:
        lowest_bid_price: ValueAuction API에서 받은 법원의 실제 최저입찰가
                         (None이면 경매회차에 따라 자동 계산)
    """
    features = []

    # ✅ 핵심 개선: ValueAuction API에서 받은 실제 최저입찰가 사용
    if lowest_bid_price is None or lowest_bid_price == 0:
        # fallback: API에서 못 받았을 경우에만 계산
        lowest_bid_price = calc_lowest_price_by_round(start_price, auction_round)

    lowest_price_ratio = lowest_bid_price / start_price if start_price > 0 else 0.8

    if bidders_actual is None:
        bidders_actual = bidders

    # 1. 기본 가격 특성 (로그 변환 포함)
    features.extend([
        start_price,
        np.log1p(start_price),
        lowest_bid_price,          # ✅ 정확한 최저입찰가
        np.log1p(lowest_bid_price),
        lowest_price_ratio,        # ✅ 실제 비율 (0.8, 0.64, 0.512 등)
    ])

    # 2. 물건 종류 (원-핫 인코딩)
    property_types = ['아파트', '다세대', '단독주택', '오피스텔', '토지', '상가', '기타']
    for ptype in property_types:
        features.append(1 if ptype in property_type else 0)

    # 3. 지역 (원-핫 인코딩 - 주요 지역만)
    regions = ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '기타']
    region_matched = False
    for reg in regions[:-1]:
        if reg in region:
            features.append(1)
            region_matched = True
        else:
            features.append(0)
    features.append(0 if region_matched else 1)  # 기타

    # 4. 면적 관련 특성
    features.extend([
        area,
        np.log1p(area),
        start_price / area if area > 0 else 0,  # 평당가
        np.log1p(start_price / area) if area > 0 else 0,
    ])

    # 5. 경매 진행 상황
    features.extend([
        auction_round,
        np.log1p(auction_round),
        bidders,
        bidders_actual,
        np.log1p(bidders_actual),
    ])

    # 6. 공유지분 & 부채
    features.extend([
        share_floor,
        share_land,
        debt_ratio,
        np.log1p(debt_ratio),
    ])

    # 7. 2순위 가격 (음수 처리)
    second_price_safe = max(0, second_price)  # 음수 방지
    features.extend([
        second_price_safe,
        np.log1p(second_price_safe),
        second_price_safe / start_price if start_price > 0 and second_price_safe > 0 else 0,
    ])

    # 8. ✅ 최저입찰가 상호작용 특성 (NEW)
    features.extend([
        lowest_price_ratio * auction_round,           # 가율 x 회차
        lowest_price_ratio * bidders_actual,          # 가율 x 입찰자
        lowest_bid_price * bidders_actual,            # 최저가 x 입찰자
        np.log1p(lowest_price_ratio * auction_round),
    ])

    # 9. 고급 상호작용 특성
    features.extend([
        start_price * auction_round,
        start_price * bidders_actual,
        area * auction_round,
        (start_price / area if area > 0 else 0) * auction_round,  # 평당가 x 회차
        bidders_actual / auction_round if auction_round > 0 else bidders_actual,  # 회차당 입찰자
        share_floor + share_land,  # 총 공유지분
        debt_ratio * auction_round,
    ])

    # 10. 다항 특성
    features.extend([
        start_price ** 2,
        area ** 2,
        auction_round ** 2,
        bidders_actual ** 2,
    ])

    # ====================
    # 11. 과거 패턴 특성 (v4 NEW)
    # ====================

    # 물건종류 정규화
    property_category = '기타'
    if '아파트' in property_type:
        property_category = '아파트'
    elif '오피스텔' in property_type:
        property_category = '오피스텔'
    elif '다세대' in property_type or '연립' in property_type:
        property_category = '다세대'
    elif '단독' in property_type:
        property_category = '단독주택'
    elif '상가' in property_type or '점포' in property_type:
        property_category = '상가'
    elif '토지' in property_type:
        property_category = '토지'

    # 지역 그룹핑
    region_group = '기타'
    for r in ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']:
        if r in region:
            region_group = r
            break

    # 패턴 1: 물건종류 × 경매회차
    pattern_pr_key = f"{property_category}_{auction_round}"
    pattern_pr_ratio = 0.5  # 기본값
    if pattern_property_round and pattern_pr_key in pattern_property_round:
        pattern_pr_ratio = pattern_property_round[pattern_pr_key]['avg_ratio']

    # 패턴 2: 지역별 평균
    region_avg_ratio = 0.5  # 기본값
    if pattern_region and region_group in pattern_region:
        region_avg_ratio = pattern_region[region_group]['avg_ratio']

    # 패턴 3: 복합 패턴 (지역 × 물건 × 회차)
    pattern_complex_key = f"{region_group}_{property_category}_{auction_round}"
    pattern_complex_ratio = 0.5  # 기본값
    if pattern_complex and pattern_complex_key in pattern_complex:
        pattern_complex_ratio = pattern_complex[pattern_complex_key]['avg_ratio']

    # 패턴 특성 추가 (5개)
    features.extend([
        pattern_pr_ratio,                                    # 1. 물건×회차 평균
        region_avg_ratio,                                    # 2. 지역 평균
        pattern_complex_ratio,                               # 3. 복합 패턴
        pattern_pr_ratio * region_avg_ratio,                 # 4. 패턴 상호작용
        abs(pattern_pr_ratio - region_avg_ratio),            # 5. 패턴 차이
    ])

    # NaN, Inf 값 처리
    features_array = np.array(features, dtype=np.float64)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)

    return features_array


def load_training_data():
    """데이터베이스에서 훈련 데이터 로드"""
    logger.info(f"데이터베이스 로드: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    # 낙찰 데이터만 조회 (actual_price > 0)
    query = """
        SELECT
            감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
            입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
            second_price, actual_price
        FROM predictions
        WHERE actual_price IS NOT NULL AND actual_price > 0
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    logger.info(f"로드된 데이터: {len(df)}건")

    # 결측치 처리
    df['입찰자수_실제'] = df['입찰자수_실제'].fillna(df['입찰자수'])
    df['공유지분_건물'] = df['공유지분_건물'].fillna(0)
    df['공유지분_토지'] = df['공유지분_토지'].fillna(0)
    df['청구금액비율'] = df['청구금액비율'].fillna(0)
    df['second_price'] = df['second_price'].fillna(0)

    # 이상치 제거 (감정가 대비 낙찰가가 너무 비정상적인 경우)
    df = df[(df['actual_price'] > df['감정가'] * 0.1) & (df['actual_price'] < df['감정가'] * 2)]

    logger.info(f"이상치 제거 후: {len(df)}건")

    return df


def create_features(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int = 1,
    bidders: int = 10
) -> np.ndarray:
    """
    입력 데이터로부터 36개 특성 생성 (훈련 시 사용한 순서와 동일)
    """
    # 최저입찰가 (감정가의 80%)
    min_price = start_price * 0.8
    평당감정가 = start_price / (area * 0.3025)

    features = []

    # 1. 기본 특성 (11개)
    features.extend([
        start_price,                                    # 감정가
        np.log1p(start_price),                         # 감정가_log
        min_price,                                      # 최저입찰가
        np.log1p(min_price),                           # 최저입찰가_log
        0.8,                                            # 최저가율
        bidders,                                        # 입찰자수
        np.log1p(bidders),                             # 입찰자수_log
        bidders / 11.0,                                # 경쟁지수 (평균 10명 가정)
        auction_round,                                  # 경매회차
        auction_round ** 2,                            # 경매회차_제곱
        max(0.5, 1 - (auction_round - 1) * 0.1),      # 회차페널티
    ])

    # 2. 상호작용 특성 (2개)
    features.extend([
        np.log1p(start_price) * np.log1p(bidders),    # 감정가x입찰자수
        0.8 * bidders,                                 # 최저가율x입찰자수
    ])

    # 3. 면적 특성 (5개)
    features.extend([
        area,                                           # 면적
        np.log1p(area),                                # 면적_log
        평당감정가,                                      # 평당감정가
        np.log1p(평당감정가),                           # 평당감정가_log
        np.log1p(area) * np.log1p(bidders),           # 면적x입찰자수
    ])

    # 4. 지역 인코딩 (1개)
    region_map = {'경기': 0, '기타': 1, '대구': 2, '부산': 3, '서울': 4, '인천': 5}
    region_idx = region_map.get(region, 1)  # 기본값: 기타
    features.append(region_idx)  # 지역_encoded

    # 5. 지역 원-핫 (6개) - 알파벳 순: 경기, 기타, 대구, 부산, 서울, 인천
    region_order = ['경기', '기타', '대구', '부산', '서울', '인천']
    for r in region_order:
        features.append(1 if region == r else 0)

    # 6. 물건종류 인코딩 (1개)
    type_map = {'다세대': 0, '단독주택': 1, '상가': 2, '아파트': 3, '오피스텔': 4}
    type_idx = type_map.get(property_type, 3)  # 기본값: 아파트
    features.append(type_idx)  # 물건종류_encoded

    # 7. 물건종류 원-핫 (5개) - 알파벳 순: 다세대, 단독주택, 상가, 아파트, 오피스텔
    type_order = ['다세대', '단독주택', '상가', '아파트', '오피스텔']
    for t in type_order:
        features.append(1 if property_type == t else 0)

    # 8. 가격구간 원-핫 (5개)
    if start_price <= 100_000_000:
        price_range = [1, 0, 0, 0, 0]  # 1억이하
    elif start_price <= 300_000_000:
        price_range = [0, 1, 0, 0, 0]  # 1-3억
    elif start_price <= 500_000_000:
        price_range = [0, 0, 1, 0, 0]  # 3-5억
    elif start_price <= 1_000_000_000:
        price_range = [0, 0, 0, 1, 0]  # 5-10억
    else:
        price_range = [0, 0, 0, 0, 1]  # 10억이상
    features.extend(price_range)

    logger.info(f"생성된 특성 개수: {len(features)}")
    return np.array(features).reshape(1, -1)


def create_features_v2(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int,
    second_price: int,
    is_hard: int,
    tag_count: int,
    share_floor: int,
    share_land: int,
    debt_ratio: float
) -> np.ndarray:
    """
    신규 변수를 포함한 특성 생성 (48개 특성)
    """
    # 기본값 설정
    if bidders_actual is None or bidders_actual == 0:
        bidders_actual = bidders
    if second_price is None or second_price < 0:
        second_price = 0

    features = []

    # 1. 기존 기본 특성 (11개)
    min_price = start_price * 0.8
    평당감정가 = start_price / (area * 0.3025) if area > 0 else 0

    features.extend([
        start_price,
        np.log1p(start_price),
        min_price,
        np.log1p(min_price),
        0.8,
        bidders_actual,  # 실제 입찰자수 사용
        np.log1p(bidders_actual),
        bidders_actual / 11.0,
        auction_round,
        auction_round ** 2,
        max(0.5, 1 - (auction_round - 1) * 0.1),
    ])

    # 2. 상호작용 특성 (2개)
    features.extend([
        np.log1p(start_price) * np.log1p(bidders_actual),
        0.8 * bidders_actual,
    ])

    # 3. 면적 특성 (5개)
    features.extend([
        area,
        np.log1p(area),
        평당감정가,
        np.log1p(평당감정가),
        np.log1p(area) * np.log1p(bidders_actual),
    ])

    # 4. 지역 인코딩 (1개)
    region_map = {'경기': 0, '기타': 1, '대구': 2, '부산': 3, '서울': 4, '인천': 5}
    region_idx = region_map.get(region, 1)
    features.append(region_idx)

    # 5. 지역 원-핫 (6개)
    region_order = ['경기', '기타', '대구', '부산', '서울', '인천']
    for r in region_order:
        features.append(1 if region == r else 0)

    # 6. 물건종류 인코딩 (1개)
    type_map = {'다세대': 0, '단독주택': 1, '상가': 2, '아파트': 3, '오피스텔': 4}
    type_idx = type_map.get(property_type, 3)
    features.append(type_idx)

    # 7. 물건종류 원-핫 (5개)
    type_order = ['다세대', '단독주택', '상가', '아파트', '오피스텔']
    for t in type_order:
        features.append(1 if property_type == t else 0)

    # 8. 가격구간 원-핫 (5개)
    if start_price <= 100_000_000:
        price_range = [1, 0, 0, 0, 0]
    elif start_price <= 300_000_000:
        price_range = [0, 1, 0, 0, 0]
    elif start_price <= 500_000_000:
        price_range = [0, 0, 1, 0, 0]
    elif start_price <= 1_000_000_000:
        price_range = [0, 0, 0, 1, 0]
    else:
        price_range = [0, 0, 0, 0, 1]
    features.extend(price_range)

    # ===== 신규 변수 (12개) =====

    # 9. 2등 입찰가 관련 (3개)
    features.append(second_price)
    features.append(np.log1p(second_price))
    # 경쟁 강도 (1등-2등 차이)
    if second_price > 0:
        competition_gap = 1 - (second_price / start_price)
    else:
        competition_gap = 0
    features.append(competition_gap)

    # 10. 권리 관련 (4개)
    features.append(is_hard)
    features.append(tag_count)
    features.append(np.log1p(tag_count))
    # 권리 리스크 점수
    risk_score = is_hard * 0.2 + tag_count * 0.05
    features.append(risk_score)

    # 11. 공유지분 (2개)
    features.append(share_floor)
    features.append(share_land)

    # 12. 청구금액 (3개)
    features.append(debt_ratio)
    features.append(debt_ratio ** 2)
    # 부채 위험 지표
    debt_risk = 1 if debt_ratio > 0.7 else 0
    features.append(debt_risk)

    return np.array(features).reshape(1, -1)


def create_features_enhanced(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int,
    second_price: int,
    is_hard: int,
    tag_count: int,
    share_floor: int,
    share_land: int,
    debt_ratio: float
) -> np.ndarray:
    """
    고도화된 특성 생성 (기존 48개 + 신규 40개 = 88개 특성)
    """
    # 기본값 설정
    if bidders_actual is None or bidders_actual == 0:
        bidders_actual = bidders
    if second_price is None or second_price < 0:
        second_price = 0

    # ===== 기존 48개 특성 (create_features_v2와 동일) =====
    features = []

    min_price = start_price * 0.8
    평당감정가 = start_price / (area * 0.3025) if area > 0 else 0

    features.extend([
        start_price, np.log1p(start_price), min_price, np.log1p(min_price),
        0.8, bidders_actual, np.log1p(bidders_actual), bidders_actual / 11.0,
        auction_round, auction_round ** 2, max(0.5, 1 - (auction_round - 1) * 0.1),
    ])

    features.extend([
        np.log1p(start_price) * np.log1p(bidders_actual),
        0.8 * bidders_actual,
    ])

    features.extend([
        area, np.log1p(area), 평당감정가, np.log1p(평당감정가),
        np.log1p(area) * np.log1p(bidders_actual),
    ])

    region_map = {'경기': 0, '기타': 1, '대구': 2, '부산': 3, '서울': 4, '인천': 5}
    features.append(region_map.get(region, 1))

    region_order = ['경기', '기타', '대구', '부산', '서울', '인천']
    for r in region_order:
        features.append(1 if region == r else 0)

    type_map = {'다세대': 0, '단독주택': 1, '상가': 2, '아파트': 3, '오피스텔': 4}
    features.append(type_map.get(property_type, 3))

    type_order = ['다세대', '단독주택', '상가', '아파트', '오피스텔']
    for t in type_order:
        features.append(1 if property_type == t else 0)

    if start_price <= 100_000_000:
        price_range = [1, 0, 0, 0, 0]
    elif start_price <= 300_000_000:
        price_range = [0, 1, 0, 0, 0]
    elif start_price <= 500_000_000:
        price_range = [0, 0, 1, 0, 0]
    elif start_price <= 1_000_000_000:
        price_range = [0, 0, 0, 1, 0]
    else:
        price_range = [0, 0, 0, 0, 1]
    features.extend(price_range)

    features.append(second_price)
    features.append(np.log1p(second_price))
    competition_gap = 1 - (second_price / start_price) if second_price > 0 else 0
    features.append(competition_gap)

    features.append(is_hard)
    features.append(tag_count)
    features.append(np.log1p(tag_count))
    risk_score = is_hard * 0.2 + tag_count * 0.05
    features.append(risk_score)

    features.append(share_floor)
    features.append(share_land)

    features.append(debt_ratio)
    features.append(debt_ratio ** 2)
    debt_risk = 1 if debt_ratio > 0.7 else 0
    features.append(debt_risk)

    # ===== 신규 고급 특성 엔지니어링 (45개) =====

    # 가격 관련 고급 특성 (5개)
    features.append(np.sqrt(start_price))
    features.append(np.cbrt(start_price))
    price_per_area = start_price / area if area > 0 else 0
    features.append(np.log1p(price_per_area))
    price_tier = np.log10(start_price + 1) / 10
    features.append(price_tier)
    price_gap = start_price - min_price
    features.append(np.log1p(price_gap))

    # 입찰 경쟁 고급 특성 (6개)
    bidder_density = bidders_actual / max(1, auction_round)
    features.append(bidder_density)
    features.append(bidders_actual ** 2)
    second_price_ratio = second_price / start_price if second_price > 0 and start_price > 0 else 0
    features.append(second_price_ratio)
    competition_intensity = (start_price - second_price) / start_price if second_price > 0 else 1.0
    features.append(competition_intensity)
    features.append(np.log1p(bidders_actual) ** 2)
    competition_index = bidders_actual * bidder_density
    features.append(competition_index)

    # 경매회차 고급 특성 (4개)
    features.append(np.log1p(auction_round))
    features.append(auction_round ** 3)
    round_depreciation = max(0.3, 1 - (auction_round * 0.15))
    features.append(round_depreciation)
    serious_failure = 1 if auction_round >= 3 else 0
    features.append(serious_failure)

    # 면적 고급 특성 (5개)
    features.append(area ** 2)
    features.append(평당감정가 ** 2)
    is_small = 1 if area < 60 else 0
    is_large = 1 if area > 120 else 0
    features.append(is_small)
    features.append(is_large)
    area_efficiency = area / (np.log1p(start_price) + 1)
    features.append(area_efficiency)

    # 복합 상호작용 특성 (8개)
    features.append(np.log1p(start_price) * auction_round)
    features.append(np.log1p(start_price) * np.log1p(area))
    features.append(bidders_actual * auction_round)
    features.append(bidders_actual * area)
    features.append(평당감정가 * bidders_actual)
    features.append(auction_round * area)
    features.append(np.log1p(start_price) * bidders_actual * auction_round)
    features.append(bidders_actual * np.log1p(start_price))

    # 권리 및 리스크 고급 특성 (6개)
    features.append(is_hard * np.log1p(start_price))
    tag_density = tag_count / max(1, auction_round)
    features.append(tag_density)
    total_risk = (is_hard * 0.3 + tag_count * 0.1 + share_floor * 0.2 +
                  share_land * 0.2 + debt_ratio * 0.2)
    features.append(total_risk)
    features.append(is_hard * debt_ratio)
    total_share = share_floor + share_land
    features.append(total_share)
    features.append(total_risk * auction_round)

    # 지역-물건 상호작용 (2개)
    is_seoul_apt = 1 if (region == '서울' and property_type == '아파트') else 0
    features.append(is_seoul_apt)
    is_gyeonggi_apt = 1 if (region == '경기' and property_type == '아파트') else 0
    features.append(is_gyeonggi_apt)

    # 부채 고급 특성 (4개)
    features.append(np.log1p(debt_ratio))
    features.append(debt_ratio ** 3)
    high_debt = 1 if debt_ratio > 0.5 else 0
    features.append(high_debt)
    features.append(debt_ratio * bidders_actual)

    return np.array(features).reshape(1, -1)


def predict_price(start_price: int, bidders: int = None) -> int:
    """
    AI 모델을 사용하여 낙찰가 예측 (기본 버전 - 36개 특성 활용)
    최소 입력값으로 나머지는 기본값 사용
    예측값은 감정가의 10% ~ 100% 범위로 제한
    """
    if bidders is None:
        bidders = settings.DEFAULT_BIDDERS

    try:
        if model is not None:
            # 기본값 설정
            default_property_type = "아파트"  # 가장 일반적
            default_region = "서울"           # 기본 지역
            default_area = 85.0               # 평균 아파트 면적
            default_auction_round = 1         # 첫 회차

            # 36개 특성 생성 (고급 예측 함수 활용)
            features = create_features(
                start_price=start_price,
                property_type=default_property_type,
                region=default_region,
                area=default_area,
                auction_round=default_auction_round,
                bidders=bidders
            )

            # AI 모델 예측
            prediction = model.predict(features.reshape(1, -1))[0]
            predicted = int(prediction)

            # 예측값 범위 제한 (감정가의 10% ~ 100%)
            min_price = int(start_price * 0.10)  # 최소 10%
            max_price = int(start_price * 1.00)  # 최대 100%
            predicted = max(min_price, min(predicted, max_price))

            logger.info(f"AI 예측 완료 (36개 특성): {start_price:,}원 -> {predicted:,}원")
            return predicted
        else:
            # 모델이 없는 경우 기본 계산식 사용
            predicted = int(start_price * settings.DEFAULT_PROFIT_MARGIN)
            logger.warning(f"AI 모델 없음, 기본 계산 사용: {predicted:,}원")
            return predicted
    except Exception as e:
        logger.error(f"예측 실패: {e}", exc_info=True)
        return int(start_price * settings.DEFAULT_PROFIT_MARGIN)


def predict_price_advanced(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int = 1,
    bidders: int = 10,
    bidders_actual: int = None,
    second_price: int = 0,
    is_hard: int = 0,
    tag_count: int = 0,
    share_floor: int = 0,
    share_land: int = 0,
    debt_ratio: float = 0.0,
    lowest_bid_price: int = None  # ValueAuction API에서 받은 실제 최저입찰가
) -> int:
    """
    AI 모델을 사용하여 낙찰가 예측 (고급 버전 - 48개 특성 사용)
    v2 모델 사용, 통계 기반 fallback 포함

    Args:
        lowest_bid_price: ValueAuction API에서 받은 법원의 실제 최저입찰가
                         (None이면 경매회차에 따라 자동 계산)
    """
    # 물건종류별 평균 낙찰률 (실제 데이터 기반)
    RATE_MAP = {
        "기타": 0.559,      # 55.9%
        "아파트": 0.717,    # 71.7%
        "단독주택": 0.502,  # 50.2%
        "다세대": 0.804,    # 80.4%
        "오피스텔": 0.805,  # 80.5%
        "상가": 0.550,      # 추정 55%
        "토지": 0.550,      # 추정 55%
    }
    DEFAULT_RATE = 0.597  # 전체 평균 59.7%

    try:
        # v2 모델 활성화 (3.91% 오차율로 매우 정확함)
        use_model = True

        if use_model and model is not None:
            # 모델이 기대하는 특성 개수 확인
            try:
                expected_features = model.n_features_in_ if hasattr(model, 'n_features_in_') else 48
            except:
                expected_features = 48

            # 특성 개수에 따라 적절한 함수 선택
            if expected_features == 58:
                # v4 모델: 58개 특성 (v3 + 패턴 특성)
                features = create_features_v4(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual or bidders, share_floor, share_land, debt_ratio,
                    second_price,
                    pattern_property_round=pattern_property_round,
                    pattern_region=pattern_region,
                    pattern_complex=pattern_complex,
                    lowest_bid_price=lowest_bid_price  # 실제 최저입찰가 전달
                )
                logger.info(f"v4 모델 사용 (58개 특성, 패턴 포함)")
            elif expected_features == 53:
                # v3 모델: 53개 특성
                features = create_features_v3(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual or bidders, share_floor, share_land, debt_ratio,
                    second_price,
                    lowest_bid_price=lowest_bid_price  # 실제 최저입찰가 전달
                )
                logger.info(f"v3 모델 사용 (53개 특성)")
            elif expected_features > 48:
                # 고도화 모델: 93개 특성 사용
                features = create_features_enhanced(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual or bidders, second_price, is_hard, tag_count,
                    share_floor, share_land, debt_ratio
                )
                logger.info(f"고도화 모델 사용 (88개 특성)")
            else:
                # 기존 v2 모델: 48개 특성 사용
                features = create_features_v2(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual or bidders, second_price, is_hard, tag_count,
                    share_floor, share_land, debt_ratio
                )
                logger.info(f"v2 모델 사용 (48개 특성)")

            # AI 모델 예측
            prediction = model.predict(features.reshape(1, -1))[0]
            predicted = int(prediction)

            # 예측값 범위 제한 강화 (감정가의 40% ~ 105%)
            # 학습 데이터와 동일한 범위로 제한하여 비현실적 예측 방지
            min_price_val = int(start_price * 0.40)  # 최소 40% (극단적 저가 방지)
            max_price_val = int(start_price * 1.05)  # 최대 105% (감정가 초과 방지)
            predicted = max(min_price_val, min(predicted, max_price_val))

            logger.info(f"AI 모델 예측 완료 ({expected_features}개 특성): {start_price:,}원 -> {predicted:,}원")
            return predicted
        else:
            # 통계 기반 예측 사용 (fallback)
            rate = RATE_MAP.get(property_type, DEFAULT_RATE)
            predicted = int(start_price * rate)
            logger.info(f"통계 기반 예측 완료: {start_price:,}원 -> {predicted:,}원 (낙찰률: {rate*100:.1f}%)")
            return predicted
    except Exception as e:
        logger.error(f"고급 예측 실패: {e}", exc_info=True)
        # 에러 시에도 통계 기반 사용
        rate = RATE_MAP.get(property_type, DEFAULT_RATE)
        return int(start_price * rate)


# -----------------------------
# 3. 국토교통부 실거래가 API
# -----------------------------

# 주요 지역 법정동 코드 (앞 5자리: 시군구 또는 읍면동 코드)
# 동(洞) 단위 코드를 구(區) 단위보다 우선 매칭하기 위해 먼저 정의
LAWD_CD_MAP: Dict[str, str] = {
    # 인천 - 동 단위 (연수구 산하)
    "송도동": "28185",  # 인천 연수구 송도동
    "옥련동": "28177",  # 인천 연수구 옥련동
    "동춘동": "28177",  # 인천 연수구 동춘동
    "선학동": "28177",  # 인천 연수구 선학동
    # 인천 - 동 단위 (남동구 산하)
    "구월동": "28200",  # 인천 남동구 구월동
    "간석동": "28200",  # 인천 남동구 간석동
    "만수동": "28200",  # 인천 남동구 만수동
    # 서울
    "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200",
    "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290",
    "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380",
    "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500",
    "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590",
    "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710",
    "강동구": "11740",
    # 인천 - 구 단위
    "중구": "28110", "동구": "28120", "미추홀구": "28140", "연수구": "28177",
    "남동구": "28200", "부평구": "28237", "계양구": "28245", "서구": "28260",
    "강화군": "28710", "옹진군": "28720",
    # 경기
    "수원시": "41110", "성남시": "41130", "의정부시": "41150", "안양시": "41170",
    "부천시": "41190", "광명시": "41210", "평택시": "41220", "동두천시": "41250",
    "안산시": "41270", "고양시": "41290", "과천시": "41290", "구리시": "41310",
    "남양주시": "41360", "오산시": "41370", "시흥시": "41390", "군포시": "41410",
    "의왕시": "41430", "하남시": "41450", "용인시": "41460", "파주시": "41480",
    "이천시": "41500", "안성시": "41550", "김포시": "41570", "화성시": "41590",
    "광주시": "41610", "양주시": "41630", "포천시": "41650", "여주시": "41670",
    # 경상북도
    "포항시 남구": "47111", "포항시 북구": "47113",
    "경주시": "47130", "김천시": "47150", "안동시": "47170", "구미시": "47190",
    "영주시": "47210", "영천시": "47230", "상주시": "47250", "문경시": "47280",
    "경산시": "47290",
    # 부산
    "중구": "26110", "서구": "26140", "동구": "26170", "영도구": "26200",
    "부산진구": "26230", "동래구": "26260", "남구": "26290", "북구": "26320",
    "해운대구": "26350", "사하구": "26380", "금정구": "26410", "강서구": "26440",
    "연제구": "26470", "수영구": "26500", "사상구": "26530",
    # 대구
    "중구": "27110", "동구": "27140", "서구": "27170", "남구": "27200",
    "북구": "27230", "수성구": "27260", "달서구": "27290",
    # 대전
    "동구": "30110", "중구": "30140", "서구": "30170", "유성구": "30200", "대덕구": "30230",
    # 광주
    "동구": "29110", "서구": "29140", "남구": "29155", "북구": "29170", "광산구": "29200",
    # 울산
    "중구": "31110", "남구": "31140", "동구": "31170", "북구": "31200", "울주군": "31710",
}

def extract_lawd_cd_from_address(address: str) -> Optional[str]:
    """
    주소 문자열에서 법정동 코드(앞 5자리) 추출
    동(洞) 단위를 우선 매칭 후, 없으면 구(區) 단위 매칭
    예: "인천광역시 연수구 송도과학로27번길 70 (송도동,롯데캐슬)" → "28185" (송도동)
    """
    if not address:
        return None

    # 1단계: 동(洞) 단위 우선 매칭 (더 세밀한 지역)
    # 송도동, 옥련동 등 "동"으로 끝나는 이름 먼저 찾기
    for location, code in LAWD_CD_MAP.items():
        if location.endswith("동") and location in address:
            logger.info(f"동 단위 매칭: {location} → {code}")
            return code

    # 2단계: 구/군/시 단위 매칭 (긴 이름부터 매칭하여 "남동구"가 "동구"보다 먼저 매칭되도록)
    # 길이가 긴 순서대로 정렬
    sorted_districts = sorted(
        [(d, c) for d, c in LAWD_CD_MAP.items() if not d.endswith("동")],
        key=lambda x: len(x[0]),
        reverse=True
    )

    for district, code in sorted_districts:
        if district in address:
            # 중복 이름 방지: 광주시(경기) vs 광주광역시 등
            # 앞에 나타나는 시/도 이름으로 필터
            if district == "중구":
                if "서울" in address: return "11140"
                if "인천" in address: return "28110"  # 인천 중구
                if "부산" in address: return "26110"
                if "대구" in address: return "27110"
                if "대전" in address: return "30140"
                if "울산" in address: return "31110"
                if "광주" in address: return "29110"
            elif district == "서구":
                if "인천" in address: return "28260"
                if "부산" in address: return "26140"
                if "대전" in address: return "30170"
                if "광주" in address: return "29140"
                if "울산" in address: return "31170"
                if "대구" in address: return "27170"
            elif district == "동구":
                if "인천" in address: return "28120"
                if "부산" in address: return "26170"
                if "대전" in address: return "30110"
                if "광주" in address: return "29110"
                if "울산" in address: return "31170"
                if "대구" in address: return "27140"
            elif district == "강서구":
                if "서울" in address: return "11500"
                if "부산" in address: return "26440"
            elif district == "강남구":
                if "서울" in address: return "11680"
            else:
                logger.info(f"구/시 단위 매칭: {district} → {code}")
                return code
    return None


def get_real_transaction(
    lawd_cd: str,
    deal_ymd: str,
    api_key: Optional[str] = None,
    apt_name: str = "",
    area: float = 0.0
) -> list:
    """
    국토교통부 아파트 매매 실거래가 상세자료 API 조회 (XML 응답)
    - apt_name: 아파트 단지명 (필터링용)
    - area: 전용면적 ㎡ (±5㎡ 범위로 필터링)
    """
    if api_key is None:
        api_key = settings.ODCLOUD_API_KEY

    if not api_key:
        logger.warning("국토부 API 키 미설정 - 실거래가 조회 불가")
        return []

    import xml.etree.ElementTree as ET

    all_items = []
    try:
        logger.info(f"실거래가 조회: lawd_cd={lawd_cd}, deal_ymd={deal_ymd}, apt={apt_name}, area={area}")
        # 일반 인증키는 URL에 직접 포함 (requests params= 사용 시 재인코딩 문제)
        url = (
            f"{settings.REALTRADE_API_URL}"
            f"?serviceKey={api_key}"
            f"&LAWD_CD={lawd_cd}"
            f"&DEAL_YMD={deal_ymd}"
            f"&numOfRows=100"
            f"&pageNo=1"
        )
        res = requests.get(url, timeout=settings.REQUEST_TIMEOUT)

        if res.status_code != 200:
            logger.warning(f"실거래가 API 오류: {res.status_code}")
            return []

        root = ET.fromstring(res.text)
        result_code = root.findtext('.//resultCode', '')
        # 성공 코드: 00, 000, 0000, 빈 문자열
        if result_code and result_code not in ('00', '000', '0000'):
            result_msg = root.findtext('.//resultMsg', '')
            logger.warning(f"실거래가 API 오류 코드: {result_code} - {result_msg}")
            return []

        items = root.findall('.//item')
        logger.info(f"실거래가 원본 건수: {len(items)}건")

        for item in items:
            item_apt = item.findtext('aptNm', '').strip()
            item_area_str = item.findtext('excluUseAr', '0').strip()
            item_price_str = item.findtext('dealAmount', '0').strip().replace(',', '')
            item_floor = item.findtext('floor', '').strip()
            item_year = item.findtext('dealYear', '').strip()
            item_month = item.findtext('dealMonth', '').strip()
            item_day = item.findtext('dealDay', '').strip()

            try:
                item_area = float(item_area_str)
                item_price = int(item_price_str) * 10000  # 만원 → 원
            except (ValueError, TypeError):
                continue

            # 단지명 필터 (지정된 경우)
            if apt_name and apt_name not in item_apt and item_apt not in apt_name:
                # 일부 이름 포함 여부도 확인
                apt_keywords = [w for w in apt_name.split() if len(w) >= 2]
                if not any(kw in item_apt for kw in apt_keywords):
                    continue

            # 면적 필터: ±10㎡ 이내 (지정된 경우)
            if area > 0 and abs(item_area - area) > 10:
                continue

            all_items.append({
                "아파트명": item_apt,
                "전용면적": item_area,
                "거래금액": item_price,
                "층": item_floor,
                "거래일": f"{item_year}-{item_month.zfill(2)}-{item_day.zfill(2)}",
            })

        logger.info(f"실거래가 필터링 후: {len(all_items)}건 (단지={apt_name}, 면적={area}㎡)")
        return all_items

    except requests.RequestException as e:
        logger.error(f"실거래가 API 요청 실패: {e}")
        return []
    except Exception as e:
        logger.error(f"실거래가 파싱 오류: {e}", exc_info=True)
        return []


def calc_market_price(transactions: list, appraisal_price: int = 0) -> int:
    """
    실거래 목록에서 평균 거래금액 계산 (최근 3건 기준)
    - appraisal_price: 감정가 (이상치 제거용)
    """
    if not transactions:
        return 0
    prices = [t["거래금액"] for t in transactions if t.get("거래금액", 0) > 0]
    if not prices:
        return 0

    # 감정가가 있으면 이상치 제거: 감정가의 50%~150% 범위만 포함 (강화된 검증)
    if appraisal_price > 0:
        min_price = appraisal_price * 0.5  # 50% 이하는 이상치
        max_price = appraisal_price * 1.5  # 150% 이상은 이상치
        filtered_prices = [p for p in prices if min_price <= p <= max_price]
        if filtered_prices:
            prices = filtered_prices
            logger.info(f"실거래가 이상치 제거: {len(transactions)}건 → {len(prices)}건 (감정가의 50~150% 범위)")
        else:
            # 모든 실거래가가 이상치인 경우 0 반환 (감정가 사용 안 함)
            logger.warning(f"실거래가 {len(prices)}건 모두 이상치 (감정가 {appraisal_price:,}원 기준) - 실거래가 신뢰 불가")
            return 0  # 이상치인 경우 실거래가 사용 안 함

    # 최근 3건 평균
    recent = prices[:3]
    return int(sum(recent) / len(recent))


# -----------------------------
# 4. 예상 수익률 계산
# -----------------------------
def calc_profit_rate(predicted_price: int, market_price: int) -> Dict[str, Any]:
    """
    예상 수익률 계산
    """
    if predicted_price <= 0:
        return {"예상수익": 0, "예상수익률": 0.0}

    profit = market_price - predicted_price
    rate = (profit / predicted_price) * 100

    return {
        "예상수익": profit,
        "예상수익률": round(rate, 2),
        "예상낙찰가": predicted_price,
        "시장가": market_price
    }


# -----------------------------
# 5. FastAPI 엔드포인트
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    메인 페이지
    """
    try:
        html_path = Path("static/index.html")
        if html_path.exists():
            return html_path.read_text(encoding="utf-8")
        else:
            return """
            <html>
                <head><title>AI 경매 예측</title></head>
                <body>
                    <h1>AI 기반 경매 낙찰가 예측 시스템</h1>
                    <p>API 문서: <a href="/docs">/docs</a></p>
                </body>
            </html>
            """
    except Exception as e:
        logger.error(f"메인 페이지 로드 실패: {e}")
        return "<h1>시스템 오류</h1>"


@app.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    """
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_load_time": model_load_time.strftime('%Y-%m-%d %H:%M:%S') if model_load_time else None,
        "version": settings.APP_VERSION
    }


@app.get("/accuracy")
async def get_accuracy_dashboard(
    mobile: bool = Query(False, description="모바일 최적화 응답 (핵심 통계만)")
):
    """
    정확도 대시보드 데이터 조회

    - 전체 예측 통계
    - 최근 예측 목록
    - 정확도 지표
    - mobile=true: 핵심 통계만 반환 (경량화)
    """
    try:
        # 통계 조회
        stats = db.get_accuracy_stats(days=30)

        # v4 모델 정보 추가
        stats['model_info'] = {
            'version': 'v4',
            'features': 58,
            'trained_on': '1,641 samples',
            'test_mae': '2,890,000원',
            'test_r2': 0.9994,
            'test_error_rate': 1.21,
            'improvements': [
                'ValueAuction API 연동으로 실제 최저입찰가 반영',
                '58개 특성 (v3 53개 + 과거 패턴 5개)',
                '물건종류/지역/단지별 낙찰 패턴 학습',
                '투자 매력도 분석 및 권리분석 데이터 활용'
            ]
        }

        if mobile:
            # 모바일: 핵심 통계만 반환 (경량화)
            return {
                "success": True,
                "stats": {
                    "total_predictions": stats.get('total_predictions', 0),
                    "verified_predictions": stats.get('verified_predictions', 0),
                    "avg_error_rate": stats.get('avg_error_rate', 0),
                    "verification_rate": stats.get('verification_rate', 0)
                }
            }
        else:
            # 웹: 전체 데이터 반환
            # 최근 예측 목록 (검증된 것만)
            recent_verified = db.get_recent_predictions(limit=20, verified_only=True)

            # 미검증 예측 목록
            unverified = db.get_unverified_predictions(limit=10)

            return {
                "success": True,
                "stats": stats,
                "recent_verified": recent_verified,
                "unverified_count": len(unverified),
                "unverified_samples": unverified[:5]  # 샘플 5개만
            }

    except Exception as e:
        logger.error(f"정확도 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify-result")
@limiter.limit("20/minute")
async def verify_prediction_result(
    request: Request,
    case_no: str = Query(..., description="사건번호"),
    actual_price: int = Query(..., description="실제 낙찰가"),
    actual_date: str = Query(None, description="낙찰 날짜 (YYYY-MM-DD)")
):
    """
    실제 낙찰 결과 업데이트

    - case_no: 사건번호
    - actual_price: 실제 낙찰가
    - actual_date: 낙찰 날짜 (선택)
    """
    try:
        success = db.update_actual_result(case_no, actual_price, actual_date)

        if success:
            return {
                "success": True,
                "message": "실제 낙찰가가 업데이트되었습니다",
                "case_no": case_no,
                "actual_price": actual_price
            }
        else:
            raise HTTPException(status_code=404, detail="예측 기록을 찾을 수 없습니다")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"낙찰가 업데이트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auction")
async def auction(
    case_no: str = Query(..., description="경매 사건 번호 (숫자만 입력 가능)"),
    lawd_cd: str = Query(None, description="지역 코드 (5자리)"),
    deal_ymd: str = Query(None, description="거래 연월 (YYYYMM)"),
    api_key: str = Query(None, description="국토교통부 API 키"),
    bidders: int = Query(None, description="예상 입찰자 수"),
    site: str = Query(None, description="담당법원명 (중복 사건번호 구분용)")
):
    """
    경매 물건 분석 및 낙찰가 예측

    - **case_no**: 경매 사건 번호 (숫자만 입력, 예: 202400001 → 2024타경00001)
    - **lawd_cd**: 법정동 코드 (선택, 실거래가 조회 시 필요)
    - **deal_ymd**: 거래 연월 (선택, 실거래가 조회 시 필요)
    - **api_key**: 국토교통부 API 키 (선택)
    - **bidders**: 예상 입찰자 수 (선택, 기본값: 10)
    """
    try:
        # 0. 사건번호 형식 변환 (숫자 → XXXX타경XXXXX)
        formatted_case_no = format_case_number(case_no)
        logger.info(f"사건번호 변환: {case_no} → {formatted_case_no}")

        # 1. 경매 정보 조회
        auction_info = get_auction_item(formatted_case_no, site)
        start_price = auction_info["감정가_숫자"]

        # 2. AI 예측 낙찰가 (고급 버전 - 88개 특성 사용, 실제 경매 정보 활용)
        property_type = auction_info.get('물건종류', '아파트')
        region = auction_info.get('지역', '서울')
        area_raw = auction_info.get('면적', '85.0')
        try:
            area = float(str(area_raw).replace('㎡', '').strip()) if area_raw else 85.0
            if area <= 0:
                area = 85.0
        except (ValueError, AttributeError):
            area = 85.0
        auction_round = auction_info.get('경매회차', 1)
        if not isinstance(auction_round, int):
            try:
                auction_round = int(auction_round)
            except (ValueError, TypeError):
                auction_round = 1

        # ValueAuction API에서 받은 실제 최저입찰가 가져오기
        actual_lowest_bid = auction_info.get('최저입찰가', 0)

        predicted_price = predict_price_advanced(
            start_price=start_price,
            property_type=property_type,
            region=region,
            area=area,
            auction_round=auction_round,
            bidders=bidders or 10,
            lowest_bid_price=actual_lowest_bid,  # 실제 최저입찰가 전달
        )

        # 3. 실거래가 데이터 가져오기
        market_price = 0  # 0 = 미조회 상태
        transactions = []

        # 아파트명 추출 (단지명 필터용)
        address = auction_info.get('소재지', '')
        apt_name_guess = ""
        # 괄호 안 단지명 추출: "... (송도동,롯데캐슬)" → "롯데캐슬"
        import re as _re
        paren_match = _re.search(r'\(([^,)]+),([^)]+)\)', address)
        if paren_match:
            apt_name_guess = paren_match.group(2).strip()
        if not apt_name_guess:
            # 주소 마지막 단어에서 추출 시도
            parts = address.split()
            for part in reversed(parts):
                if len(part) >= 3 and any(c in part for c in ['아파트', '캐슬', '파크', '힐스', '자이', '래미안', '푸르지오', '아이파크', '롯데', '현대']):
                    apt_name_guess = part
                    break

        # 브랜드명만 추출 (매칭 범위 확대)
        # "롯데캐슬" → "롯데", "래미안자이" → "래미안" 등
        if apt_name_guess:
            brand_names = ['롯데', '래미안', '푸르지오', '자이', '힐스테이트', '아이파크',
                          '더샵', '센트레빌', '현대', '삼성', 'SK', '두산', '대우']
            for brand in brand_names:
                if brand in apt_name_guess:
                    apt_name_guess = brand
                    logger.info(f"브랜드명 추출: {brand}")
                    break

        # lawd_cd 자동 추출 (주소 기반)
        effective_lawd_cd = lawd_cd
        if not effective_lawd_cd and address:
            effective_lawd_cd = extract_lawd_cd_from_address(address)
            if effective_lawd_cd:
                logger.info(f"주소에서 lawd_cd 자동 추출: {effective_lawd_cd} (주소: {address[:30]}...)")

        # deal_ymd 자동 설정 (최근 3개월 순차 시도)
        if effective_lawd_cd and settings.ODCLOUD_API_KEY:
            from datetime import datetime as _dt
            today = _dt.today()
            months_to_try = []
            for delta in range(0, 4):  # 이번달 포함 최근 4개월
                m = today.month - delta
                y = today.year
                while m <= 0:
                    m += 12
                    y -= 1
                months_to_try.append(f"{y}{m:02d}")

            effective_deal_ymd = deal_ymd or months_to_try[0]
            area_float = area if area > 0 else 0.0

            for ymd in (months_to_try if not deal_ymd else [deal_ymd]):
                transactions = get_real_transaction(
                    lawd_cd=effective_lawd_cd,
                    deal_ymd=ymd,
                    api_key=api_key,
                    apt_name=apt_name_guess,
                    area=area_float
                )
                if transactions:
                    logger.info(f"실거래가 {ymd} 기준 {len(transactions)}건 조회 성공")
                    break

            if transactions:
                market_price = calc_market_price(transactions, start_price)
                logger.info(f"실거래가 평균: {market_price:,}원 ({len(transactions)}건 평균)")

        # 실거래가 미조회 시 감정가로 fallback
        real_transaction_note = ""
        real_transaction_warning = ""  # 경고 메시지

        if market_price <= 0:
            market_price = start_price

        # 실거래가 안내 메시지 생성
        if effective_lawd_cd and settings.ODCLOUD_API_KEY:
            if transactions:
                real_transaction_note = f"최근 4개월 실거래 {len(transactions)}건 평균"
                # 실거래가 신뢰도 경고 추가
                real_transaction_warning = "※ 실거래가는 참고용이며, 정확한 시세는 네이버 부동산, KB부동산, 한국감정원 등에서 확인하세요."
            else:
                real_transaction_note = "최근 4개월 실거래 데이터 없음 (감정가 사용)"
                real_transaction_warning = "※ 해당 물건의 실거래 데이터가 없습니다. 네이버 부동산 등에서 직접 시세를 확인하세요."
        else:
            if not settings.ODCLOUD_API_KEY:
                real_transaction_note = "실거래가 API 키 미설정"
            elif not effective_lawd_cd:
                real_transaction_note = "법정동 코드 추출 실패"
            real_transaction_warning = "※ 실거래가 조회 불가. 네이버 부동산, KB부동산 등에서 직접 시세를 확인하세요."

        # 4. 예상 수익률 계산
        profit_result = calc_profit_rate(predicted_price, market_price)

        # 4-1. 고급 분석 데이터 계산 (전체분석 탭용)
        # ValueAuction API에서 받아온 실제 최저입찰가 사용 (법원이 실제로 정한 금액)
        lowest_bid_price = auction_info.get('최저입찰가', 0)
        # fallback: API에서 최저입찰가를 못 받았을 경우에만 계산식 사용
        if not lowest_bid_price or lowest_bid_price == 0:
            lowest_bid_price = calc_lowest_price_by_round(start_price, auction_round)
            logger.warning(f"최저입찰가 API 조회 실패 - 계산식 사용: {lowest_bid_price:,}원 (감정가의 {(lowest_bid_price/start_price*100):.1f}%)")
        else:
            logger.info(f"ValueAuction API에서 실제 최저입찰가 사용: {lowest_bid_price:,}원 (감정가의 {(lowest_bid_price/start_price*100):.1f}%)")

        lowest_bid_ratio = (lowest_bid_price / start_price * 100) if start_price > 0 else 0
        predicted_ratio = (predicted_price / start_price * 100) if start_price > 0 else 0

        # ✅ 투자 매력도 점수 계산 (0-100점, 높을수록 매력적)
        investment_score = 0  # 총점
        score_details = []    # 세부 항목

        # 1. 가격 메리트 (40점) - AI 예측가 vs 최저입찰가
        price_merit = 0
        if lowest_bid_price > 0:
            price_ratio = predicted_price / lowest_bid_price
            if price_ratio >= 1.20:
                price_merit = 40
                price_level = "매우 높음"
            elif price_ratio >= 1.10:
                price_merit = 35
                price_level = "높음"
            elif price_ratio >= 1.00:
                price_merit = 30
                price_level = "적정"
            elif price_ratio >= 0.95:
                price_merit = 20
                price_level = "보통"
            elif price_ratio >= 0.90:
                price_merit = 10
                price_level = "낮음"
            else:
                price_merit = 0
                price_level = "매우 낮음"
        else:
            price_merit = 20
            price_level = "정보 없음"

        investment_score += price_merit
        score_details.append({
            "category": "가격 메리트",
            "score": price_merit,
            "max_score": 40,
            "level": price_level,
            "description": f"AI 예측가가 최저입찰가 대비 {((price_ratio-1)*100):.1f}%" if lowest_bid_price > 0 else "정보 없음"
        })

        # 2. 유찰 메리트 (25점) - 유찰 횟수 (할인 기회)
        failure_merit = 0
        if auction_round == 1:
            failure_merit = 15
            failure_level = "첫 경매"
        elif auction_round == 2:
            failure_merit = 25
            failure_level = "최적 (1회 유찰)"
        elif auction_round == 3:
            failure_merit = 22
            failure_level = "좋음 (2회 유찰)"
        elif auction_round == 4:
            failure_merit = 18
            failure_level = "보통 (3회 유찰)"
        else:
            failure_merit = 15
            failure_level = "관심 필요"

        investment_score += failure_merit
        score_details.append({
            "category": "유찰 메리트",
            "score": failure_merit,
            "max_score": 25,
            "level": failure_level,
            "description": f"{auction_round}회차 경매"
        })

        # 3. 시세 대비 할인율 (25점)
        discount_merit = 0
        if market_price > 0 and lowest_bid_price > 0:
            discount_rate = (market_price - lowest_bid_price) / market_price * 100
            if discount_rate >= 30:
                discount_merit = 25
                discount_level = "최고 할인"
            elif discount_rate >= 20:
                discount_merit = 20
                discount_level = "큰 할인"
            elif discount_rate >= 10:
                discount_merit = 15
                discount_level = "보통 할인"
            elif discount_rate >= 5:
                discount_merit = 10
                discount_level = "약간 할인"
            elif discount_rate >= 0:
                discount_merit = 5
                discount_level = "시세 수준"
            else:
                discount_merit = 0
                discount_level = "시세 초과"
        else:
            discount_merit = 12
            discount_rate = 0
            discount_level = "정보 없음"

        investment_score += discount_merit
        score_details.append({
            "category": "시세 대비 할인율",
            "score": discount_merit,
            "max_score": 25,
            "level": discount_level,
            "description": f"시세 대비 {discount_rate:.1f}% 할인" if market_price > 0 else "실거래가 정보 없음"
        })

        # 4. 권리관계 안정성 (10점)
        rights_merit = 10  # 기본 만점
        rights_issues = []

        # ValueAuction에서 권리분석 정보 가져오기
        rights_info = auction_info.get('권리분석', {})
        claim_ratio = rights_info.get('청구금액비율', 0)
        has_share_floor = rights_info.get('공유지분_건물', False)
        has_share_land = rights_info.get('공유지분_토지', False)

        # 청구금액 비율에 따른 감점
        if claim_ratio >= 0.7:
            rights_merit -= 8
            rights_issues.append("청구금액 높음 (-8점)")
        elif claim_ratio >= 0.5:
            rights_merit -= 5
            rights_issues.append("청구금액 다소 높음 (-5점)")
        elif claim_ratio >= 0.3:
            rights_merit -= 3
            rights_issues.append("청구금액 보통 (-3점)")

        # 공유지분 감점
        if has_share_floor or has_share_land:
            rights_merit -= 3
            rights_issues.append("공유지분 있음 (-3점)")

        rights_merit = max(0, rights_merit)
        investment_score += rights_merit

        rights_level = "우수" if rights_merit >= 8 else "보통" if rights_merit >= 5 else "주의"
        score_details.append({
            "category": "권리관계 안정성",
            "score": rights_merit,
            "max_score": 10,
            "level": rights_level,
            "description": ", ".join(rights_issues) if rights_issues else "양호"
        })

        # 총점 범위 제한
        investment_score = max(0, min(100, investment_score))

        # 투자 매력도 등급 결정
        if investment_score >= 80:
            investment_level = "매우 높음"
            investment_color = "excellent"
        elif investment_score >= 65:
            investment_level = "높음"
            investment_color = "good"
        elif investment_score >= 50:
            investment_level = "보통"
            investment_color = "normal"
        elif investment_score >= 35:
            investment_level = "낮음"
            investment_color = "low"
        else:
            investment_level = "매우 낮음"
            investment_color = "very_low"

        # AI 신뢰도 계산 (실제 DB 통계 사용)
        try:
            accuracy_stats = db.get_accuracy_stats(days=30)
            verified_count = accuracy_stats.get('verified_predictions', 0)
            avg_error = accuracy_stats.get('avg_error_rate', 1.21)

            # 검증된 예측 수에 따라 신뢰도 점수 계산
            if verified_count >= 100:
                base_score = 90
            elif verified_count >= 50:
                base_score = 85
            elif verified_count >= 20:
                base_score = 80
            else:
                base_score = 75

            # 오차율에 따라 점수 조정 (오차율이 낮을수록 높은 점수)
            if avg_error < 2.0:
                score_adjustment = 5
            elif avg_error < 3.0:
                score_adjustment = 0
            elif avg_error < 5.0:
                score_adjustment = -5
            else:
                score_adjustment = -10

            final_score = min(100, max(0, base_score + score_adjustment))
            stars = min(5, max(1, round(final_score / 20)))

            ai_confidence = {
                "score": final_score,
                "stars": stars,
                "training_samples": 1641,  # v4 모델 학습 샘플
                "avg_error_rate": avg_error,
                "model_version": "v4"
            }
        except Exception as e:
            logger.warning(f"AI 신뢰도 통계 조회 실패, 기본값 사용: {e}")
            # 실패 시 기본값
            ai_confidence = {
                "score": 85,
                "stars": 4,
                "training_samples": 1641,
                "avg_error_rate": 1.21,
                "model_version": "v4"
            }

        # 입찰 전략 추천 계산 (현실적인 전략)
        bidding_strategy = {
            "current_round": auction_round,
            "current_minimum": lowest_bid_price,
            "predicted_price": predicted_price,
            "recommendation": "bid_now",
            "wait_until_round": None,
            "potential_savings": 0,
            "message": "현재 회차 입찰 권장"
        }

        # 회차별 최저가 계산 (표준 경매 감정가율)
        round_ratios = {
            1: 1.00,
            2: 0.80,
            3: 0.64,
            4: 0.512,
            5: 0.4096
        }

        # 다음 회차 계산 (현재 + 1회차만 고려 - 현실성 중시)
        next_round = auction_round + 1
        if next_round <= 5:
            next_ratio = round_ratios.get(next_round, 0.4096)
            next_min_bid = int(start_price * next_ratio)
            potential_savings = lowest_bid_price - next_min_bid
        else:
            next_min_bid = lowest_bid_price
            potential_savings = 0

        # 전략 결정 로직 (현실적 판단)
        price_diff = predicted_price - lowest_bid_price
        price_diff_pct = (price_diff / lowest_bid_price * 100) if lowest_bid_price > 0 else 0

        # ✅ 최우선 체크: AI 예측가가 최저입찰가보다 낮으면 유찰 대기
        if predicted_price < lowest_bid_price:
            # 다음 회차 정보 설정
            if next_round <= 5 and predicted_price >= next_min_bid:
                savings = lowest_bid_price - next_min_bid
                bidding_strategy["recommendation"] = "wait_for_next"
                bidding_strategy["wait_until_round"] = next_round
                bidding_strategy["potential_savings"] = savings
                bidding_strategy["message"] = "유찰 대기 권장"
            else:
                # 다음 회차에도 입찰 불가한 경우
                bidding_strategy["recommendation"] = "cannot_bid"
                bidding_strategy["message"] = "입찰 불가 (AI 예측가가 낮음)"

        elif predicted_price >= lowest_bid_price * 1.05:
            # AI 예측가가 현재 최저가보다 5% 이상 높음 → 입찰 적정
            bidding_strategy["recommendation"] = "bid_now"
            bidding_strategy["message"] = f"현재 회차 입찰 적정 (AI 예측가가 최저가 대비 {price_diff_pct:.1f}% 높음)"

        elif predicted_price >= lowest_bid_price:
            # AI 예측가가 최저가 이상 ~ 105% 미만 → 입찰 가능
            bidding_strategy["recommendation"] = "bid_now"
            bidding_strategy["message"] = f"현재 회차 입찰 적정 (AI 예측가가 최저입찰가 범위 내, {price_diff_pct:.1f}% 높음)"

        # 여기까지 오면 predicted_price >= lowest_bid_price 이므로 입찰 가능

        # 5. 데이터베이스에 예측 저장
        try:
            db.save_prediction({
                'case_no': formatted_case_no,
                '물건번호': auction_info.get('물건번호') or formatted_case_no,
                '사건번호': auction_info.get('사건번호') or formatted_case_no,
                '감정가': start_price,
                '물건종류': auction_info.get('물건종류'),
                '지역': auction_info.get('지역'),
                '면적': float(auction_info.get('면적', '0').replace('㎡', '')) if isinstance(auction_info.get('면적'), str) else auction_info.get('면적', 0),
                '경매회차': auction_info.get('경매회차', 1),
                '입찰자수': bidders or 10,
                'predicted_price': predicted_price,
                'expected_profit': profit_result.get('예상수익', 0),
                'profit_rate': profit_result.get('예상수익률', 0),
                'prediction_mode': 'full_analysis',
                'model_used': model is not None,
                'source': 'auction_analysis'
            })
        except Exception as e:
            logger.warning(f"예측 저장 실패 (계속 진행): {e}")

        # 6. 결과 반환
        return JSONResponse(content={
            "success": True,
            "data": {
                "auction_info": auction_info,
                "predicted_price": predicted_price,
                "predicted_price_formatted": f"{predicted_price:,}원",
                "market_price": market_price,
                "market_price_formatted": f"{market_price:,}원",
                "profit_analysis": profit_result,
                "transactions_count": len(transactions),
                "real_transaction_note": real_transaction_note,
                "real_transaction_warning": real_transaction_warning,
                "model_used": model is not None,
                # 고급 분석 데이터 (전체분석 탭용)
                "advanced_analysis": {
                    "lowest_bid_price": lowest_bid_price,
                    "lowest_bid_ratio": round(lowest_bid_ratio, 2),
                    "predicted_ratio": round(predicted_ratio, 2),
                    "investment_score": {
                        "total_score": investment_score,
                        "level": investment_level,
                        "color": investment_color,
                        "details": score_details
                    },
                    "ai_confidence": ai_confidence,
                    "bidding_strategy": bidding_strategy
                }
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예측 처리 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@app.get("/predict")
@limiter.limit("30/minute")
async def predict_only(
    request: Request,
    start_price: int = Query(..., description="감정가 (원)"),
    property_type: str = Query(None, description="물건종류 (아파트/다세대/오피스텔/단독주택/상가)"),
    region: str = Query(None, description="지역 (서울/경기/인천/부산/대구/기타)"),
    area: float = Query(None, description="면적 (㎡)"),
    auction_round: int = Query(1, description="경매 회차"),
    bidders: int = Query(10, description="예상 입찰자 수"),
    bidders_actual: int = Query(None, description="실제 입찰자 수 (선택)"),
    second_price: int = Query(0, description="2등 입찰가 (선택)"),
    is_hard: int = Query(0, description="권리분석 복잡도 (0/1, 선택)"),
    tag_count: int = Query(0, description="권리사항 태그 수 (선택)"),
    share_floor: int = Query(0, description="공유지분 건물 여부 (0/1, 선택)"),
    share_land: int = Query(0, description="공유지분 토지 여부 (0/1, 선택)"),
    debt_ratio: float = Query(0.0, description="청구금액 비율 (선택, 0.0~1.0)"),
    mobile: bool = Query(False, description="모바일 최적화 응답 (간소화)")
):
    """
    낙찰가 예측 API (AI 모델 v2 - 48개 특성 활용)

    - **간단 예측**: start_price, bidders만 입력 → 기본값 사용 (아파트, 서울, 85㎡)
    - **맞춤 예측**: 모든 파라미터 입력 → 사용자 지정 값으로 정확한 예측

    **v2 모델: 48개 특성, 3.91% 평균 오차율**
    """
    try:
        # 캐시 확인 (동일한 입력에 대해 1시간 동안 캐시 사용)
        cache_key = get_cache_key(
            start_price, property_type, region, area, auction_round, bidders,
            bidders_actual, second_price, is_hard, tag_count, share_floor, share_land, debt_ratio, mobile
        )
        cached_result = get_from_cache(cache_key)
        if cached_result:
            cached_result["cached"] = True
            return cached_result

        # 맞춤 예측 (사용자가 상세 정보를 제공한 경우)
        if property_type and region and area:
            predicted = predict_price_advanced(
                start_price, property_type, region, area, auction_round, bidders,
                bidders_actual, second_price, is_hard, tag_count,
                share_floor, share_land, debt_ratio
            )
            mode = "맞춤 AI 예측 (사용자 지정값, 48개 특성, v2 모델)"
            used_defaults = False
        else:
            # 간단 예측 (기본값 사용)
            predicted = predict_price(start_price, bidders)
            mode = "간단 AI 예측 (기본값: 아파트, 서울, 85㎡, 36개 특성)"
            used_defaults = True

        # 예상 수익 계산
        expected_profit = start_price - predicted  # 감정가 - 예측 낙찰가
        profit_rate = (expected_profit / start_price * 100) if start_price > 0 else 0
        bid_ratio = (predicted / start_price * 100) if start_price > 0 else 0

        # 데이터베이스에 예측 저장
        try:
            db.save_prediction({
                'case_no': f"PREDICT-{int(datetime.now().timestamp())}",
                '감정가': start_price,
                '물건종류': property_type or "아파트",
                '지역': region or "서울",
                '면적': area or 85.0,
                '경매회차': auction_round,
                '입찰자수': bidders,
                'predicted_price': predicted,
                'expected_profit': expected_profit,
                'profit_rate': profit_rate,
                'prediction_mode': mode,
                'model_used': model is not None,
                'source': 'simple_predict'
            })
        except Exception as e:
            logger.warning(f"예측 저장 실패 (계속 진행): {e}")

        # 결과 생성
        if mobile:
            # 모바일 최적화 응답 (간소화, 클라이언트에서 포맷팅)
            result = {
                "success": True,
                "data": {
                    "start_price": start_price,
                    "predicted_price": predicted,
                    "expected_profit": expected_profit,
                    "profit_rate": round(profit_rate, 2),
                    "bid_ratio": round(bid_ratio, 2)
                },
                "input": {
                    "property_type": property_type or "아파트",
                    "region": region or "서울",
                    "area": area or 85.0,
                    "auction_round": auction_round,
                    "bidders": bidders
                },
                "cached": False
            }
        else:
            # 기존 웹 응답 (하위 호환성 유지)
            result = {
                "success": True,
                "start_price": start_price,
                "start_price_formatted": f"{start_price:,}원",
                "predicted_price": predicted,
                "predicted_price_formatted": f"{predicted:,}원",

                # 예상 수익 정보 (핵심)
                "expected_profit": expected_profit,
                "expected_profit_formatted": f"{expected_profit:,}원",
                "profit_rate": round(profit_rate, 2),
                "profit_rate_formatted": f"{profit_rate:.2f}%",

                # 낙찰률 (참고용)
                "bid_ratio": round(bid_ratio, 2),
                "bid_ratio_formatted": f"{bid_ratio:.2f}%",

                # 입력 정보
                "property_type": property_type if property_type else "아파트 (기본값)",
                "region": region if region else "서울 (기본값)",
                "area": area if area else 85.0,
                "auction_round": auction_round,
                "bidders": bidders,

                # 메타 정보
                "model_used": model is not None,
                "prediction_mode": mode,
                "used_defaults": used_defaults,
                "features_count": 48 if (property_type and region and area) else 36,
                "cached": False
            }

        # 결과를 캐시에 저장
        set_to_cache(cache_key, result)

        return result
    except ValueError as e:
        # 입력값 검증 에러
        handle_validation_error("입력 파라미터", str(e), "올바른 숫자 값을 입력해주세요")
    except AttributeError as e:
        # 모델이 로드되지 않은 경우
        if "model" in str(e).lower():
            handle_model_error(e)
        else:
            handle_server_error("예측 처리", e, APIError.PREDICTION_FAILED)
    except Exception as e:
        # 기타 모든 예측 에러
        handle_server_error("낙찰가 예측", e, APIError.PREDICTION_FAILED)


@app.post("/reload-model")
@limiter.limit("1/minute")
async def reload_model(request: Request):
    """
    AI 모델을 핫 리로드하는 엔드포인트
    재학습 후 서버를 재시작하지 않고 모델을 업데이트할 수 있습니다.
    """
    try:
        success, version = load_model()

        if success:
            return {
                "success": True,
                "message": "모델이 성공적으로 리로드되었습니다",
                "model_version": version,
                "load_time": model_load_time.strftime('%Y-%m-%d %H:%M:%S') if model_load_time else None,
                "model_loaded": model is not None
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="모델 파일을 찾을 수 없거나 로드에 실패했습니다"
            )
    except Exception as e:
        logger.error(f"모델 리로드 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model-status")
async def get_model_status():
    """
    현재 로드된 모델의 상태 정보를 반환합니다
    """
    return {
        "model_loaded": model is not None,
        "model_version": "v2" if model_v2_path.exists() and model is not None else "v1" if model is not None else None,
        "load_time": model_load_time.strftime('%Y-%m-%d %H:%M:%S') if model_load_time else None,
        "v2_path_exists": model_v2_path.exists(),
        "v1_path_exists": model_v1_path.exists()
    }


@app.get("/predictions")
@limiter.limit("30/minute")
async def get_predictions(
    request: Request,
    limit: int = Query(20, description="반환할 최대 결과 수 (기본: 20, 최대: 100)", ge=1, le=100),
    offset: int = Query(0, description="건너뛸 결과 수 (페이지네이션)", ge=0),
    verified_only: bool = Query(False, description="검증된 예측만 조회"),
    mobile: bool = Query(False, description="모바일 최적화 응답 (간소화)")
):
    """
    예측 히스토리 조회 (페이지네이션 지원)

    - limit: 최대 반환 개수 (기본 20, 최대 100)
    - offset: 건너뛸 개수 (페이지네이션용)
    - verified_only: true일 경우 실제 낙찰가가 입력된 검증된 예측만 반환
    - mobile: 간소화된 응답 (핵심 필드만 반환)
    """
    try:
        # 데이터베이스에서 예측 조회
        all_predictions = db.get_recent_predictions(limit=1000, verified_only=verified_only)

        # 페이지네이션 적용
        total_count = len(all_predictions)
        paginated_predictions = all_predictions[offset:offset + limit]

        if mobile:
            # 모바일: 핵심 필드만 반환
            simplified_predictions = []
            for pred in paginated_predictions:
                simplified_predictions.append({
                    "id": pred.get("id"),
                    "case_no": pred.get("case_no"),
                    "predicted_price": pred.get("predicted_price"),
                    "actual_price": pred.get("actual_price"),
                    "error_rate": pred.get("error_rate"),
                    "created_at": pred.get("created_at"),
                    "verified": pred.get("verified", 0) == 1
                })

            return {
                "success": True,
                "predictions": simplified_predictions,
                "count": len(simplified_predictions),
                "total": total_count,
                "offset": offset,
                "limit": limit,
                "has_more": (offset + limit) < total_count
            }
        else:
            # 웹: 전체 데이터 반환
            return {
                "success": True,
                "predictions": paginated_predictions,
                "count": len(paginated_predictions),
                "total": total_count,
                "offset": offset,
                "limit": limit,
                "has_more": (offset + limit) < total_count
            }

    except Exception as e:
        logger.error(f"예측 히스토리 조회 오류: {e}", exc_info=True)
        handle_server_error("예측 히스토리 조회", e, APIError.DATABASE_ERROR)


@app.get("/price-range-stats")
async def get_price_range_stats():
    """
    감정가 구간별 통계를 반환합니다
    파이프라인 실행 시 자동으로 업데이트되는 최신 통계입니다.
    """
    try:
        stats_file = Path("data/price_range_stats.json")

        if not stats_file.exists():
            # 파일이 없으면 분석 실행
            logger.info("구간별 통계 파일이 없습니다. 분석을 실행합니다...")
            import subprocess
            subprocess.run(["python", "analyze_by_price_range.py"], check=True)

        # JSON 파일 읽기
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats_data = json.load(f)

        return {
            "success": True,
            "data": stats_data
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="구간별 통계 파일을 찾을 수 없습니다. 먼저 analyze_by_price_range.py를 실행하세요."
        )
    except Exception as e:
        logger.error(f"구간별 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search-case")
@limiter.limit("30/minute")
async def search_case(
    request: Request,
    query: str = Query(..., description="검색할 사건번호 (부분 검색 가능)", min_length=1),
    limit: int = Query(10, description="반환할 최대 결과 수 (기본: 10, 최대: 100)", ge=1, le=100),
    offset: int = Query(0, description="건너뛸 결과 수 (페이지네이션)", ge=0),
    mobile: bool = Query(False, description="모바일 최적화 응답 (간소화)")
):
    """
    사건번호 검색 (자동완성 및 페이지네이션 지원)
    ValueAuction API를 사용하여 사건번호를 검색합니다.

    - limit: 최대 반환 개수 (기본 10, 최대 100)
    - offset: 건너뛸 개수 (페이지네이션용)
    - mobile: 간소화된 응답 (case_no만 반환)
    """
    try:
        logger.info(f"사건번호 검색: {query}, limit={limit}, offset={offset}")

        api_url = "https://valueauction.co.kr/api/search"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Content-Type": "application/json",
            "Referer": "https://valueauction.co.kr/",
            "Origin": "https://valueauction.co.kr"
        }

        payload = {
            "auctionType": "auction",
            "case": query
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            return {
                "success": False,
                "results": [],
                "message": "검색 실패"
            }

        data = response.json()
        all_results = data.get('results', [])

        # 페이지네이션 적용
        total_count = len(all_results)
        paginated_results = all_results[offset:offset + limit]

        # 결과 포맷팅
        if mobile:
            # 모바일: 사건번호만 반환 (초경량)
            formatted_results = [
                item.get('case', {}).get('name', '')
                for item in paginated_results
            ]
        else:
            # 웹: 전체 정보 반환
            formatted_results = []
            for item in paginated_results:
                case_info = item.get('case', {})
                formatted_results.append({
                    "case_no": case_info.get('name', ''),
                    "site": case_info.get('site', ''),
                    "number": case_info.get('number', '')
                })

        return {
            "success": True,
            "results": formatted_results,
            "count": len(formatted_results),
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_count
        }

    except requests.Timeout:
        logger.warning("ValueAuction API 타임아웃")
        return {
            "success": False,
            "results": [],
            "message": "검색 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.",
            "error_code": APIError.EXTERNAL_API_ERROR
        }
    except requests.RequestException as e:
        logger.error(f"ValueAuction API 호출 실패: {e}")
        return {
            "success": False,
            "results": [],
            "message": "검색 서비스에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요.",
            "error_code": APIError.EXTERNAL_API_ERROR
        }
    except Exception as e:
        logger.error(f"사건번호 검색 오류: {e}", exc_info=True)
        return {
            "success": False,
            "results": [],
            "message": "검색 중 오류가 발생했습니다. 관리자에게 문의하세요.",
            "error_code": APIError.INTERNAL_SERVER_ERROR
        }


@app.get("/auctions/search")
@limiter.limit("30/minute")
async def search_local_auctions(
    request: Request,
    query: str = Query(None, description="검색 키워드 (사건번호 또는 주소)", min_length=1),
    region: str = Query(None, description="지역 필터"),
    property_type: str = Query(None, description="물건종류 필터"),
    min_price: int = Query(None, description="최소 감정가"),
    max_price: int = Query(None, description="최대 감정가"),
    limit: int = Query(10, description="반환할 최대 결과 수", ge=1, le=100),
    offset: int = Query(0, description="건너뛸 결과 수 (페이지네이션)", ge=0)
):
    """
    로컬 데이터베이스에서 경매 물건 검색

    - query: 사건번호 또는 주소 키워드
    - region: 지역 필터 (서울, 경기, 인천 등)
    - property_type: 물건종류 (아파트, 오피스텔 등)
    - min_price, max_price: 감정가 범위
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # SQL 쿼리 구성
        sql = """
            SELECT
                case_no,
                사건번호,
                물건번호,
                물건종류,
                지역,
                감정가,
                면적,
                경매회차,
                predicted_price,
                created_at
            FROM predictions
            WHERE 1=1
        """
        params = []

        # 검색 키워드 (사건번호 또는 주소)
        if query:
            sql += " AND (사건번호 LIKE ? OR case_no LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        # 지역 필터
        if region:
            sql += " AND 지역 = ?"
            params.append(region)

        # 물건종류 필터
        if property_type:
            sql += " AND 물건종류 = ?"
            params.append(property_type)

        # 가격 범위 필터
        if min_price:
            sql += " AND 감정가 >= ?"
            params.append(min_price)

        if max_price:
            sql += " AND 감정가 <= ?"
            params.append(max_price)

        # 정렬 및 페이지네이션
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # 전체 개수 조회 (페이지네이션용)
        count_sql = sql.split("LIMIT")[0].replace("SELECT case_no, 사건번호, 물건번호, 물건종류, 지역, 감정가, 면적, 경매회차, predicted_price, created_at", "SELECT COUNT(*)")
        cursor.execute(count_sql, params[:-2])  # LIMIT, OFFSET 제외
        total_count = cursor.fetchone()[0]

        # 결과 포맷팅
        results = []
        for row in rows:
            results.append({
                "case_no": row[0],
                "사건번호": row[1],
                "물건번호": row[2],
                "물건종류": row[3],
                "지역": row[4],
                "감정가": row[5],
                "감정가_formatted": f"{row[5]:,}원" if row[5] else "정보 없음",
                "면적": row[6],
                "경매회차": row[7],
                "predicted_price": row[8],
                "predicted_price_formatted": f"{row[8]:,}원" if row[8] else "정보 없음",
                "created_at": row[9]
            })

        conn.close()

        return {
            "success": True,
            "items": results,
            "count": len(results),
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_count
        }

    except Exception as e:
        logger.error(f"로컬 경매 검색 오류: {e}", exc_info=True)
        return {
            "success": False,
            "items": [],
            "message": "검색 중 오류가 발생했습니다",
            "error": str(e)
        }


# ============================================================================
# JWT 인증 API
# ============================================================================

# Pydantic 모델 정의
class UserRegister(BaseModel):
    """사용자 회원가입 요청"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    """사용자 로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh Token 요청"""
    refresh_token: str


# 인증 의존성 함수
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    현재 사용자 확인 (Authorization 헤더에서 JWT 추출)

    Authorization: Bearer <access_token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="잘못된 인증 형식입니다")

    token = authorization.replace("Bearer ", "")

    # 토큰 검증
    payload = auth.verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 토큰입니다")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="잘못된 토큰입니다")

    # DB에서 사용자 조회
    conn = db._get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        return dict(user)
    finally:
        conn.close()


@app.post("/auth/register", tags=["인증"])
async def register_user(user_data: UserRegister):
    """
    사용자 회원가입

    - 이메일과 비밀번호로 회원가입
    - 비밀번호는 bcrypt로 해싱되어 저장
    - 이메일은 고유해야 함
    """
    try:
        # 이메일 유효성 검증
        if not auth.validate_email(user_data.email):
            raise HTTPException(status_code=400, detail="유효하지 않은 이메일 형식입니다")

        # 비밀번호 강도 검증
        is_valid, error_msg = auth.validate_password(user_data.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # 비밀번호 해싱
        hashed_password = auth.hash_password(user_data.password)

        # DB에 사용자 저장
        conn = db._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (email, password_hash, name)
                VALUES (?, ?, ?)
            """, (user_data.email, hashed_password, user_data.name))

            user_id = cursor.lastrowid
            conn.commit()

            logger.info(f"신규 사용자 등록: {user_data.email} (ID={user_id})")

            # JWT 토큰 생성 (로그인과 동일)
            token_data = {
                "user_id": user_id,
                "email": user_data.email
            }

            access_token = auth.create_access_token(token_data)
            refresh_token = auth.create_refresh_token(token_data)

            # Refresh Token을 DB에 저장
            token_hash = auth.hash_password(refresh_token)
            expires_at = datetime.utcnow() + timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)

            cursor.execute("""
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, token_hash, expires_at))

            conn.commit()

            return {
                "success": True,
                "message": "회원가입이 완료되었습니다",
                "user": {
                    "id": user_id,
                    "email": user_data.email,
                    "name": user_data.name
                },
                "access_token": access_token,
                "refresh_token": refresh_token
            }

        except sqlite3.IntegrityError:
            conn.rollback()
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회원가입 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다")


@app.post("/auth/login", response_model=TokenResponse, tags=["인증"])
async def login_user(login_data: UserLogin):
    """
    사용자 로그인

    - 이메일과 비밀번호로 로그인
    - Access Token (1시간)과 Refresh Token (30일) 발급
    """
    try:
        # DB에서 사용자 조회
        conn = db._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (login_data.email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")

        # 비활성화된 사용자 체크
        if not user['is_active']:
            raise HTTPException(status_code=403, detail="비활성화된 계정입니다")

        # 비밀번호 검증
        if not auth.verify_password(login_data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")

        # JWT 토큰 생성
        token_data = {
            "user_id": user['id'],
            "email": user['email']
        }

        access_token = auth.create_access_token(token_data)
        refresh_token = auth.create_refresh_token(token_data)

        # Refresh Token을 DB에 저장
        token_hash = auth.hash_password(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)

        cursor.execute("""
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
        """, (user['id'], token_hash, expires_at))

        # 마지막 로그인 시간 업데이트
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        """, (user['id'],))

        conn.commit()
        conn.close()

        logger.info(f"로그인 성공: {login_data.email} (ID={user['id']})")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="로그인 중 오류가 발생했습니다")


@app.post("/auth/refresh", response_model=TokenResponse, tags=["인증"])
async def refresh_access_token(refresh_data: RefreshTokenRequest):
    """
    Access Token 갱신

    - Refresh Token으로 새로운 Access Token 발급
    - Refresh Token도 함께 갱신 (Rotating Refresh Token)
    """
    try:
        # Refresh Token 검증
        payload = auth.verify_token(refresh_data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 Refresh Token입니다")

        user_id = payload.get("user_id")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(status_code=401, detail="잘못된 토큰입니다")

        # DB에서 사용자 확인
        conn = db._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        # 새로운 토큰 생성
        token_data = {"user_id": user_id, "email": email}
        new_access_token = auth.create_access_token(token_data)
        new_refresh_token = auth.create_refresh_token(token_data)

        # 새로운 Refresh Token을 DB에 저장
        token_hash = auth.hash_password(new_refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)

        cursor.execute("""
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
        """, (user_id, token_hash, expires_at))

        conn.commit()
        conn.close()

        logger.info(f"토큰 갱신: {email} (ID={user_id})")

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="토큰 갱신 중 오류가 발생했습니다")


@app.post("/auth/logout", tags=["인증"])
async def logout_user(
    refresh_data: RefreshTokenRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    로그아웃

    - Refresh Token을 무효화 (revoke)
    - Authorization 헤더에 Access Token 필요
    """
    try:
        # Refresh Token 검증
        payload = auth.verify_token(refresh_data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")

        # DB에서 Refresh Token 무효화
        token_hash = auth.hash_password(refresh_data.refresh_token)
        conn = db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE refresh_tokens
            SET is_revoked = 1
            WHERE user_id = ? AND token_hash = ?
        """, (current_user['id'], token_hash))

        conn.commit()
        conn.close()

        logger.info(f"로그아웃: {current_user['email']} (ID={current_user['id']})")

        return {
            "success": True,
            "message": "로그아웃되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그아웃 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="로그아웃 중 오류가 발생했습니다")


@app.get("/auth/me", tags=["인증"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    현재 로그인된 사용자 정보 조회

    - Authorization 헤더에 Access Token 필요
    """
    return {
        "success": True,
        "user": {
            "id": current_user['id'],
            "email": current_user['email'],
            "name": current_user['name'],
            "is_admin": bool(current_user['is_admin']),
            "created_at": current_user['created_at'],
            "last_login": current_user['last_login']
        }
    }


# ============================================================
# 푸시 알림 API (FCM)
# ============================================================

class FCMTokenSubscribe(BaseModel):
    """FCM 토큰 등록 요청"""
    fcm_token: str
    device_id: str
    device_type: str = "android"
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


class SendNotificationRequest(BaseModel):
    """알림 전송 요청 (관리자용)"""
    user_ids: Optional[list[int]] = None  # None이면 전체 사용자
    title: str
    body: str
    data: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None


@app.post("/notifications/subscribe", tags=["알림"])
async def subscribe_fcm_token(
    token_data: FCMTokenSubscribe,
    current_user: dict = Depends(get_current_user)
):
    """
    FCM 토큰 등록/갱신

    - 사용자의 디바이스 FCM 토큰을 등록합니다
    - 이미 등록된 device_id는 토큰이 갱신됩니다
    """
    try:
        # FCM 토큰 형식 검증
        if not notifications.validate_fcm_token(token_data.fcm_token):
            raise HTTPException(status_code=400, detail="유효하지 않은 FCM 토큰 형식입니다")

        conn = db._get_connection()
        cursor = conn.cursor()

        # 기존 토큰 확인 (같은 device_id + user_id)
        cursor.execute("""
            SELECT id FROM fcm_tokens
            WHERE user_id = ? AND device_id = ?
        """, (current_user['id'], token_data.device_id))

        existing = cursor.fetchone()

        if existing:
            # 토큰 갱신
            cursor.execute("""
                UPDATE fcm_tokens
                SET fcm_token = ?,
                    device_type = ?,
                    device_model = ?,
                    os_version = ?,
                    app_version = ?,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                token_data.fcm_token,
                token_data.device_type,
                token_data.device_model,
                token_data.os_version,
                token_data.app_version,
                existing[0]
            ))
            action = "updated"
        else:
            # 신규 토큰 등록
            cursor.execute("""
                INSERT INTO fcm_tokens (
                    user_id, device_id, fcm_token, device_type,
                    device_model, os_version, app_version, last_used_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                current_user['id'],
                token_data.device_id,
                token_data.fcm_token,
                token_data.device_type,
                token_data.device_model,
                token_data.os_version,
                token_data.app_version
            ))
            action = "registered"

        conn.commit()
        conn.close()

        logger.info(
            f"FCM 토큰 {action}: user_id={current_user['id']}, "
            f"device_id={token_data.device_id}"
        )

        return {
            "success": True,
            "message": f"FCM 토큰이 {action}되었습니다",
            "action": action
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FCM 토큰 등록 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="FCM 토큰 등록 중 오류가 발생했습니다")


@app.delete("/notifications/unsubscribe/{device_id}", tags=["알림"])
async def unsubscribe_fcm_token(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    FCM 토큰 구독 해제

    - 특정 디바이스의 푸시 알림을 비활성화합니다
    """
    try:
        conn = db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fcm_tokens
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND device_id = ?
        """, (current_user['id'], device_id))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        if affected == 0:
            raise HTTPException(status_code=404, detail="등록된 디바이스를 찾을 수 없습니다")

        logger.info(f"FCM 토큰 비활성화: user_id={current_user['id']}, device_id={device_id}")

        return {
            "success": True,
            "message": "푸시 알림 구독이 해제되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FCM 토큰 구독 해제 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="구독 해제 중 오류가 발생했습니다")


@app.post("/notifications/send", tags=["알림"])
async def send_notification(
    notification_data: SendNotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    푸시 알림 전송 (관리자 전용)

    - 특정 사용자 또는 전체 사용자에게 푸시 알림을 전송합니다
    - 관리자 권한 필요
    """
    # 관리자 권한 확인
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")

    try:
        conn = db._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # FCM 토큰 조회
        if notification_data.user_ids:
            # 특정 사용자들
            placeholders = ','.join('?' * len(notification_data.user_ids))
            query = f"""
                SELECT fcm_token, user_id FROM fcm_tokens
                WHERE user_id IN ({placeholders}) AND is_active = 1
            """
            cursor.execute(query, notification_data.user_ids)
        else:
            # 전체 사용자
            cursor.execute("""
                SELECT fcm_token, user_id FROM fcm_tokens
                WHERE is_active = 1
            """)

        tokens_data = cursor.fetchall()
        tokens = [row['fcm_token'] for row in tokens_data]

        if not tokens:
            return {
                "success": True,
                "message": "전송할 대상이 없습니다",
                "success_count": 0,
                "failure_count": 0
            }

        # 일괄 전송
        result = notifications.send_multicast_notification(
            tokens=tokens,
            title=notification_data.title,
            body=notification_data.body,
            data=notification_data.data,
            image_url=notification_data.image_url
        )

        # 알림 로그 저장
        for row in tokens_data:
            cursor.execute("""
                INSERT INTO notification_logs (
                    user_id, notification_type, title, body, data,
                    fcm_token, success
                ) VALUES (?, 'manual', ?, ?, ?, ?, 1)
            """, (
                row['user_id'],
                notification_data.title,
                notification_data.body,
                json.dumps(notification_data.data) if notification_data.data else None,
                row['fcm_token']
            ))

        conn.commit()
        conn.close()

        logger.info(
            f"푸시 알림 전송 완료: {result['success_count']}/{len(tokens)} 성공"
        )

        return {
            "success": True,
            "message": f"{result['success_count']}명에게 알림을 전송했습니다",
            "success_count": result['success_count'],
            "failure_count": result['failure_count']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"푸시 알림 전송 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="알림 전송 중 오류가 발생했습니다")


@app.get("/notifications/history", tags=["알림"])
async def get_notification_history(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    알림 수신 내역 조회

    - 사용자가 받은 푸시 알림 내역을 조회합니다
    """
    try:
        conn = db._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 총 개수 조회
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM notification_logs
            WHERE user_id = ?
        """, (current_user['id'],))

        total = cursor.fetchone()['total']

        # 알림 내역 조회
        cursor.execute("""
            SELECT
                id,
                notification_type,
                title,
                body,
                data,
                success,
                sent_at
            FROM notification_logs
            WHERE user_id = ?
            ORDER BY sent_at DESC
            LIMIT ? OFFSET ?
        """, (current_user['id'], limit, offset))

        notifications_list = []
        for row in cursor.fetchall():
            notification = dict(row)
            # JSON 데이터 파싱
            if notification['data']:
                try:
                    notification['data'] = json.loads(notification['data'])
                except:
                    notification['data'] = None
            notifications_list.append(notification)

        conn.close()

        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
            "notifications": notifications_list
        }

    except Exception as e:
        logger.error(f"알림 내역 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="알림 내역 조회 중 오류가 발생했습니다")


@app.post("/notifications/test", tags=["알림"])
async def send_test_notification(current_user: dict = Depends(get_current_user)):
    """
    테스트 푸시 알림 전송

    - 현재 로그인한 사용자의 모든 활성 디바이스로 테스트 알림을 전송합니다
    """
    try:
        conn = db._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 사용자의 활성 FCM 토큰 조회
        cursor.execute("""
            SELECT fcm_token, device_id FROM fcm_tokens
            WHERE user_id = ? AND is_active = 1
        """, (current_user['id'],))

        tokens_data = cursor.fetchall()

        if not tokens_data:
            return {
                "success": False,
                "message": "등록된 디바이스가 없습니다"
            }

        # 각 디바이스로 테스트 알림 전송
        success_count = 0
        for row in tokens_data:
            success = notifications.send_notification(
                token=row['fcm_token'],
                title="테스트 알림",
                body=f"경매예측AI 앱 푸시 알림이 정상 작동합니다! 👍",
                data={"type": "test", "device_id": row['device_id']}
            )
            if success:
                success_count += 1

        conn.close()

        return {
            "success": True,
            "message": f"{success_count}/{len(tokens_data)}개 디바이스로 테스트 알림을 전송했습니다",
            "success_count": success_count,
            "total_devices": len(tokens_data)
        }

    except Exception as e:
        logger.error(f"테스트 알림 전송 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="테스트 알림 전송 중 오류가 발생했습니다")


# =====================================================================
# 알림 스케줄러 (APScheduler)
# =====================================================================

# 스케줄러 인스턴스 (전역)
notification_scheduler = BackgroundScheduler()


def send_auction_reminders_job():
    """
    내일 경매가 있는 물건에 대해 알림 전송
    매일 오전 9시에 실행
    """
    try:
        logger.info("=== 경매 알림 작업 시작 ===")

        # 내일 날짜 계산
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        conn = db._get_connection()
        cursor = conn.cursor()

        # 내일 경매가 있는 물건 조회
        cursor.execute("""
            SELECT id, case_number, address, appraisal_value, auction_date
            FROM auction_items
            WHERE DATE(auction_date) = ?
            AND status IN ('scheduled', 'active')
        """, (tomorrow,))

        auctions = cursor.fetchall()

        if not auctions:
            logger.info(f"내일({tomorrow}) 예정된 경매가 없습니다")
            conn.close()
            return

        logger.info(f"내일({tomorrow}) 경매 {len(auctions)}건 발견")

        # 각 경매 물건에 대해 알림 전송
        for auction in auctions:
            auction_id, case_number, address, appraisal_value, auction_date = auction

            # 이 물건을 구독한 사용자 찾기
            cursor.execute("""
                SELECT DISTINCT user_id
                FROM auction_subscriptions
                WHERE notification_enabled = 1
                AND (
                    case_number = ?
                    OR (address_keyword IS NOT NULL AND ? LIKE '%' || address_keyword || '%')
                    OR (min_price IS NOT NULL AND max_price IS NOT NULL
                        AND ? BETWEEN min_price AND max_price)
                )
            """, (case_number, address, appraisal_value))

            subscribers = cursor.fetchall()

            if not subscribers:
                continue

            logger.info(f"경매 {case_number}에 대한 구독자 {len(subscribers)}명 발견")

            # 구독자들의 FCM 토큰 수집
            user_ids = [sub[0] for sub in subscribers]
            placeholders = ','.join('?' * len(user_ids))

            cursor.execute(f"""
                SELECT fcm_token, user_id
                FROM fcm_tokens
                WHERE user_id IN ({placeholders})
                AND is_active = 1
            """, user_ids)

            tokens_data = cursor.fetchall()

            if not tokens_data:
                logger.info(f"경매 {case_number}의 구독자 중 활성 FCM 토큰이 없습니다")
                continue

            # 알림 템플릿 생성
            notification = notifications.NotificationTemplates.auction_reminder(
                case_number=case_number,
                auction_date=auction_date
            )

            # FCM 토큰 리스트
            fcm_tokens = [token[0] for token in tokens_data]

            # 일괄 알림 전송
            result = notifications.send_multicast_notification(
                tokens=fcm_tokens,
                title=notification['title'],
                body=notification['body'],
                data=notification['data']
            )

            logger.info(
                f"경매 {case_number} 알림 전송 완료: "
                f"성공={result['success_count']}, 실패={result['failure_count']}"
            )

            # 알림 로그 저장
            for token, user_id in tokens_data:
                cursor.execute("""
                    INSERT INTO notification_logs (
                        user_id, notification_type, title, body, data,
                        fcm_token, success, sent_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    user_id,
                    'auction_reminder',
                    notification['title'],
                    notification['body'],
                    json.dumps(notification['data']),
                    token,
                    1  # 일괄 전송이므로 개별 성공 여부는 추적 안함
                ))

            conn.commit()

        conn.close()
        logger.info(f"=== 경매 알림 작업 완료: 총 {len(auctions)}건 처리 ===")

    except Exception as e:
        logger.error(f"경매 알림 작업 중 오류 발생: {e}", exc_info=True)


def check_price_drops_job():
    """
    가격 하락 물건 체크 및 알림 전송
    매일 오후 2시에 실행
    """
    try:
        logger.info("=== 가격 하락 체크 작업 시작 ===")

        conn = db._get_connection()
        cursor = conn.cursor()

        # 최근 가격이 하락한 물건 찾기 (최근 7일 이내)
        cursor.execute("""
            SELECT
                a.id,
                a.case_number,
                a.appraisal_value,
                a.minimum_sale_price
            FROM auction_items a
            WHERE a.updated_at >= datetime('now', '-7 days')
            AND a.status IN ('scheduled', 'active')
            AND EXISTS (
                SELECT 1 FROM auction_subscriptions s
                WHERE s.case_number = a.case_number
                AND s.notification_enabled = 1
            )
        """)

        price_drops = cursor.fetchall()

        if not price_drops:
            logger.info("가격 하락 물건이 없습니다")
            conn.close()
            return

        logger.info(f"가격 하락 가능성 물건 {len(price_drops)}건 발견")

        for item in price_drops:
            item_id, case_number, appraisal_value, minimum_sale_price = item

            # 이 물건을 구독한 사용자의 FCM 토큰 조회
            cursor.execute("""
                SELECT DISTINCT f.fcm_token, f.user_id
                FROM auction_subscriptions s
                JOIN fcm_tokens f ON s.user_id = f.user_id
                WHERE s.case_number = ?
                AND s.notification_enabled = 1
                AND f.is_active = 1
            """, (case_number,))

            tokens_data = cursor.fetchall()

            if not tokens_data:
                continue

            # 가격 하락 알림 생성
            current_price = minimum_sale_price or appraisal_value
            notification = notifications.NotificationTemplates.price_drop_alert(
                case_number=case_number,
                current_price=current_price
            )

            # FCM 토큰 리스트
            fcm_tokens = [token[0] for token in tokens_data]

            # 일괄 알림 전송
            result = notifications.send_multicast_notification(
                tokens=fcm_tokens,
                title=notification['title'],
                body=notification['body'],
                data=notification['data']
            )

            logger.info(
                f"가격 하락 알림 전송 완료 ({case_number}): "
                f"성공={result['success_count']}, 실패={result['failure_count']}"
            )

            # 알림 로그 저장
            for token, user_id in tokens_data:
                cursor.execute("""
                    INSERT INTO notification_logs (
                        user_id, notification_type, title, body, data,
                        fcm_token, success, sent_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    user_id,
                    'price_drop',
                    notification['title'],
                    notification['body'],
                    json.dumps(notification['data']),
                    token,
                    1
                ))

            conn.commit()

        conn.close()
        logger.info("=== 가격 하락 체크 작업 완료 ===")

    except Exception as e:
        logger.error(f"가격 하락 체크 작업 중 오류 발생: {e}", exc_info=True)


def start_notification_scheduler():
    """알림 스케줄러 시작"""
    try:
        # 경매 알림: 매일 오전 9시
        notification_scheduler.add_job(
            send_auction_reminders_job,
            CronTrigger(hour=9, minute=0),
            id='auction_reminders',
            name='경매 1일 전 알림',
            replace_existing=True
        )

        # 가격 하락 체크: 매일 오후 2시
        notification_scheduler.add_job(
            check_price_drops_job,
            CronTrigger(hour=14, minute=0),
            id='price_drop_check',
            name='가격 하락 알림',
            replace_existing=True
        )

        notification_scheduler.start()
        logger.info("=" * 60)
        logger.info("📅 알림 스케줄러 시작 완료")
        logger.info("  - 경매 알림: 매일 오전 9시")
        logger.info("  - 가격 하락 체크: 매일 오후 2시")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"스케줄러 시작 실패: {e}", exc_info=True)


def stop_notification_scheduler():
    """알림 스케줄러 종료"""
    try:
        notification_scheduler.shutdown(wait=False)
        logger.info("알림 스케줄러 종료 완료")
    except Exception as e:
        logger.error(f"스케줄러 종료 실패: {e}", exc_info=True)


# FastAPI 이벤트: 애플리케이션 시작 시 스케줄러 자동 시작
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("애플리케이션 시작 중...")
    start_notification_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("애플리케이션 종료 중...")
    stop_notification_scheduler()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
