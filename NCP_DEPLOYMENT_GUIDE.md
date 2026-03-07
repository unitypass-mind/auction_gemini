# NCP 서버 배포 가이드

## 개요
이 문서는 경매 AI 서비스를 Naver Cloud Platform (NCP)에 배포하는 전체 과정을 안내합니다.

## 목차
1. [NCP 계정 설정](#1-ncp-계정-설정)
2. [서버 인스턴스 생성](#2-서버-인스턴스-생성)
3. [서버 초기 설정](#3-서버-초기-설정)
4. [애플리케이션 배포](#4-애플리케이션-배포)
5. [Nginx + Gunicorn 설정](#5-nginx--gunicorn-설정)
6. [도메인 연결 및 HTTPS](#6-도메인-연결-및-https)
7. [모니터링 및 로그 관리](#7-모니터링-및-로그-관리)
8. [백업 및 보안](#8-백업-및-보안)

---

## 1. NCP 계정 설정

### 1.1 회원가입
1. https://www.ncloud.com 접속
2. **회원가입** 클릭
3. 이메일 인증 완료
4. 본인 인증 (휴대폰 또는 아이핀)

### 1.2 결제 수단 등록
1. 콘솔 > 마이페이지 > 결제 관리
2. 신용카드 또는 계좌 등록
3. **무료 크레딧 100,000원** 자동 지급 확인

### 1.3 콘솔 접근
- Console: https://console.ncloud.com
- 주요 메뉴: Compute > Server, Storage > Object Storage, Networking > Load Balancer

---

## 2. 서버 인스턴스 생성

### 2.1 서버 생성 (표준형)
1. **Console > Compute > Server** 이동
2. **서버 생성** 버튼 클릭
3. 서버 이미지 선택:
   - **OS**: Ubuntu Server 22.04 LTS
   - 버전: 최신 버전 선택

### 2.2 서버 스펙 선택
**권장 스펙 (초기)**:
- **서버 타입**: Standard
- **vCPU**: 2 Core
- **메모리**: 4GB RAM
- **스토리지**: 50GB SSD

**예상 비용**: 약 40,000원/월

**스케일업 시나리오**:
- 트래픽 증가 → High CPU (4 Core, 8GB)
- 대용량 데이터 → 스토리지 추가

### 2.3 네트워크 설정
1. **VPC 선택** (자동 생성 또는 기존 VPC)
2. **공인 IP 할당**: "신규 할당" 선택
3. **ACG (Access Control Group)** 설정:
   ```
   Inbound Rules:
   - SSH (22번 포트): 관리자 IP만 허용
   - HTTP (80번 포트): 0.0.0.0/0 (전체 허용)
   - HTTPS (443번 포트): 0.0.0.0/0 (전체 허용)
   - Custom (8000번 포트): 0.0.0.0/0 (개발용, 나중에 제거)
   ```

### 2.4 서버 인증키 생성
1. **인증키 이름**: `auction-ai-key`
2. **인증키 다운로드** (PEM 파일)
3. 안전한 위치에 보관:
   ```bash
   mv ~/Downloads/auction-ai-key.pem ~/.ssh/
   chmod 400 ~/.ssh/auction-ai-key.pem
   ```

### 2.5 서버 생성 완료
- 서버 생성 소요 시간: 약 3~5분
- 서버 목록에서 **공인 IP** 확인

---

## 3. 서버 초기 설정

### 3.1 SSH 접속
```bash
# Windows (Git Bash 또는 PowerShell)
ssh -i ~/.ssh/auction-ai-key.pem root@<공인IP>

# 처음 접속 시 fingerprint 확인
# "yes" 입력
```

### 3.2 시스템 업데이트
```bash
apt update && apt upgrade -y
```

### 3.3 타임존 설정
```bash
timedatectl set-timezone Asia/Seoul
date  # 확인
```

### 3.4 방화벽 설정 (UFW)
```bash
# UFW 설치 및 활성화
apt install ufw -y

# 기본 정책: 모든 인바운드 차단, 아웃바운드 허용
ufw default deny incoming
ufw default allow outgoing

# 필수 포트 열기
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# 방화벽 활성화
ufw enable

# 상태 확인
ufw status verbose
```

### 3.5 Python 3.10+ 설치
```bash
# Python 설치 확인 (Ubuntu 22.04는 기본 3.10)
python3 --version

# pip 설치
apt install python3-pip python3-venv -y

# 필수 라이브러리 설치
apt install build-essential libssl-dev libffi-dev python3-dev -y
```

### 3.6 Git 설치
```bash
apt install git -y
git --version
```

### 3.7 Nginx 설치
```bash
apt install nginx -y
systemctl start nginx
systemctl enable nginx
systemctl status nginx
```

### 3.8 관리자 계정 생성 (보안 강화)
```bash
# 새 사용자 생성
adduser auctionai

# sudo 권한 부여
usermod -aG sudo auctionai

# SSH 키 복사
mkdir -p /home/auctionai/.ssh
cp ~/.ssh/authorized_keys /home/auctionai/.ssh/
chown -R auctionai:auctionai /home/auctionai/.ssh
chmod 700 /home/auctionai/.ssh
chmod 600 /home/auctionai/.ssh/authorized_keys

# 이후 접속은 auctionai 계정으로
# ssh -i ~/.ssh/auction-ai-key.pem auctionai@<공인IP>
```

---

## 4. 애플리케이션 배포

### 4.1 GitHub Repository 준비
```bash
# SSH 키 생성 (서버에서)
ssh-keygen -t ed25519 -C "server@auction-ai"
cat ~/.ssh/id_ed25519.pub

# GitHub > Settings > Deploy Keys에 공개키 추가
```

### 4.2 프로젝트 클론
```bash
# 작업 디렉토리로 이동
cd /home/auctionai

# Git 클론
git clone git@github.com:YOUR_USERNAME/auction_gemini.git

# 또는 HTTPS (Deploy Key 없이)
git clone https://github.com/YOUR_USERNAME/auction_gemini.git

cd auction_gemini
```

### 4.3 가상환경 설정
```bash
# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# 의존성 설치
pip install -r requirements.txt
```

**requirements.txt 내용 확인**:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pandas==2.1.3
scikit-learn==1.3.2
joblib==1.3.2
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
firebase-admin==6.3.0
apscheduler==3.10.4
```

### 4.4 환경변수 설정
```bash
# .env 파일 생성
nano .env
```

**.env 내용**:
```bash
# JWT 설정
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Firebase
FIREBASE_SERVICE_ACCOUNT=/home/auctionai/auction_gemini/firebase-service-account.json

# 데이터베이스 경로
DATABASE_PATH=/home/auctionai/auction_gemini/database/auction.db

# 로그 디렉토리
LOG_DIR=/home/auctionai/auction_gemini/logs

# 환경
ENVIRONMENT=production
```

**보안 주의**:
```bash
chmod 600 .env
```

### 4.5 Firebase 서비스 계정 키 업로드
```bash
# 로컬에서 서버로 복사
scp -i ~/.ssh/auction-ai-key.pem \
  firebase-service-account.json \
  auctionai@<공인IP>:/home/auctionai/auction_gemini/

# 서버에서 권한 설정
chmod 600 /home/auctionai/auction_gemini/firebase-service-account.json
```

### 4.6 데이터베이스 준비
```bash
# 데이터베이스 디렉토리 생성
mkdir -p database logs

# 기존 DB 업로드 (로컬에서)
scp -i ~/.ssh/auction-ai-key.pem \
  database/auction.db \
  auctionai@<공인IP>:/home/auctionai/auction_gemini/database/

# 모델 파일 업로드
scp -i ~/.ssh/auction-ai-key.pem \
  models/random_forest_model_v4.joblib \
  auctionai@<공인IP>:/home/auctionai/auction_gemini/models/
```

### 4.7 테스트 실행
```bash
# 개발 서버로 테스트
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --host 0.0.0.0 --port 8000

# 다른 터미널에서 테스트
curl http://localhost:8000
curl http://localhost:8000/stats
```

---

## 5. Nginx + Gunicorn 설정

### 5.1 Gunicorn 설치
```bash
source venv/bin/activate
pip install gunicorn
```

### 5.2 Gunicorn 설정 파일
```bash
nano /home/auctionai/auction_gemini/gunicorn_config.py
```

**gunicorn_config.py 내용**:
```python
import multiprocessing

# 서버 소켓
bind = "127.0.0.1:8000"

# Worker 프로세스
workers = multiprocessing.cpu_count() * 2 + 1  # 4 Core → 9 workers
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120

# 로깅
accesslog = "/home/auctionai/auction_gemini/logs/gunicorn_access.log"
errorlog = "/home/auctionai/auction_gemini/logs/gunicorn_error.log"
loglevel = "info"

# 프로세스 이름
proc_name = "auction_ai_api"

# Reload on code changes (개발 환경만)
# reload = True
```

### 5.3 systemd 서비스 등록
```bash
sudo nano /etc/systemd/system/auction-api.service
```

**auction-api.service 내용**:
```ini
[Unit]
Description=Auction AI FastAPI Application
After=network.target

[Service]
Type=notify
User=auctionai
Group=auctionai
WorkingDirectory=/home/auctionai/auction_gemini
Environment="PATH=/home/auctionai/auction_gemini/venv/bin"
ExecStart=/home/auctionai/auction_gemini/venv/bin/gunicorn main:app \
          -c /home/auctionai/auction_gemini/gunicorn_config.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 시작**:
```bash
# 데몬 리로드
sudo systemctl daemon-reload

# 서비스 활성화 및 시작
sudo systemctl enable auction-api
sudo systemctl start auction-api

# 상태 확인
sudo systemctl status auction-api

# 로그 확인
sudo journalctl -u auction-api -f
```

### 5.4 Nginx 리버스 프록시 설정
```bash
sudo nano /etc/nginx/sites-available/auction-api
```

**Nginx 설정 내용**:
```nginx
upstream auction_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.auction-ai.com;  # 실제 도메인으로 변경

    # 클라이언트 요청 크기 제한
    client_max_body_size 10M;

    # 로그
    access_log /var/log/nginx/auction_api_access.log;
    error_log /var/log/nginx/auction_api_error.log;

    # 정적 파일 (있는 경우)
    location /static {
        alias /home/auctionai/auction_gemini/static;
    }

    # API 프록시
    location / {
        proxy_pass http://auction_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 헬스체크 엔드포인트
    location /health {
        access_log off;
        proxy_pass http://auction_api;
    }
}
```

**Nginx 설정 활성화**:
```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/auction-api /etc/nginx/sites-enabled/

# 기본 사이트 비활성화 (선택)
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 5.5 방화벽 포트 8000 제거
```bash
# 개발용 포트 제거 (Nginx를 통해서만 접근)
sudo ufw delete allow 8000/tcp
sudo ufw reload
```

---

## 6. 도메인 연결 및 HTTPS

### 6.1 도메인 구매 및 DNS 설정
1. **도메인 구매** (가비아, Cloudflare 등)
   - 예: `auction-ai.com`
   - 서브도메인: `api.auction-ai.com`

2. **DNS A 레코드 설정**:
   ```
   Type: A
   Name: api
   Value: <NCP 서버 공인 IP>
   TTL: 300
   ```

3. **DNS 전파 확인** (5분~1시간):
   ```bash
   nslookup api.auction-ai.com
   ping api.auction-ai.com
   ```

### 6.2 Let's Encrypt SSL 인증서 설치
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급
sudo certbot --nginx -d api.auction-ai.com

# 입력 정보:
# - Email: your-email@example.com
# - Agree to terms: Yes
# - Share email: No (선택)
# - Redirect HTTP to HTTPS: Yes (2번 선택)
```

**자동 갱신 테스트**:
```bash
sudo certbot renew --dry-run
```

### 6.3 Nginx HTTPS 설정 확인
Certbot이 자동으로 수정한 설정 확인:
```bash
sudo nano /etc/nginx/sites-available/auction-api
```

다음과 같이 443 포트 설정이 추가되어야 함:
```nginx
server {
    listen 443 ssl;
    server_name api.auction-ai.com;

    ssl_certificate /etc/letsencrypt/live/api.auction-ai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.auction-ai.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # ... 나머지 설정
}

server {
    if ($host = api.auction-ai.com) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    server_name api.auction-ai.com;
    return 404;
}
```

### 6.4 HTTPS 접속 테스트
```bash
# 브라우저에서 접속
https://api.auction-ai.com

# curl로 테스트
curl https://api.auction-ai.com
curl https://api.auction-ai.com/stats
```

---

## 7. 모니터링 및 로그 관리

### 7.1 로그 로테이션 설정
```bash
sudo nano /etc/logrotate.d/auction-api
```

**로그 로테이션 설정**:
```
/home/auctionai/auction_gemini/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 auctionai auctionai
    sharedscripts
    postrotate
        systemctl reload auction-api > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/auction_api_*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
```

### 7.2 시스템 모니터링
```bash
# 실시간 리소스 모니터링
htop

# 디스크 사용량
df -h

# 메모리 사용량
free -h

# 네트워크 연결 상태
netstat -tulpn | grep -E ':(80|443|8000)'

# 서비스 상태
systemctl status auction-api nginx
```

### 7.3 애플리케이션 로그 확인
```bash
# Gunicorn 로그
tail -f /home/auctionai/auction_gemini/logs/gunicorn_access.log
tail -f /home/auctionai/auction_gemini/logs/gunicorn_error.log

# 애플리케이션 로그
tail -f /home/auctionai/auction_gemini/logs/auction_api_*.log

# 스케줄러 로그
tail -f /home/auctionai/auction_gemini/logs/scheduler_*.log

# Nginx 로그
sudo tail -f /var/log/nginx/auction_api_access.log
sudo tail -f /var/log/nginx/auction_api_error.log

# systemd 로그
sudo journalctl -u auction-api -f
```

### 7.4 NCP Monitoring 서비스 활용
1. **Console > Monitoring** 이동
2. **Server Monitoring** 선택
3. 모니터링 대상 서버 추가
4. 알림 설정:
   - CPU 사용률 > 80%
   - 메모리 사용률 > 85%
   - 디스크 사용률 > 90%

---

## 8. 백업 및 보안

### 8.1 데이터베이스 백업 스크립트
```bash
nano /home/auctionai/auction_gemini/backup_db.sh
```

**backup_db.sh 내용**:
```bash
#!/bin/bash

BACKUP_DIR="/home/auctionai/backups"
DB_PATH="/home/auctionai/auction_gemini/database/auction.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/auction_db_$TIMESTAMP.db"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# SQLite 백업
sqlite3 $DB_PATH ".backup '$BACKUP_FILE'"

# 압축
gzip $BACKUP_FILE

# 30일 이상 된 백업 파일 삭제
find $BACKUP_DIR -name "*.db.gz" -mtime +30 -delete

echo "Database backup completed: ${BACKUP_FILE}.gz"
```

**실행 권한 부여**:
```bash
chmod +x /home/auctionai/auction_gemini/backup_db.sh
```

**Cron 작업 등록 (매일 새벽 3시)**:
```bash
crontab -e

# 다음 라인 추가
0 3 * * * /home/auctionai/auction_gemini/backup_db.sh >> /home/auctionai/auction_gemini/logs/backup.log 2>&1
```

### 8.2 NCP Object Storage 백업 (선택)
```bash
# AWS CLI 설치 (S3 호환)
pip install awscli

# NCP Object Storage 설정
aws configure --profile ncp
# Access Key: NCP Console에서 생성
# Secret Key: NCP Console에서 생성
# Region: kr-standard

# 백업 업로드
aws s3 sync /home/auctionai/backups/ \
  s3://auction-ai-backups/ \
  --profile ncp
```

### 8.3 보안 강화
```bash
# SSH 포트 변경 (선택)
sudo nano /etc/ssh/sshd_config
# Port 22 → Port 2222로 변경
sudo systemctl restart sshd
# UFW 규칙 업데이트: ufw allow 2222/tcp

# Root 로그인 비활성화
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
sudo systemctl restart sshd

# fail2ban 설치 (브루트포스 공격 방지)
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 8.4 정기 보안 업데이트
```bash
# 자동 보안 업데이트 활성화
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 9. 배포 후 체크리스트

- [ ] 서버 인스턴스 생성 및 공인 IP 할당
- [ ] SSH 접속 및 초기 설정 완료
- [ ] Python, Nginx, Git 설치 완료
- [ ] 프로젝트 클론 및 의존성 설치
- [ ] 환경변수 (.env) 설정
- [ ] Firebase 서비스 계정 키 업로드
- [ ] 데이터베이스 및 모델 파일 업로드
- [ ] Gunicorn + systemd 서비스 등록
- [ ] Nginx 리버스 프록시 설정
- [ ] 방화벽 (UFW) 설정
- [ ] 도메인 DNS 설정
- [ ] SSL 인증서 발급 (Let's Encrypt)
- [ ] HTTPS 접속 테스트
- [ ] 로그 로테이션 설정
- [ ] 데이터베이스 백업 스크립트 및 Cron 작업
- [ ] 모니터링 알림 설정
- [ ] 보안 강화 (Root 로그인 비활성화, fail2ban)

---

## 10. 배포 후 유지보수

### 10.1 코드 업데이트
```bash
cd /home/auctionai/auction_gemini
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart auction-api
```

### 10.2 서비스 재시작
```bash
# API 서버 재시작
sudo systemctl restart auction-api

# Nginx 재시작
sudo systemctl restart nginx

# 스케줄러 재시작 (systemd 서비스인 경우)
sudo systemctl restart auction-scheduler
```

### 10.3 로그 분석
```bash
# 에러 로그 검색
grep -i error /home/auctionai/auction_gemini/logs/*.log

# 최근 1시간 요청 수
tail -n 1000 /var/log/nginx/auction_api_access.log | wc -l

# 응답 시간 분석
awk '{print $NF}' /var/log/nginx/auction_api_access.log | sort -n | tail -n 10
```

---

## 11. 문제 해결

### 11.1 서비스가 시작되지 않음
```bash
# 로그 확인
sudo journalctl -u auction-api -n 50 --no-pager

# 포트 충돌 확인
sudo netstat -tulpn | grep 8000

# 권한 문제 확인
ls -la /home/auctionai/auction_gemini
```

### 11.2 502 Bad Gateway (Nginx)
- Gunicorn이 실행 중인지 확인: `systemctl status auction-api`
- Gunicorn 로그 확인: `/home/auctionai/auction_gemini/logs/gunicorn_error.log`
- Nginx upstream 설정 확인: `127.0.0.1:8000`

### 11.3 메모리 부족
```bash
# 메모리 사용량 확인
free -h

# Gunicorn worker 수 줄이기
# gunicorn_config.py에서 workers 수 조정
workers = 4  # 기존 9에서 4로 감소
```

### 11.4 디스크 공간 부족
```bash
# 디스크 사용량 확인
df -h

# 로그 파일 정리
sudo journalctl --vacuum-time=7d
find /home/auctionai/auction_gemini/logs -name "*.log" -mtime +30 -delete

# APT 캐시 정리
sudo apt clean
```

---

## 12. 참고 자료

- [NCP 공식 문서](https://guide.ncloud-docs.com/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn 설정](https://docs.gunicorn.org/en/stable/settings.html)
- [Nginx 최적화](https://www.nginx.com/blog/tuning-nginx/)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)

---

**작성일**: 2026-03-05
**버전**: 1.0
**작성자**: Claude AI Assistant
**예상 배포 시간**: 4~6시간
**예상 월 비용**: 약 40,000원 (Standard 2 Core, 4GB)
