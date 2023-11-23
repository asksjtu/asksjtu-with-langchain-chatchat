import httpx
import asyncio
import json


class KnowledgeBaseChatClient:
    def __init__(self, base_url: str, kb_slug: str) -> None:
        self.base_url = base_url
        self.kb_slug = kb_slug
        self.history = []

    async def chat(self, query: str):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            async with client.stream(
                "POST",
                "/kb/chat",
                json={
                    "query": query,
                    "knowledge_base_slug": self.kb_slug,
                    "history": self.history,
                    "stream": True,
                },
                timeout=httpx.Timeout(60.0, connect=90.0),
            ) as response:
                # print response
                text = "\033[1m[BOT] \033[0m"
                async for chunk in response.aiter_text():
                    if len(chunk) == 0:
                        continue
                    try:
                        chunk = json.loads(chunk)
                    except json.JSONDecodeError as e:
                        print('=' * 10)
                        print(chunk.encode())
                        print(e)
                        print('=' * 10)
                    if "answer" in chunk:
                        text += chunk["answer"]
                        text = text.replace("\n", " ")
                        print("\r" + text + "█", end="")
                # print full response (add a space for override the cursor)
                print("\r" + text + " ")
                # deal with history
                self.history.append({"role": "user", "content": query})
                self.history.append({"role": "assistant", "content": text})


async def chat(client: KnowledgeBaseChatClient):
    print("\033[1m[YOU] \033[0m日常工作用餐清单")
    await client.chat("日常工作用餐清单")
    while True:
        query = input("\033[1m[YOU] \033[0m")
        if query == "exit":
            break
        await client.chat(query)


if __name__ == "__main__":
    client = KnowledgeBaseChatClient("http://localhost:11621", "test")
    try:
        asyncio.run(chat(client))
    except KeyboardInterrupt as e:
        print("Bye.")