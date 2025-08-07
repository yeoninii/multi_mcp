import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

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
    # Google API 키 설정 (.env 파일에서 로드)
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ 오류: GOOGLE_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일을 생성하고 GOOGLE_API_KEY를 설정해주세요:")
        print("   GOOGLE_API_KEY=your-api-key-here")
        return
    
    server_params = StdioServerParameters(
        command="python",
        # Make sure to update to the full absolute path to your main.py file
        args=["/Users/a80128121/Desktop/mac_mini/project/aicc/event_mcp.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)

            # Google Gemini 모델 사용
            # 사용 가능한 모델들:
            # - gemini-1.5-flash (빠르고 효율적)
            # - gemini-1.5-pro (더 정확하고 강력)
            # - gemini-2.5-flash (최신 Gemini 2.5 Flash 모델)
            # - gemini-2.5-pro (최신 Gemini 2.5 Pro 모델)
            # - gemini-2.5-flash-lite (비용 효율적인 Gemini 2.5 Flash-Lite)
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",  # 최신 Gemini 2.5 Flash 모델
                google_api_key=google_api_key,
                temperature=0.1
            )

            # Create and run the agent
            agent = create_react_agent(llm, tools)
            
            # 대화 히스토리 초기화
            conversation_history = []
            
            print("🎉 안녕하세요! 카드 추천 도우미입니다.")
            print("💳 다양한 카드 정보를 검색하고 추천받을 수 있습니다.")
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
