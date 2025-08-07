import json
import os
import sys
from pathlib import Path
from fastmcp.server import FastMCP, Context
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


# 전역 데이터 저장
CARD_DATA = []
BENEFIT_KEYWORDS = {}

def load_card_data():
    """카드 데이터와 키워드 데이터를 로드합니다."""
    global CARD_DATA, BENEFIT_KEYWORDS
    print("🔄 [MCP] 카드 데이터 로딩 시작...")
    
    # shcard.json 로드
    shcard_path = Path(__file__).parent / "resource" / "shcard.json"
    try:
        with open(shcard_path, "r", encoding="utf-8") as f:
            CARD_DATA = json.load(f)
        print(f"✅ [MCP] 카드 데이터 로드 완료: {len(CARD_DATA)}개 카드")
    except Exception as e:
        print(f"❌ [MCP] 카드 데이터 로드 실패: {e}")
        CARD_DATA = []
    
    # benefit_keywords.json 로드
    keywords_path = Path(__file__).parent / "resource" / "benefit_keywords.json"
    try:
        with open(keywords_path, "r", encoding="utf-8") as f:
            BENEFIT_KEYWORDS = json.load(f)
        print(f"✅ [MCP] 키워드 데이터 로드 완료: {len(BENEFIT_KEYWORDS)}개 키워드")
    except Exception as e:
        print(f"❌ [MCP] 키워드 데이터 로드 실패: {e}")
        BENEFIT_KEYWORDS = []

    print(f"🎉 [MCP] 데이터 로딩 완료 - {len(CARD_DATA)}개 카드, {len(BENEFIT_KEYWORDS)}개 키워드")


load_card_data()

# MCP 서버 초기화
card_mcp = FastMCP(
    "CardSearchServer", 
    instructions='''
    특정 카드 정보 및 혜택 기반으로 카드 찾기를 제공하는 서버입니다.

    **혜택 기반 검색**
    사용자의 질문이 혜택기반 질문이면
    - get_available_benefit_keysords를 호출하여 상세 키워드 얻습니다. 사용자의 질문에 들어있는 키워드가 상세키워드랑 반드시 일치해야할 필요는 없습니다. 예를 들어 사용자의 질문이 "무이자할부"라면 상세키워드는 "무이자"가 될 수 있습니다.
    - search_cards_by_benefit 를 사용하여 혜택 키워드로 카드를 검색합니다.

    **연회비 기반 검색**
    사용자의 질문이 연회비 기반 질문이면
    - search_cards_by_annual_fee 를 사용하여 연회비 기준으로 카드를 검색합니다.

    **카드 정보**
    사용자의 질문이 카드 이름 기반 질문이면
    - get_all_cards_with_name 를 사용하여 모든 카드의 이름을 가져와 알맞은 카드를 선택합니다.
    - get_card_info를 사용하여 카드 상세 정보를 가져와 사용자의 질문에 대답합니다.

    **특정 카드 혜택 검색**
    특정 카드에 대한 헤택을 묻는 질문이라면
    - get_all_cards_with_name 사용하여 카드 url를 가져옵니다.
    - get_card_info를 사용하여 카드 상세 정보를 가져와 사용자의 질문에 대답합니다.


    주의사항:
    - 위의 4가지의 경우에 해당하지 않는다면 get_all_cards_with_name를 사용하여 전체 카드 리스트를 살펴보고 사용자의 질문에 대답합니다.
    - 카드 정보에 대해서 물을 떄에는 get_card_info를 사용하여 상세 정보를 반드시 가져와야합니다.
    - 정보를 제공할 때에는 카드 정보와 혜택 정보를 함께 제공해야하며 url만 제공하지 마세요.
    '''
)

@card_mcp.tool(
        name="get_all_cards_with_name",
        description="모든 카드의 이름을(name, url, idx)를 가져옵니다.",
        tags=["search"],
)
async def get_all_cards_with_name(ctx: Context) -> List[dict]:
    """모든 카드의 기본 정보(name, url, idx)를 가져옵니다."""
    print(f"🔍 [MCP] get_all_cards_with_name 함수 진입")
    await ctx.debug(f"🔍 get_all_cards_with_name 함수 진입")
    
    cards_info = []
    for card in CARD_DATA:
        cards_info.append({
            "name": card.get("name", ""),
            "url": card.get("url", ""),
            "idx": card.get("idx", 0)
        })
    print(cards_info)

    print(f"✅ [MCP] get_all_cards_with_name 완료 - {len(cards_info)}개 카드 반환")
    await ctx.debug(f"✅ get_all_cards_with_name 완료 - {len(cards_info)}개 카드 반환")
    return cards_info

