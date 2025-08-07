#!/usr/bin/env python3
import asyncio
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

# .env 파일 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI(
    title="신한카드 추천 API",
    description="신한카드 추천 및 이벤트 정보를 제공하는 API 서비스",
    version="1.0.0"
)

# 전역 변수로 클라이언트와 에이전트 저장
client = None
agent = None

# 대화 히스토리 저장소 (세션별로 관리)
conversation_sessions = {}

# Pydantic 모델 정의
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    conversation_history: List[Dict[str, str]]

class CardSearchRequest(BaseModel):
    benefit_keyword: Optional[str] = None
    max_annual_fee: Optional[int] = None
    card_name: Optional[str] = None

class EventRequest(BaseModel):
    pass

# API 초기화 함수
async def initialize_services():
    """MCP 클라이언트와 에이전트를 초기화합니다."""
    global client, agent
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise Exception("GOOGLE_API_KEY가 설정되지 않았습니다.")
    
    # MCP 클라이언트 초기화
    client = MultiServerMCPClient(
        {
            "event": {
                "command": "python",
                "args": ["/Users/a80128121/Desktop/mac_mini/project/aicc/event_mcp.py"],
                "transport": "stdio",
            },
            "card": {
                "command": "python",
                "args": ["/Users/a80128121/Desktop/mac_mini/project/aicc/card_mcp.py"],
                "transport": "stdio",
            }
        }
    )
    
    # 도구 로드
    tools = await client.get_tools()
    
    # LLM 초기화
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.1
    )
    
    # 프롬프트 정의
    prompt = '''당신은 신한카드 전문 어시스턴트입니다. 사용자 질문에 대한 친절하고 정확한 답변을 해야합니다.
    
    카드 관련 도구:
    - get_all_cards_with_name: 모든 카드 목록 조회
    - get_available_benefit_keysords: 사용 가능한 혜택 키워드 조회
    - search_cards_by_benefit: 혜택 키워드로 카드 검색
    - search_cards_by_annual_fee: 연회비 기준 카드 검색
    - get_card_info: 특정 카드 상세 정보 조회

    이벤트 관련 도구:
    - get_event_data: 진행중인 이벤트 데이터 조회

    사용 지침:
    1. 사용자의 질문을 정확히 이해하고 적절한 도구를 선택하세요.
    2. 카드, 이벤트 정보가 명확히 들어나지 않을 때는 모든 도구를 사용하여 관련된 카드, 이벤트 정보를 모두 제공해야합니다.
    '''
    
    # 에이전트 생성
    agent = create_react_agent(llm, tools, prompt=prompt)
    
    print("✅ API 서비스 초기화 완료")

# 앱 시작 시 초기화
@app.on_event("startup")
async def startup_event():
    await initialize_services()

# 헬스체크 엔드포인트
@app.get("/")
async def root():
    return {"message": "신한카드 추천 API 서비스가 실행 중입니다.", "status": "healthy"}

