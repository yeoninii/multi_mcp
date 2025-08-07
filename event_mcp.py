import json
import os
import sys
from pathlib import Path
from fastmcp.server import FastMCP, Context
from typing import List, Dict, Any, Optional

# 전역 데이터 저장
EVENT_DATA = []

def load_event_data():
    """이벤트 데이터를 로드합니다."""
    global EVENT_DATA
    print("🔄 [MCP] 이벤트 데이터 로딩 시작...")
    
    event_path = Path(__file__).parent / "resource" / "event.json"
    print(f"📁 이벤트 파일 경로: {event_path}")
    
    try:
        with open(event_path, "r", encoding="utf-8") as f:
            EVENT_DATA = json.load(f)
        print(f"✅ [MCP] 이벤트 데이터 로드 완료: {len(EVENT_DATA)}개 이벤트")
    except FileNotFoundError:
        print(f"❌ [MCP] 이벤트 파일을 찾을 수 없습니다: {event_path}")
        EVENT_DATA = []
    except json.JSONDecodeError as e:
        print(f"❌ [MCP] JSON 파싱 오류: {e}")
        EVENT_DATA = []
    except Exception as e:
        print(f"❌ [MCP] 이벤트 데이터 로드 실패: {e}")
        EVENT_DATA = []

# 데이터 로드
load_event_data()

# MCP 서버 초기화
event_mcp = FastMCP(
    "EventSearchServer",
    instructions="""
    진행중인 이벤트 데이터를 검색하는 서비스입니다.
    
    이벤트 관련 질문이 들어오면 get_event_data를 사용하여 이벤트 데이터를 가져와 가장 적절한 이벤트를 선택합니다.
    해당 이벤트를 시작날짜 종료 날짜와 함께 사용자에게 알려줍니다.
    
    mobWbEvtNm : 이벤트 제목
    mobWbEvtStd : 이벤트 시작 날짜
    mobWbEvtEdd : 이벤트 종료 날짜    
    """
)

@event_mcp.tool(
    name="get_event_data",
    description="진행중인 이벤트 데이터를 가져옵니다.",
    tags=["search"],
)
async def get_event_data(ctx: Context) -> List[Dict[str, Any]]:
    """신한카드 이벤트 데이터를 가져옵니다."""
    print(f"🔍 [MCP] get_event_data 함수 진입")
    await ctx.debug(f"🔍 get_event_data 함수 진입")
    
    return EVENT_DATA

if __name__ == "__main__":
    print("🚀 [DEBUG] MCP 서버 시작 - EventSearchServer")
    event_mcp.run(transport="stdio")