@card_mcp.tool(
        name="get_available_benefit_keysords",
        description="사용 가능한 모든 혜택 키워드 목록을 반환합니다.",
        tags=["search"],
)
async def get_available_benefit_keysords(ctx: Context) -> List[str]:
    """사용 가능한 모든 혜택 키워드 목록을 반환합니다."""
    print(f"🔍 [MCP] get_available_benefit_keysords 함수 진입")
    await ctx.debug(f"🔍 get_available_benefit_keysords 함수 진입")
    
    result = BENEFIT_KEYWORDS
    print(f"✅ [MCP] get_available_benefit_keysords 완료 - {len(result) if isinstance(result, list) else 'dict'} 반환")
    await ctx.debug(f"✅ get_available_benefit_keysords 완료 - {len(result) if isinstance(result, list) else 'dict'} 반환")
    return result

@card_mcp.tool(
        name="search_cards_by_benefit",
        description="혜택 키워드로 카드를 검색합니다. get_available_benefit_keysords를 이용하여 사용 가능한 혜택 키워드를 얻어오세요.",
        tags=["search"],
)
async def search_cards_by_benefit(benefit_keyword: str, ctx: Context) -> Dict[str, Any]:
    """혜택 키워드로 카드를 검색합니다.
    
    Args:
        benefit_keyword: get_available_benefit_keysords로 얻어온 혜택 키워드 중 하나를 입력하세요.
    """
    print(f"🔍 [MCP] search_cards_by_benefit 함수 진입 - keyword: '{benefit_keyword}'")
    await ctx.debug(f"🔍 search_cards_by_benefit 함수 진입 - keyword: '{benefit_keyword}'")

    if benefit_keyword not in BENEFIT_KEYWORDS:
        print(f"❌ [MCP] search_cards_by_benefit - 키워드 '{benefit_keyword}'가 존재하지 않음")
        await ctx.debug(f"❌ search_cards_by_benefit - 키워드 '{benefit_keyword}'가 존재하지 않음")
        return {"error": "혜택 키워드가 존재하지 않습니다."}
    
    matching_cards = []
    
    for card in CARD_DATA:
        if benefit_keyword in card.get('benefit_keywords', []):
            matching_cards.append(card)
            continue

    result = {
        "query": benefit_keyword,
        "total_matches": len(matching_cards),
        "cards": matching_cards
    }
    
    print(f"✅ [MCP] search_cards_by_benefit 완료 - '{benefit_keyword}'로 {len(matching_cards)}개 카드 검색됨")
    await ctx.debug(f"✅ search_cards_by_benefit 완료 - '{benefit_keyword}'로 {len(matching_cards)}개 카드 검색됨")
    return result


@card_mcp.tool(
        name="search_cards_by_annual_fee",
        description="연회비 기준으로 카드를 검색합니다. 연회비는 최대 연회비를 기준으로 검색합니다.",
        tags=["search"],
)
async def search_cards_by_annual_fee(max_fee:int, ctx: Context):
    print(f"🔍 [MCP] search_cards_by_annual_fee 함수 진입 - max_fee: {max_fee}")
    await ctx.debug(f"🔍 search_cards_by_annual_fee 함수 진입 - max_fee: {max_fee}")
    
    filtered_cards = []

    for card in CARD_DATA:
        annual_fees = card.get('annual_fees', [])
        if annual_fees:
            min_fee = min([int(fee) for fee in annual_fees])
            if min_fee <= max_fee:
                filtered_cards.append(card)
        else:
            filtered_cards.append(card)

    print(f"✅ [MCP] search_cards_by_annual_fee 완료 - {max_fee}원 이하 {len(filtered_cards)}개 카드 검색됨")
    await ctx.debug(f"✅ search_cards_by_annual_fee 완료 - {max_fee}원 이하 {len(filtered_cards)}개 카드 검색됨")
    return filtered_cards


