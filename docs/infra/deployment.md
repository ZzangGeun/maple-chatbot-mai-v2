# 배포 가이드 (Deployment)

클라우드 VM 1대에 Docker Compose로 배포하는 절차입니다. 운영 구성은 [`docker-compose.prod.yml`](../../docker-compose.prod.yml)에 있습니다.

## 1. 구성

```
인터넷 ──80/443──▶ Caddy (HTTPS 자동 발급·갱신, deploy/Caddyfile)
                      │
                      ▼
                   Django (uvicorn ASGI, 정적 파일·React 화면은 WhiteNoise로 서빙)
                      │ X-Internal-Token
                      ▼
                   AI 서버 (FastAPI, 임베딩 모델 CPU 실행, LLM은 외부 API)
         Postgres(pgvector) · Redis  ← 외부 포트 없음, 컨테이너끼리만 접근
```

| 서비스 | 이미지 | 비고 |
| :--- | :--- | :--- |
| `caddy` | `caddy:2` | 외부에 열리는 유일한 서비스. SSE가 버퍼링되지 않도록 즉시 전달 |
| `django` | `Dockerfile.django` | 시작 시 `migrate` 실행, `production` 설정, 워커 수는 `WEB_CONCURRENCY` |
| `fastapi` | `Dockerfile.fastapi` | CPU 전용 PyTorch. 임베딩 모델은 `hf_cache` 볼륨에 보관 |
| `db` | `pgvector/pgvector:pg16` | `pgdata` 볼륨 |
| `redis` | `redis:7-alpine` | 캐시·요청 제한 카운터·넥슨 API 응답 캐시 |

개발용 `docker-compose.yml`과 다른 점은 다음과 같습니다.
- 소스를 마운트하지 않고 이미지에 담습니다. 코드를 바꾸면 `--build`로 다시 빌드합니다.
- Caddy(80/443)만 외부에 열고, DB·Redis·AI 서버 포트는 열지 않습니다.
- Django가 `runserver` 대신 uvicorn으로 실행되므로 채팅 답변이 실시간으로 스트리밍됩니다.

## 2. 서버 준비

1. **VM**: 4 vCPU / 8GB RAM 이상을 권장합니다(임베딩 모델과 PyTorch가 메모리를 씁니다). 디스크는 30GB 이상, 리전은 서울을 권장합니다.
2. **방화벽**: 22(SSH), 80, 443만 엽니다.
3. **도메인**: DNS A 레코드를 서버 공인 IP로 연결합니다. 이 연결이 되어 있어야 Caddy가 인증서를 받을 수 있습니다.
4. **Docker 설치**: Docker Engine과 Compose 플러그인을 설치합니다.

## 3. 첫 배포

```bash
git clone <저장소 주소> mai && cd mai
mkdir -p env && cp deploy/env.prod.example env/.env.prod
# env/.env.prod 값 채우기: DOMAIN, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, SECRET_KEY,
# DATABASE_PASSWORD, AI_SERVER_TOKEN, NEXON_API_KEY, DEEPSEEK_API_KEY 등

docker compose -f docker-compose.prod.yml --env-file env/.env.prod up -d --build
docker compose -f docker-compose.prod.yml ps        # 모든 서비스가 healthy인지 확인

# 지식 베이스 적재 (검토된 공략 문서 + 넥슨 공지). 처음에는 임베딩 모델을 내려받습니다.
docker compose -f docker-compose.prod.yml exec fastapi python -m ai_server.rag.ingest
```

- 비밀 값은 `python -c "import secrets; print(secrets.token_urlsafe(48))"`로 만듭니다.
- 관리자 계정이 필요하면 `docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser`로 만듭니다.

## 4. 업데이트 배포

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file env/.env.prod up -d --build
```

마이그레이션은 Django 컨테이너가 시작할 때 자동으로 실행됩니다. `env/.env.prod`만 바꿨다면 `--build` 없이 `up -d`를 실행해도 컨테이너가 새 값으로 다시 만들어집니다.

## 5. 운영 점검 목록

- [ ] 브라우저에서 `https://도메인` 접속, 로그인·채팅 답변 스트리밍 확인
- [ ] HTTPS가 정상이면 `SECURE_HSTS_SECONDS=31536000`으로 올리고 다시 배포
- [ ] 넥슨 Open API **서비스 단계 키**로 바꾸고 `NEXON_REQUESTS_PER_SECOND` 상향, 서비스 화면에 출처 표기
- [ ] DeepSeek 결제·사용 한도 설정
- [ ] 공략 문서 검토(`status: reviewed`) 후 적재
- [ ] DB 정기 백업 설정 (아래)
- [ ] 개인정보처리방침 게시 (회원가입·대화 기록 저장, 애드센스 승인에도 필요)

## 6. 백업과 로그

```bash
# DB 백업 (cron으로 매일 실행 권장, 백업 파일은 서버 밖으로도 복사)
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres -Fc maple_chatbot_db > backup_$(date +%Y%m%d).dump

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f django fastapi
```

## 7. 보안 설정 요약

| 항목 | 설정 |
| :--- | :--- |
| 채팅 세션 소유권 | 로그인 세션은 본인만, 비로그인 세션은 만든 브라우저(세션 키)만 접근 |
| CSRF | 모든 POST/DELETE에 적용. 프론트가 시작할 때 부르는 `/api/v1/auth/user/`가 쿠키를 발급 |
| 요청 횟수 제한 | `CHAT_RATE_LIMIT_USER`(계정 기준), `CHAT_RATE_LIMIT_ANON`(IP 기준), Redis 카운터 |
| 메시지 길이 | `CHAT_MESSAGE_MAX_CHARS` (기본 2000자) |
| AI 서버 | 외부 포트 없음 + `AI_SERVER_TOKEN` 검사. 관리자 API는 `AI_ADMIN_TOKEN` 일치 시에만 허용 |
| HTTPS·쿠키 | Caddy가 인증서 처리, 세션·CSRF 쿠키 `Secure`, HSTS는 설정값으로 켬 |

## 8. CI/CD (예정)

GitHub Actions로 `pytest` → 이미지 빌드 → 서버에서 `git pull && docker compose ... up -d --build`를 자동화할 예정입니다.
