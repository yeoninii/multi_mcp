from card_mcp import card_mcp
from event_mcp import event_mcp
from fastmcp.server import FastMCP


main_mcp = FastMCP("MainMCP")

# 새로운 mount 방식 사용
main_mcp.mount(card_mcp)
main_mcp.mount(event_mcp)

if __name__ == "__main__":
    main_mcp.run(transport="http", host="127.0.0.1", port=8000)