# 채팅 API
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """사용자 메시지에 대한 AI 응답을 제공합니다."""
    try:
        if agent is None:
            raise HTTPException(status_code=500, detail="에이전트가 초기화되지 않았습니다.")
        
        session_id = request.session_id
        
        # 세션별 대화 히스토리 가져오기
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
        
        conversation_history = conversation_sessions[session_id]
        
        # 사용자 메시지 추가
        conversation_history.append(HumanMessage(content=request.message))
        
        # 에이전트 실행
        agent_response = await agent.ainvoke({"messages": conversation_history})
        
        # AI 응답 추출
        ai_message = agent_response["messages"][-1]
        conversation_history.append(ai_message)
        
        # 세션에 대화 히스토리 저장
        conversation_sessions[session_id] = conversation_history
        
        # 응답 형식으로 변환
        response_history = []
        for msg in conversation_history:
            if isinstance(msg, HumanMessage):
                response_history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                response_history.append({"role": "assistant", "content": msg.content})
        
        return ChatResponse(
            response=ai_message.content,
            session_id=session_id,
            conversation_history=response_history
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")

# 카드 검색 API
@app.post("/cards/search")
async def search_cards(request: CardSearchRequest):
    """카드 검색 API"""
    try:
        if client is None:
            raise HTTPException(status_code=500, detail="클라이언트가 초기화되지 않았습니다.")
        
        tools = await client.get_tools()
        
        # 검색 조건에 따른 도구 선택
        if request.benefit_keyword:
            # 혜택 키워드로 검색
            search_tool = next((tool for tool in tools if tool.name == "search_cards_by_benefit"), None)
            if search_tool:
                result = await search_tool.ainvoke({"benefit_keyword": request.benefit_keyword})
                return {"type": "benefit_search", "data": result}
        
        elif request.max_annual_fee:
            # 연회비로 검색
            search_tool = next((tool for tool in tools if tool.name == "search_cards_by_annual_fee"), None)
            if search_tool:
                result = await search_tool.ainvoke({"max_fee": request.max_annual_fee})
                return {"type": "annual_fee_search", "data": result}
        
        elif request.card_name:
            # 카드 이름으로 검색
            search_tool = next((tool for tool in tools if tool.name == "get_all_cards_with_name"), None)
            if search_tool:
                result = await search_tool.ainvoke({})
                # 이름으로 필터링
                filtered_cards = [card for card in result if request.card_name.lower() in card.get("name", "").lower()]
                return {"type": "name_search", "data": filtered_cards}
        
        else:
            # 모든 카드 반환
            search_tool = next((tool for tool in tools if tool.name == "get_all_cards_with_name"), None)
            if search_tool:
                result = await search_tool.ainvoke({})
                return {"type": "all_cards", "data": result}
        
        raise HTTPException(status_code=404, detail="적절한 검색 도구를 찾을 수 없습니다.")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카드 검색 중 오류 발생: {str(e)}")

# 이벤트 조회 API
@app.get("/events")
async def get_events():
    """진행중인 이벤트 목록을 조회합니다."""
    try:
        if client is None:
            raise HTTPException(status_code=500, detail="클라이언트가 초기화되지 않았습니다.")
        
        tools = await client.get_tools()
        event_tool = next((tool for tool in tools if tool.name == "get_event_data"), None)
        
        if event_tool:
            result = await event_tool.ainvoke({})
            return {"type": "events", "data": result}
        else:
            raise HTTPException(status_code=404, detail="이벤트 도구를 찾을 수 없습니다.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이벤트 조회 중 오류 발생: {str(e)}")

# 대화 히스토리 조회 API
@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """특정 세션의 대화 히스토리를 조회합니다."""
    try:
        if session_id not in conversation_sessions:
            return {"session_id": session_id, "conversation_history": []}
        
        conversation_history = conversation_sessions[session_id]
        
        # 응답 형식으로 변환
        response_history = []
        for msg in conversation_history:
            if isinstance(msg, HumanMessage):
                response_history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                response_history.append({"role": "assistant", "content": msg.content})
        
        return {
            "session_id": session_id,
            "conversation_history": response_history,
            "message_count": len(response_history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 히스토리 조회 중 오류 발생: {str(e)}")

# 대화 히스토리 삭제 API
@app.delete("/chat/history/{session_id}")
async def delete_chat_history(session_id: str):
    """특정 세션의 대화 히스토리를 삭제합니다."""
    try:
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]
            return {"message": f"세션 '{session_id}'의 대화 히스토리가 삭제되었습니다."}
        else:
            return {"message": f"세션 '{session_id}'가 존재하지 않습니다."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 히스토리 삭제 중 오류 발생: {str(e)}")

# 활성 세션 목록 조회 API
@app.get("/chat/sessions")
async def get_active_sessions():
    """현재 활성화된 세션 목록을 조회합니다."""
    try:
        sessions = []
        for session_id, history in conversation_sessions.items():
            sessions.append({
                "session_id": session_id,
                "message_count": len(history),
                "last_activity": "recent"  # 실제로는 타임스탬프를 저장할 수 있음
            })
        
        return {
            "active_sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"세션 목록 조회 중 오류 발생: {str(e)}")

# 사용 가능한 혜택 키워드 API
@app.get("/benefit-keywords")
async def get_benefit_keywords():
    """사용 가능한 혜택 키워드 목록을 조회합니다."""
    try:
        if client is None:
            raise HTTPException(status_code=500, detail="클라이언트가 초기화되지 않았습니다.")
        
        tools = await client.get_tools()
        keyword_tool = next((tool for tool in tools if tool.name == "get_available_benefit_keysords"), None)
        
        if keyword_tool:
            result = await keyword_tool.ainvoke({})
            return {"type": "benefit_keywords", "data": result}
        else:
            raise HTTPException(status_code=404, detail="혜택 키워드 도구를 찾을 수 없습니다.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"혜택 키워드 조회 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 