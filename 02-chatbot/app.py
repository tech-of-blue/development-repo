import os
import json
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="宮沢賢治 チャットボット", layout="centered")
st.title("宮沢賢治 チャットボット")

# セッション初期化
if "history" not in st.session_state:
    st.session_state.history = []

if "loaded" not in st.session_state:
    with open("kenji_embeddings.json", encoding="utf-8") as f:
        data = json.load(f)

    chunks = [{"text": d["text"], "source": d["source"]} for d in data]
    embeddings = np.array([d["embedding"] for d in data], dtype=np.float32)
    norm_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    st.session_state.chunks = chunks
    st.session_state.norm_embeddings = norm_embeddings
    st.session_state.loaded = True


# システムプロンプト
system_prompt = """
あなたは宮沢賢治の文体・語彙・世界観を強く反映して話す対話AIです。
自然、宇宙、心象風景を大切にし、詩的だが会話として自然な返答をしてください。
"""

# チャット履歴表示
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# ユーザー入力
user_input = st.chat_input("問いかけてください…")

if user_input:
    # ユーザー表示
    with st.chat_message("user"):
        st.write(user_input)

    # ---- embedding ----
    res = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=user_input
    )
    query_embedding = np.array(res.data[0].embedding)
    norm_query = query_embedding / np.linalg.norm(query_embedding)

    # ---- 検索 ----
    scores = np.dot(st.session_state.norm_embeddings, norm_query)
    top_indices = np.argsort(scores)[::-1][:3]
    retrieved_texts = [st.session_state.chunks[i] for i in top_indices]
    context = "\n\n".join(c["text"] for c in retrieved_texts)

    # ---- LLM ----
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"参考文章:\n{context}"},
            *st.session_state.history,
            {"role": "user", "content": user_input}
        ]
    )

    reply = response.choices[0].message.content

    # アシスタント表示
    with st.chat_message("assistant"):
        st.write(reply)

    # 履歴保存
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.session_state.history = st.session_state.history[-10:]
