"""Reddit source adapter — discover & fetch Reddit posts/comments (Phase 1)."""

from typing import Any

from app.adapters.base import SourceAdapter, register
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept-Language": "en-US,en;q=0.9"
}

class RedditAdapter(SourceAdapter):
    """Adapter for Reddit data sources."""

    @property
    def name(self) -> str:
        return "reddit"

    async def discover(self, source_config: dict) -> list[str]:
        """提取Reddit帖子URL。

        Args:
            source_config (dict): _description_

        Raises:
            ValueError: _description_
            ValueError: _description_

        Returns:
            list[str]: _description_
        """
        urls = []
        base_url = source_config.get("base_url")
        if base_url:
            # 深度：source.config["depth"] = 条数倍数（默认 1，Reddit 上限 100）
            depth = int(self._config.get("depth") or 1)
            request_url = f"{base_url}/new.json?limit={min(25 * depth, 100)}"
            
            async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout()) as client:
                response = await client.get(request_url)
                if response.status_code == 200:
                    for child in response.json()["data"]["children"]:
                        permalink = child["data"]["permalink"]
                        urls.append(f"https://www.reddit.com{permalink}")
                else:
                    raise ValueError("Invalid URL")
                return urls
        else:
            raise ValueError("Reddit base_url is not specified")

    async def fetch(self, url: str) -> dict[str, Any]:
        """接收帖子的 URL，请求该 URL 的 JSON 数据。返回包含帖子和评论的字典。

        Args:
            url (str): _description_

        Raises:
            ValueError: _description_

        Returns:
            dict[str, Any]: _description_
        """
        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout()) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                listing = data[0]["data"]["children"][0]["data"]
                comments_listing = data[1]["data"]["children"]
                return {
                    "listing": listing,
                    "comments_listing": comments_listing
                }
            else:
                raise ValueError("Invalid URL")


    async def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """解析原始字典数据为标准数据格式。

        Args:
            raw (dict[str, Any]): _description_

        Returns:
            dict[str, Any]: _description_
        """
        post_data = raw["listing"]
        
        parse_data = {
            "source_item_id": f"t3_{post_data['id']}",
            "url": f"https://www.reddit.com{post_data['permalink']}",
            "title": post_data["title"],
            "content": post_data["selftext"],
            "published_at": post_data["created_utc"],
            "engagement_score": post_data["score"] + post_data["num_comments"],
            "author": post_data["author"],
        }
        return parse_data


register("reddit", RedditAdapter)


