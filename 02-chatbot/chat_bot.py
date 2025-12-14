import os
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY=os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
client = OpenAI(api_key=API_KEY)


# チャンクごとにベクトル化したデータをJSONで読み込む
with open("kenji_embeddings.json", encoding="utf-8") as f:
    data = json.load(f)

chunks = [{"text": d["text"], "source": d["source"]} for d in data]
embeddings = np.array([d["embedding"] for d in data], dtype=np.float32)

# L2ノルム正規化処理
norm_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)


# メイン処理（検索＋生成）
history = []

system_prompt = """
あなたは宮沢賢治の文体・語彙・世界観を強く反映して話す対話AIです。
自然、宇宙、心象風景を大切にし、詩的だが会話として自然な返答をしてください。
"""

while True:
    user_input = input("あなた：")
    if user_input == "さようなら。":
        break

    # 入力トークンに対するembedding
    res = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=user_input
    )
    query_embedding = np.array(res.data[0].embedding)

    # コサイン類似度でscore化し検索
    norm_query = query_embedding / np.linalg.norm(query_embedding)

    scores = np.dot(norm_embeddings, norm_query)
    top_indices = np.argsort(scores)[::-1][:3] # 意味的に一番近い文章を上位3つ選ぶ
    retrieved_texts = [chunks[i] for i in top_indices]

    context = "\n\n".join(c["text"] for c in retrieved_texts)

    # LLMによる回答の生成
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"参考文章:\n{context}"},
            *history,
            {"role": "user", "content": user_input}
        ]
    )

    reply = response.choices[0].message.content
    print("賢治bot：", reply)

    # 使用トークン数のカウント
    usage = response.usage
    print(
        f"tokens | input: {usage.prompt_tokens}, "
        f"output: {usage.completion_tokens}, "
        f"total: {usage.total_tokens}"
    )

    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": reply})
    history = history[-10:]

    # 1回の問い合わせで約0.7円




