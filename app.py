import os
import json # 💡 파일 저장을 위한 라이브러리 추가
import streamlit as st
from openai import OpenAI

# (API 키 불러오기 설정 등은 기존과 동일...)
try:
    NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

st.set_page_config(page_title="My Multi-AI Hub", page_icon="🚀", layout="wide")
st.title("🚀 나만의 최상위 AI 비서")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

MODELS = {
    "👑 Nemotron 3 Ultra (550B)": "nvidia/nemotron-3-ultra-550b-a55b",
    "🔗 Kimi K2.6 (Moonshot)": "moonshotai/kimi-k2.6",
    "⚡ DeepSeek V4 Pro": "deepseek-ai/deepseek-v4-pro",
    "🤖 GLM 5.2 (Zhipu AI)": "z-ai/glm-5.2",
    "💻 MiniMax M3": "minimaxai/minimax-m3"
}

# 💡 핵심: 대화 내용을 파일(JSON)로 저장하고 불러오는 함수
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# --- 대화 세션 상태 초기화 및 불러오기 ---
if "messages" not in st.session_state:
    # 앱을 처음 켤 때 파일에서 대화 내용을 읽어옵니다.
    st.session_state.messages = load_history()

# --- 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 모델 설정")
    selected_label = st.selectbox("사용할 모델을 선택하세요:", list(MODELS.keys()))
    selected_model = MODELS[selected_label]
    
    st.divider()
    if st.button("🗑️ 대화 내역 모두 지우기", use_container_width=True):
        st.session_state.messages = []
        save_history([]) # 파일도 깨끗하게 비웁니다
        st.rerun()

# 이전 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 사용자 입력 및 응답 처리 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_history(st.session_state.messages) # 질문할 때마다 자동 저장

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            stream_response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=0.7,
                stream=True  
            )
            
            for chunk in stream_response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_history(st.session_state.messages) # 답변이 끝나도 자동 저장
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
