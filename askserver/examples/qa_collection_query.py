import httpx


class QACollectionQueryClient:
    def __init__(self, base_url: str, slug: str) -> None:
        self.base_url = base_url
        self.slug = slug
        self.history = []

    def query(self, text: str):
        with httpx.Client(base_url=self.base_url) as client:
            resp = client.post("/qa/query", json={"query": text, "slug": self.slug})
            data = resp.json()
            qas = data["qas"]
            for qa in qas:
                print(f"\033[1m[{qa['score']}] \033[0m" + qa["question"])


def query(client: QACollectionQueryClient):
    print("\033[1m[YOU] \033[0m日常工作用餐清单")
    client.query("日常工作用餐清单？")
    while True:
        query = input("\033[1m[YOU] \033[0m")
        if query == "exit":
            break
        client.query(query)


if __name__ == "__main__":
    client = QACollectionQueryClient(
        "http://127.0.0.1:11620",
        "9b80d371a44c9dce4db55ac57305b6ec05d2dff1a8a0ed0297c8515b8dbfcda9",
    )
    try:
        query(client)
    except KeyboardInterrupt as e:
        print("Bye.")
