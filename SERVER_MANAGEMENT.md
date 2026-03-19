# Auction AI 서버 관리 가이드

## 서버 정보
- **IP**: 49.50.131.190
- **SSH 포트**: 2222
- **서비스명**: auction_ai.service
- **로그 파일**: /tmp/auction_ai.log

## systemd 서비스 관리

서버는 systemd 서비스로 관리되어 자동으로 재시작됩니다.

### 서비스 상태 확인
```bash
ssh -p 2222 root@49.50.131.190 "systemctl status auction_ai.service"
```

### 서비스 시작
```bash
ssh -p 2222 root@49.50.131.190 "systemctl start auction_ai.service"
```

### 서비스 중지
```bash
ssh -p 2222 root@49.50.131.190 "systemctl stop auction_ai.service"
```

### 서비스 재시작
```bash
ssh -p 2222 root@49.50.131.190 "systemctl restart auction_ai.service"
```

## 코드 배포

### 간편 배포 (추천)
서버에 재시작 스크립트가 있습니다. 이 스크립트는 자동으로 최신 코드를 가져오고 서버를 재시작합니다.

```bash
ssh -p 2222 root@49.50.131.190 "/root/auction_gemini/restart_server.sh"
```

### 수동 배포
```bash
# 1. 로컬에서 코드 푸시
git add .
git commit -m "메시지"
git push

# 2. 서버에서 코드 가져오기 및 재시작
ssh -p 2222 root@49.50.131.190 "cd /root/auction_gemini && git pull && systemctl restart auction_ai.service"
```

## 로그 확인

### 실시간 로그 보기
```bash
ssh -p 2222 root@49.50.131.190 "tail -f /tmp/auction_ai.log"
```

### 최근 로그 확인
```bash
ssh -p 2222 root@49.50.131.190 "tail -100 /tmp/auction_ai.log"
```

### systemd 서비스 로그
```bash
ssh -p 2222 root@49.50.131.190 "journalctl -u auction_ai.service -n 50"
```

## 문제 해결

### 포트가 이미 사용 중인 경우
```bash
ssh -p 2222 root@49.50.131.190 "lsof -ti:8000 | xargs kill -9 && systemctl restart auction_ai.service"
```

### 서비스가 시작되지 않는 경우
1. 로그 확인:
```bash
ssh -p 2222 root@49.50.131.190 "journalctl -u auction_ai.service -n 50"
```

2. 모든 프로세스 정리 후 재시작:
```bash
ssh -p 2222 root@49.50.131.190 "systemctl stop auction_ai.service && lsof -ti:8000 | xargs kill -9 2>/dev/null; systemctl start auction_ai.service"
```

## 서비스 설정 파일

서비스 설정 파일 위치: `/etc/systemd/system/auction_ai.service`

수정 후 적용:
```bash
ssh -p 2222 root@49.50.131.190 "systemctl daemon-reload && systemctl restart auction_ai.service"
```

## 서버 부팅 시 자동 시작

서비스는 이미 부팅 시 자동 시작되도록 설정되어 있습니다.

확인:
```bash
ssh -p 2222 root@49.50.131.190 "systemctl is-enabled auction_ai.service"
```

비활성화 (필요시):
```bash
ssh -p 2222 root@49.50.131.190 "systemctl disable auction_ai.service"
```

활성화:
```bash
ssh -p 2222 root@49.50.131.190 "systemctl enable auction_ai.service"
```
