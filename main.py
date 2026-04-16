import feedparser
import smtplib
import os
from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. 깃허브 금고에서 정보 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# 2. 메일 수신자 설정
RECEIVER_EMAIL = "ho@kca.kr" 

# 3. Gemini AI 설정 (최신 SDK 방식)
client = genai.Client(api_key=GEMINI_API_KEY)

# 4. 검색할 키워드 세팅 
KEYWORDS = ["6G", "5G", "spectrum", "fcc", "ofcom", "주파수", "전파"]

def fetch_news():
    """구글 뉴스에서 키워드별로 최근 24시간 기사를 수집하고 중복을 제거합니다."""
    unique_news = {}
    for keyword in KEYWORDS:
        url = f"https://news.google.com/rss/search?q={keyword}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]: 
            unique_news[entry.link] = entry.title
    return unique_news

def categorize_and_summarize(news_dict):
    """수집된 뉴스를 AI에 전달하여 5개 국가별 요약 리포트를 생성합니다."""
    prompt = """당신은 전파/통신 정책 전문가를 위한 뉴스 요약 어시스턴트입니다.
    아래 수집된 최신 뉴스들을 [한국, 미국, 일본, 중국, 영국] 5개 국가별로 엄격하게 분류해서 요약해 주세요.

    [요구사항]
    1. 반드시 '한국, 미국, 일본, 중국, 영국' 5개 국가를 각각 대제목(<h3>)으로 작성하세요.
    2. 각 국가별로 관련된 뉴스가 있다면 핵심 내용을 3~4문장으로 요약(<p>)하고, 그 아래에 참고한 기사의 제목과 링크를 리스트(<ul><li><a href="링크">제목</a></li></ul>)로 첨부하세요.
    3. 해당 국가와 관련된 뉴스가 전혀 없다면, 국가 제목 아래에 "<p>최근 24시간 내 주요 이슈 없음</p>"이라고만 작성하세요.
    4. 위 5개 국가에 속하지 않는 뉴스나 관련 없는 내용은 제외하세요.
    5. 결과물은 반드시 이메일 본문에 바로 쓸 수 있는 HTML 코드로만 출력하세요. (```html 같은 마크다운 기호는 절대 쓰지 마세요)

    [수집된 뉴스 목록]\n"""
    
    for link, title in news_dict.items():
        prompt += f"- 제목: {title} (링크: {link})\n"

    # 최신 모델(gemini-2.5-flash) 적용
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    html_content = response.text.replace("```html", "").replace("```", "").strip()
    return html_content

def send_email(content):
    """생성된 HTML 내용을 이메일로 발송합니다."""
    msg = MIMEMultipart()
    msg['Subject'] = "📰 글로벌 전파/통신 일일 동향 리포트 (한국/미국/일본/중국/영국)"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    full_html = f"<h2>오늘의 글로벌 주요 이슈 (최근 24시간)</h2><hr>{content}"
    
    body = MIMEText(full_html, 'html')
    msg.attach(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    print("뉴스 수집 중...")
    news_data = fetch_news()
    
    if news_data:
        print(f"총 {len(news_data)}개의 기사 수집 완료. AI 국가별 요약 중...")
        summary_html = categorize_and_summarize(news_data)
        
        print("이메일 발송 중...")
        send_email(summary_html)
        print("이메일 발송 완료!")
    else:
        print("최근 24시간 내 수집된 뉴스가 없습니다.")
