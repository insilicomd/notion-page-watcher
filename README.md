# Notion 연구노트 업데이트 알림

Notion API를 사용하여 어제 수정된 페이지를 자동으로 검색하고, 이메일 알림을 발송하며, Notion 데이터베이스에 기록하는 도구입니다.

## 기능

- 어제 수정된 Notion 페이지 자동 검색 (한국 시간 기준)
- 업데이트 목록을 HTML 형식의 이메일로 발송
- 업데이트 내역을 Notion 데이터베이스에 자동 기록

## 설치

```bash
# uv 설치 (설치되어 있지 않은 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 변수를 설정합니다:

```env
# Notion API
NOTION_API_KEY=your_notion_api_key

# SMTP 설정
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SENDER_EMAIL=your_email@example.com
GW_PW=your_email_password
```

### Notion API 키 발급

1. [Notion Developers](https://www.notion.so/my-integrations)에서 새 통합 생성
2. 생성된 Internal Integration Token을 `NOTION_API_KEY`에 설정
3. 검색할 Notion 워크스페이스에서 해당 통합을 연결

## 사용 방법

### 기본 실행
`notion_page_watcher.ipynb` 파일 사용

````
# 오늘 기준 어제 업데이트 검색 및 알림
main(reciver_email_list=["recipient@example.com"])

# 2025년 12월 17일 기준으로 12월 16일 업데이트 검색
main(reciver_email_list=["recipient@example.com"], now="20251217")
```

### CLI 실행

```bash
uv run python notion_page_watcher.py
```

`notion_page_watcher.py` 하단의 `reciver_email_list`와 `now` 변수를 수정하여 실행합니다.

## 주요 함수

| 함수 | 설명 |
|------|------|
| `search_recent_pages()` | 최근 수정된 페이지 검색 |
| `filter_yesterday_updates(results, now)` | 어제 업데이트된 페이지 필터링 |
| `add_to_db(title, page_id, uid, write_date)` | Notion 데이터베이스에 기록 |
| `send_email(receiver_email_list, body, yesterday)` | 이메일 발송 |
| `main(reciver_email_list, now)` | 전체 프로세스 실행 |

## 이메일 형식

발송되는 이메일은 HTML 형식이며, 다음 정보를 포함합니다:

- 페이지 제목 (굵은 글씨)
- 페이지 URL
- 마지막 수정 시간 (KST)
