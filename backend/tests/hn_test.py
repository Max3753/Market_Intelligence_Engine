import asyncio
from app.adapters.hn import HackerNewsAdapter

async def test():
    a = HackerNewsAdapter()
    urls = await a.discover({})
    print(f"发现 {len(urls)} 个帖子")
    print("第一个:", urls[0])
    raw = await a.fetch(urls[0])
    doc = await a.parse(raw)
    print(doc)
    
if __name__ == "__main__":
    asyncio.run(test())