# 신한카드 추천 AI 서비스

신한카드 추천 및 이벤트 정보를 제공하는 AI 서비스입니다. MCP(Model Context Protocol)를 사용하여 카드 정보와 이벤트 데이터를 검색하고 추천합니다.

## 🚀 주요 기능

- **카드 추천**: 혜택, 연회비, 카드명 등 다양한 조건으로 카드 추천
- **이벤트 정보**: 진행중인 신한카드 이벤트 정보 제공
- **대화형 인터페이스**: 자연어로 카드 추천 요청 가능
- **REST API**: 웹 애플리케이션에서 사용할 수 있는 API 제공

## 📋 요구사항

- Python 3.11+
- Google AI API 키 (Gemini)

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd aicc
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. Playwright 브라우저 설치
```bash
playwright install chromium
```

### 5. 환경변수 설정
`.env` 파일을 생성하고 Google AI API 키를 설정하세요:
```bash
echo "GOOGLE_API_KEY=your-google-ai-api-key-here" > .env
```

## 🎯 사용 방법

### CLI 모드 (대화형)
```bash
# 단일 MCP 서버 사용
python client.py

# 다중 MCP 서버 사용
python multi_mcp_client.py
```

### API 서버 모드
```bash
# API 서버 실행
python api_server.py
```

서버가 실행되면 `http://localhost:8000`에서 API를 사용할 수 있습니다.

## 📚 API 문서

### 주요 엔드포인트

#### 1. 채팅 API
```http
POST /chat
Content-Type: application/json

{
  "message": "지하철 카드 추천해줘",
  "session_id": "user123"
}
```

#### 2. 카드 검색 API
```http
POST /cards/search
Content-Type: application/json

{
  "benefit_keyword": "교통",
  "max_annual_fee": 50000,
  "card_name": "신한카드"
}
```

#### 3. 이벤트 조회 API
```http
GET /events
```

#### 4. 대화 히스토리 관리
```http
GET /chat/history/{session_id}
DELETE /chat/history/{session_id}
GET /chat/sessions
```

### API 테스트
```bash
python api_client_example.py
```

## 🔧 프로젝트 구조

```
aicc/
├── client.py                 # 단일 MCP 클라이언트
├── multi_mcp_client.py       # 다중 MCP 클라이언트
├── api_server.py             # FastAPI 서버
├── api_client_example.py     # API 테스트 클라이언트
├── card_mcp.py              # 카드 MCP 서버
├── event_mcp.py             # 이벤트 MCP 서버
├── requirements.txt          # 의존성 목록
├── .env                     # 환경변수 (API 키)
├── .gitignore               # Git 무시 파일
└── resource/                # 데이터 파일
    ├── shcard.json          # 카드 데이터
    ├── event.json           # 이벤트 데이터
    └── benefit_keywords.json # 혜택 키워드
```

## 🎨 사용 예시

### CLI에서 사용
```
💬 사용자: 지하철 카드 추천해줘
🤖 AI: 교통 혜택이 있는 카드들을 찾아보겠습니다...

💬 사용자: 연회비가 낮은 카드도 알려줘
🤖 AI: 연회비가 낮은 카드들을 검색해보겠습니다...
```

### API에서 사용
```python
import requests

# 채팅 요청
response = requests.post("http://localhost:8000/chat", json={
    "message": "지하철 카드 추천해줘",
    "session_id": "user123"
})

print(response.json()["response"])
```

## 🔍 지원하는 검색 조건

### 카드 검색
- **혜택 키워드**: 교통, 마트, 편의점, 푸드, 영화, 문화, 해외이용 등
- **연회비**: 최대 연회비 기준 검색
- **카드명**: 카드 이름으로 검색
- **브랜드**: VISA, Mastercard 등

### 이벤트 검색
- **진행중인 이벤트**: 현재 진행중인 모든 이벤트
- **이벤트 기간**: 시작일, 종료일 정보

## 🛡️ 보안

- `.env` 파일에 API 키를 저장하고 Git에 포함하지 않습니다
- API 키는 환경변수로 관리됩니다

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🆘 문제 해결

### 일반적인 문제

1. **API 키 오류**: `.env` 파일에 올바른 Google AI API 키가 설정되어 있는지 확인
2. **Playwright 오류**: `playwright install chromium` 실행
3. **포트 충돌**: 다른 서비스가 8000번 포트를 사용 중인지 확인

### 로그 확인
- MCP 서버 로그: 각 MCP 서버 실행 시 디버그 정보 출력
- API 서버 로그: FastAPI 서버 실행 시 로그 확인

## 📞 지원

문제가 발생하면 이슈를 생성해주세요. 