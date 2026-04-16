import feedparser
import smtplib
import os
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 깃허브 금고에서 정보 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# ⭐️ 메일을 받을 주소 (네이버, 다음 등 평소 확인하시는 메일 주소로 수정하세요!)
RECEIVER_EMAIL = "ho@kca.kr" 

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ⭐️ 검색할 키워드 세팅 
KEYWORDS = ["6G", "5G", "spectrum", "fcc", "ofcom", "주파수", "전파"]

def fetch_news(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    return feed.entries[:3] 

def summarize_news(news_list, keyword):
    prompt = f"다음은 '{keyword}' 관련 최신 뉴스 제목과 링크들입니다. 이 이슈들의 핵심 내용을 3~4문장으로 깔끔하게 요약해주세요.\n\n"
    for news in news_list:
        prompt += f"- 제목: {news.title}\n- 링크: {news.link}\n"
    response = model.generate_content(prompt)
    return response.text

def send_email(content):
    msg = MIMEMultipart()
    msg['Subject'] = "📰 오늘의 주요 이슈 요약 리포트"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    body = MIMEText(content, 'html')
    msg.attach(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    email_body = "<h2>오늘의 트렌드 요약</h2><hr>"
    for keyword in KEYWORDS:
        news_items = fetch_news(keyword)
        if news_items:
            summary = summarize_news(news_items, keyword)
            email_body += f"<h3>🔍 {keyword}</h3>"
            email_body += f"<p>{summary.replace(chr(10), '<br>')}</p>"
            email_body += "<ul>"
            for item in news_items:
                 email_body += f"<li><a href='{item.link}'>{item.title}</a></li>"
            email_body += "</ul><br>"
    send_email(email_body)
    print("이메일 발송 완료!")
