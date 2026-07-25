import os
import streamlit as st
from openai import OpenAI

# 1. API 키 안전하게 불러오기
try:
    NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

st.set_page_config(page_title="My Multi-AI Hub", page_icon="🚀", layout="wide")
st.title("🚀 나만의 최상위 AI 비서")

if not NVIDIA_API_KEY:
    st.error("API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해 주세요.")
    st.stop()

# 2. OpenAI 클라이언트 초기화
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# 3. 💡 요청하신 5개 모델 목록 적용
MODELS = {
    "👑 Nemotron 3 Ultra (550B)": "nvidia/nemotron-3-ultra-550b-a55b",
    "🔗 Kimi K2.6 (Moonshot)": "moonshotai/kimi-k2.6",
    "⚡ DeepSeek V4 Pro": "deepseek-ai/deepseek-v4-pro",
    "🤖 GLM 5.2 (Zhipu AI)": "z-ai/glm-5.2",
    "💻 MiniMax M3": "minimaxai/minimax-m3"
}

# --- 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 모델 설정")
    selected_label = st.selectbox("사용할 모델을 선택하세요:", list(MODELS.keys()))
    selected_model = MODELS[selected_label]
    
    st.info(f"선택된 엔진:\n`{selected_model}`")
    
    st.divider()
    if st.button("🗑️ 대화 내역 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 대화 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 사용자 입력 및 응답 처리 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
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
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
            st.warning("💡 모델 권한 오류인 경우: build.nvidia.com 에서 해당 모델을 검색 후 'Agree to Terms(약관 동의)' 버튼을 눌러주세요.")
