"""
에러 처리 헬퍼 모듈
표준화된 에러 응답 및 로깅
"""
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class APIError:
    """API 에러 코드 상수"""

    # 클라이언트 에러 (400번대)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_CASE_NUMBER = "INVALID_CASE_NUMBER"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # 서버 에러 (500번대)
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
    PREDICTION_FAILED = "PREDICTION_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


def create_error_response(
    error_code: str,
    message: str,
    detail: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    표준화된 에러 응답 생성

    Args:
        error_code: 에러 코드 (APIError 클래스 참조)
        message: 사용자 친화적 메시지
        detail: 상세 에러 정보 (선택)
        data: 추가 데이터 (선택)

    Returns:
        표준화된 에러 응답 딕셔너리
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        }
    }

    if detail:
        response["error"]["detail"] = detail

    if data:
        response["data"] = data

    return response


def handle_validation_error(
    field_name: str,
    value: Any,
    expected: str
) -> HTTPException:
    """
    입력 검증 에러 처리

    Args:
        field_name: 필드 이름
        value: 입력값
        expected: 기대값 설명

    Returns:
        HTTPException (400)
    """
    error_response = create_error_response(
        error_code=APIError.INVALID_INPUT,
        message=f"입력값이 올바르지 않습니다: {field_name}",
        detail=f"'{value}'는 유효하지 않습니다. {expected}",
        data={"field": field_name, "value": str(value)}
    )

    logger.warning(
        f"Validation error: {field_name}={value}",
        extra={"error_code": APIError.INVALID_INPUT}
    )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_response
    )


def handle_not_found_error(
    resource_type: str,
    resource_id: str
) -> HTTPException:
    """
    리소스 없음 에러 처리

    Args:
        resource_type: 리소스 타입 (예: "사건번호", "모델")
        resource_id: 리소스 ID

    Returns:
        HTTPException (404)
    """
    error_response = create_error_response(
        error_code=APIError.RESOURCE_NOT_FOUND,
        message=f"{resource_type}을(를) 찾을 수 없습니다",
        detail=f"'{resource_id}'에 해당하는 {resource_type}이(가) 존재하지 않습니다",
        data={"resource_type": resource_type, "resource_id": resource_id}
    )

    logger.info(
        f"Resource not found: {resource_type}={resource_id}",
        extra={"error_code": APIError.RESOURCE_NOT_FOUND}
    )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error_response
    )


def handle_server_error(
    operation: str,
    error: Exception,
    error_code: str = APIError.INTERNAL_SERVER_ERROR
) -> HTTPException:
    """
    서버 에러 처리

    Args:
        operation: 수행 중이던 작업 설명
        error: 발생한 예외
        error_code: 에러 코드 (기본: INTERNAL_SERVER_ERROR)

    Returns:
        HTTPException (500)
    """
    error_message = str(error)
    error_response = create_error_response(
        error_code=error_code,
        message=f"{operation} 중 오류가 발생했습니다",
        detail=f"일시적인 오류입니다. 잠시 후 다시 시도해주세요.",
        data={"operation": operation}
    )

    logger.error(
        f"Server error during {operation}: {error_message}",
        exc_info=True,
        extra={"error_code": error_code, "operation": operation}
    )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=error_response
    )


def handle_external_api_error(
    api_name: str,
    error: Exception
) -> HTTPException:
    """
    외부 API 호출 실패 에러 처리

    Args:
        api_name: 외부 API 이름
        error: 발생한 예외

    Returns:
        HTTPException (503)
    """
    error_response = create_error_response(
        error_code=APIError.EXTERNAL_API_ERROR,
        message=f"{api_name} API 연결에 실패했습니다",
        detail="외부 서비스에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요.",
        data={"api_name": api_name}
    )

    logger.error(
        f"External API error: {api_name} - {str(error)}",
        exc_info=True,
        extra={"error_code": APIError.EXTERNAL_API_ERROR, "api_name": api_name}
    )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=error_response
    )


def handle_model_error(
    error: Exception
) -> HTTPException:
    """
    AI 모델 관련 에러 처리

    Args:
        error: 발생한 예외

    Returns:
        HTTPException (500)
    """
    error_response = create_error_response(
        error_code=APIError.MODEL_NOT_LOADED,
        message="AI 모델을 사용할 수 없습니다",
        detail="모델이 로드되지 않았거나 오류가 발생했습니다. 관리자에게 문의하세요.",
        data={}
    )

    logger.error(
        f"Model error: {str(error)}",
        exc_info=True,
        extra={"error_code": APIError.MODEL_NOT_LOADED}
    )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=error_response
    )


def log_api_call(
    endpoint: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    user_ip: Optional[str] = None
):
    """
    API 호출 로깅

    Args:
        endpoint: API 엔드포인트
        method: HTTP 메소드
        params: 요청 파라미터
        user_ip: 사용자 IP 주소
    """
    logger.info(
        f"API call: {method} {endpoint}",
        extra={
            "endpoint": endpoint,
            "method": method,
            "params": params or {},
            "user_ip": user_ip or "unknown"
        }
    )