@card_mcp.tool(
    name="get_card_info",
    description="특정 카드의 상세 정보(이름, 혜택)을 URL을 통해 가져옵니다. **중요: 카드 데이터서에 제공되는 url만 사용해야합니다. 임의의 웹사이트 URL은 사용할 수 없습니다.",
    tags=["search"],
)
async def get_card_info(url: str, ctx: Context) -> dict:
    '''
    카드 상세 정보를 가져오는 도구입니다.
    'CardList' 리소스에서 가져온 URL을 사용하여 카드 상세 정보를 조회할 수 있습니다.
    

    parameters:
    - url: 카드 상세 정보 url

    return: json
    {
        "card_name": 카드 이름,
        "url": 카드 상세 정보 url,
        "benefits": 카드 혜택 정보
    }
    '''
    print(f"🔍 [MCP] get_card_info 함수 진입 - url: {url}")
    await ctx.debug(f"🔍 get_card_info 함수 진입 - url: {url}")
    
    # URL 유효성 검사: CARD_DATA에 해당 URL이 있는지 확인
    if CARD_DATA is None:
        print(f"❌ [MCP] get_card_info - 카드 데이터가 로드되지 않음")
        await ctx.debug(f"❌ get_card_info - 카드 데이터가 로드되지 않음")
        return {"error": "카드 데이터가 로드되지 않았습니다."}
    
    # CARD_DATA가 리스트인지 확인
    if not isinstance(CARD_DATA, list):
        print(f"❌ [MCP] get_card_info - 카드 데이터 형식이 올바르지 않음")
        await ctx.debug(f"❌ get_card_info - 카드 데이터 형식이 올바르지 않음")
        return {"error": "카드 데이터 형식이 올바르지 않습니다."}
    
    # 입력된 URL이 CARD_DATA에 있는지 확인
    url_exists = False
    card_name = ""
    selected_card = None
    for card in CARD_DATA:
        if isinstance(card, dict) and card.get("url") == url:
            url_exists = True
            card_name = card.get("name", "알 수 없는 카드")
            selected_card = card
            break
    
    if not url_exists:
        print(f"❌ [MCP] get_card_info - URL '{url}'이 카드 데이터에 존재하지 않음")
        await ctx.debug(f"❌ get_card_info - URL '{url}'이 카드 데이터에 존재하지 않음")
        return {"error": f"입력된 URL '{url}'이 카드 데이터에 존재하지 않습니다. 유효한 카드 URL을 입력해주세요."}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector("div.bene_area", timeout=30000)
            await page.wait_for_selector("strong.card", timeout=30000)
            
            benefit_buttons_selector = "div.bene_area > dl > dt"
            buttons = await page.query_selector_all(benefit_buttons_selector)
            

            print(f"총 {len(buttons)}개의 혜택을 클릭하여 펼칩니다...")
            for button in buttons:
                await button.click()
                await page.wait_for_timeout(500)

            # 4. 모든 정보가 표시된 최종 HTML 컨텐츠 추출
            html_content = await page.content()

            # 5. BeautifulSoup을 이용해 데이터 정제 및 구조화
            soup = BeautifulSoup(html_content, "html.parser")

            card_name_element = soup.select_one("strong.card")
            card_name = card_name_element.text.strip() if card_name_element else "알 수 없는 카드"

            benefits_data = []
            # # 열려있는 혜택 섹션(li.on)을 순회
            benefit_sections = soup.select("div.bene_area > dl")

            print(f"총 {len(benefit_sections)}개의 리스트를 가져 왔습니다.")
            for dl in benefit_sections:
                category = dl.select_one("p.txt1").text.strip()
                summary = dl.select_one("i").text.strip()
                

                # 상세 정보(<dd>)는 있을 수도, 없을 수도 있습니다.
                details_tag = dl.select_one("dd")
                details = details_tag.get_text(separator="\n", strip=True) if details_tag else "상세 설명 없음"
                
                benefits_data.append({
                    'category': category,
                    'summary': summary,
                    'details': details
                })
            

            # 6. 최종 JSON 결과 생성
            result = {**selected_card, "benefits": benefits_data}
            #result = {"card_name": card_name, "url": url, "benefits": benefits_data}
            
            print(f"✅ [MCP] get_card_info 완료 - '{card_name}' 카드 정보 수집 완료")
            await ctx.debug(f"✅ get_card_info 완료 - '{card_name}' 카드 정보 수집 완료")
            
        except Exception as e:
            print(f"❌ [MCP] get_card_info - 데이터 처리 중 오류: {e}")
            await ctx.debug(f"❌ get_card_info - 데이터 처리 중 오류: {e}")
            result = {"error": f"데이터 처리 중 오류 발생: {e}"}

        finally:
            await browser.close()

        return result

if __name__ == "__main__":
    card_mcp.run(transport="stdio")
