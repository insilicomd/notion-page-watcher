import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Notion API 설정
NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
NOTION_VERSION = "2025-09-03"

# API 헤더 설정
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}


def get_users():
    url = "https://api.notion.com/v1/users"
    response = requests.get(url, headers=headers)
    if response.status_code ==200:
        return response.json()
    else:
        return None
    

def get_user_list():
    users = get_users()
    if users:
        user_results = users['results']
        
        results = {}
        for user in user_results:
            uid = user['id']
            name = user['name']
            results[uid] = name 
    return results


def search_recent_pages():
    """최근 수정된 페이지 검색"""
    url = "https://api.notion.com/v1/search"
    
    payload = {
        "filter": {
            "value": "page",
            "property": "object"
        },
        "sort": {
            "direction": "descending",
            "timestamp": "last_edited_time"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        # print(f"오류 발생: {response.status_code}")
        # print(response.text)
        return None


def get_now(now=None):
    kst = ZoneInfo("Asia/Seoul")
    if now is None:
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
    else:
        year = int(now[:4])
        month = int(now[4:6])
        day = int(now[6:])

    now_kst = datetime(year, month, day, 0, 0, 0, tzinfo=kst)
    today_start_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)

    return today_start_kst


def filter_yesterday_updates(results, now=None):
    """
    어제 업데이트된 페이지만 필터링 (한국 시간 기준)
    now: str='20251217'
    """
    kst = ZoneInfo("Asia/Seoul")
    today_start_kst = get_now(now=now)
    yesterday_start_kst = today_start_kst - timedelta(days=1)
    
    yesterday_pages = []
    
    if results and 'results' in results:
        for page in results['results']:
            # UTC 시간을 파싱 후 KST로 변환
            last_edited_utc = datetime.fromisoformat(
                page['last_edited_time'].replace('Z', '+00:00')
            )
            last_edited_kst = last_edited_utc.astimezone(kst)
            
            # KST 기준으로 비교
            if yesterday_start_kst <= last_edited_kst < today_start_kst:
                yesterday_pages.append(page)
    
    return yesterday_pages


def extract_title(page):
    """페이지에서 제목 추출"""
    title = "제목 없음"        

    if 'properties' in page:
        for prop_name, prop_value in page['properties'].items():
            if prop_value.get('type') == 'title' and prop_value.get('title'):
                title_list = prop_value['title']
                if title_list:
                    for key, value in title_list[0].items():
                        if key == 'plain_text':
                            title = value
                            break
                break    
    return title


def extract_user_id(page):
    if 'last_edited_by' in page:
        uid = page['last_edited_by']['id']
        return uid
    else:
        return None


def add_to_db(title, page_id, uid, write_date):
    url = "https://api.notion.com/v1/pages"
    db_research_log_id = os.environ.get('ADDED_DB_ID')

    payload = {
        "parent": {"database_id": db_research_log_id},
        "icon": {
            "type": "external",
            "external": {"url": "https://www.notion.so/icons/compose_gray.svg"} 
        },
        "properties": {
            "제목": {
                "title": [{"text": {"content": title}}]
            },
            # "URL": {
            #     "url": page_url
            # },
            "링크": {
                "rich_text": [
                    {
                        "type": "mention",
                        "mention": {
                            "type": "page",
                            "page": {"id": page_id} 
                        }
                    }
                ]
            },
            "작성자": {
                "people": [{"id": uid}]
            },
            "날짜": {
                "date": {"start": write_date}

            },
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    return response.status_code == 200


def send_email(receiver_email_list, body, yesterday):
    # 설정
    smtp_server = os.environ.get('SMTP_SERVER')
    port = os.environ.get('SMTP_PORT')
    sender_email = os.environ.get('SENDER_EMAIL')
    pw = os.environ.get('SENDER_PW')

    # 메시지 생성
    message = MIMEMultipart()
    message["From"] = sender_email
    message["Subject"] = f"연구노트 업데이트 목록 ({yesterday})"
    message.attach(MIMEText(body, "html"))

    for receiver_email in receiver_email_list:
        message["To"] = receiver_email

        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, pw)
            server.sendmail(sender_email, receiver_email, message.as_string())


def main(reciver_email_list, now=None):
    """
    변수 입력 양식
        - now: str="20251217"
    """
    # users = get_user_list()
    results = search_recent_pages()
    if results:
        yesterday_pages = filter_yesterday_updates(results=results, now=now)
        
        # 이메일 body 생성
        now = get_now(now=now)
        yesterday = now - timedelta(days=1)
        
        yesterday_email = f"{yesterday.month}/{yesterday.day}"
        write_date = f"{yesterday.year}-{yesterday.month:02d}-{yesterday.day:02d}"
        body = []

        spaces_8 = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        spaces_2 = "&nbsp;&nbsp;"

        for num, page in enumerate(yesterday_pages):
            title = extract_title(page)
            page_url = page['url']
            page_id = page['id']
            uid = extract_user_id(page)

            kst = ZoneInfo("Asia/Seoul")
            last_edited_utc = datetime.fromisoformat(page['last_edited_time'].replace('Z', '+00:00'))
            last_edited_kst = last_edited_utc.astimezone(kst)

            # 노션 입력
            add_to_db(title, page_id, uid, write_date)

            page_contents = f"<b>{num+1}. {spaces_2}{title}</b> <br> {spaces_8}{page_url} <br>{spaces_8} ({last_edited_kst.strftime('%Y-%m-%d %H:%M:%S')} (KST))<br><br>"
            body.append(page_contents)

        # 이메일 발송
        if len(yesterday_pages):
            send_email(reciver_email_list, "\n\n".join(body), yesterday_email)


if __name__=="__main__":
    """
    reciver_email_list: list
    now: None or string(yyyymmdd)
    """
    reciver_email_list = ["test@example.com"]
    now = None
    
    main(reciver_email_list=reciver_email_list, 
         now=now)