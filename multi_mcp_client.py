import asyncio
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# .env 파일 로드
load_dotenv()

def print_help():
    """도움말 출력"""
    print("\n" + "="*50)
    print("📋 사용 가능한 명령어:")
    print("  - 'help': 도움말 보기")
    print("  - 'history': 대화 히스토리 보기")
    print("  - 'clear': 대화 히스토리 초기화")
    print("  - 'quit' 또는 'exit': 종료")
    print("="*50)
    print("💡 카드 추천 예시:")
    print("  - '지하철 카드 추천해줘'")
    print("  - '연회비가 낮은 카드 알려줘'")
    print("  - '해외여행 카드 추천해줘'")
    print("  - '현대카드 중에서 추천해줘'")
    print("  - 'KT 통신 카드 추천해줘'")
    print("="*50)
    print("🎁 이벤트 정보 예시:")
    print("  - '현재 진행중인 이벤트 알려줘'")
    print("  - '신한카드 이벤트 정보 보여줘'")
    print("  - '카드 발급 이벤트 있나요?'")
    print("="*50)

def print_history(conversation_history):
    """대화 히스토리 출력"""
    if not conversation_history:
        print("\n대화 히스토리가 없습니다.")
        return
    
    print("\n" + "="*50)
    print("📝 대화 히스토리:")
    print("="*50)
    
    for i, message in enumerate(conversation_history, 1):
        if isinstance(message, HumanMessage):
            print(f"{i}. 사용자: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"{i}. AI: {message.content}")
        print("-" * 30)

async def main():

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ 오류: GOOGLE_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일을 생성하고 GOOGLE_API_KEY를 설정해주세요:")
        print("   GOOGLE_API_KEY=your-api-key-here")
        return

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

    tools = await client.get_tools()

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

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # 최신 Gemini 2.5 Flash 모델
        google_api_key=google_api_key,
        temperature=0.1
    )
    agent = create_react_agent(llm, tools, prompt=prompt)

    conversation_history = []
    
    print("🎉 안녕하세요! 신한카드 전문 어시스턴트입니다.")
    print("💳 다양한 카드 정보를 검색하고 추천받을 수 있습니다.")
    print("🎁 이벤트 정보도 함께 제공합니다.")
    print("💡 'help'를 입력하면 사용법을 확인할 수 있습니다.")
    print("=" * 50)

    while True:
                try:
                    # 사용자 입력 받기
                    user_input = input("\n💬 사용자: ").strip()
                    
                    # 종료 조건 확인
                    if user_input.lower() in ['quit', 'exit', '종료']:
                        print("\n👋 대화를 종료합니다. 감사합니다!")
                        break
                    
                    # 도움말
                    if user_input.lower() in ['help', '도움말']:
                        print_help()
                        continue
                    
                    # 대화 히스토리 보기
                    if user_input.lower() in ['history', '히스토리']:
                        print_history(conversation_history)
                        continue
                    
                    # 대화 히스토리 초기화
                    if user_input.lower() in ['clear', '초기화']:
                        conversation_history = []
                        print("\n🗑️ 대화 히스토리가 초기화되었습니다.")
                        continue
                    
                    if not user_input:
                        continue
                    
                    # 대화 히스토리에 사용자 메시지 추가
                    conversation_history.append(HumanMessage(content=user_input))
                    
                    print("🤔 AI가 생각하고 있습니다...")
                    
                    # 에이전트에 전체 대화 히스토리 전달
                    agent_response = await agent.ainvoke({"messages": conversation_history})
                    
                    # AI 응답을 대화 히스토리에 추가
                    ai_message = agent_response["messages"][-1]  # 마지막 메시지가 AI 응답
                    conversation_history.append(ai_message)
                    
                    # AI 응답 출력
                    print(f"\n🤖 AI: {ai_message.content}")
                    
                except KeyboardInterrupt:
                    print("\n\n👋 대화를 종료합니다. 감사합니다!")
                    break
                except Exception as e:
                    print(f"\n❌ 오류가 발생했습니다: {e}")
                    print("🔄 다시 시도해주세요.")

if __name__ == "__main__":
    asyncio.run(main())