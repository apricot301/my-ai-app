import os
import streamlit as st
from openai import OpenAI

# 1. API 키 안전하게 불러오기 (클라우드/로컬 모두 지원)
try:
    NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

st.set_page_config(page_title="My Multi-AI Hub", page_icon="🚀", layout="wide")
st.title("🚀 최상위 AI 통합 비서")

if not NVIDIA_API_KEY:
    st.error("API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해 주세요.")
    st.stop()

# 2. OpenAI 클라이언트 초기화 (NVIDIA 서버로 연결)
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# 3. 💡 엄선된 최상위 고성능 모델 목록 (공식 100% 작동 명칭)
MODELS = {
    "👑 NVIDIA Nemotron 70B (최강 추론/코딩)": "nvidia/llama-3.1-nemotron-70b-instruct",
    "🚀 Meta Llama 3.3 70B (균형잡힌 범용 AI)": "meta/llama-3.3-70b-instruct",
    "🧠 Qwen 2.5 72B (한국어 성능 최우수)": "qwen/qwen2.5-72b-instruct",
    "✍️ Mistral Large 2 (자연스러운 글쓰기)": "mistralai/mistral-large-2-instruct",
    "💻 MiniMax M3 (작동 확인된 백업용)": "minimaxai/minimax-m3"
}

# --- 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 모델 설정")
    selected_label = st.selectbox("사용할 최고급 AI를 선택하세요:", list(MODELS.keys()))
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

# --- 사용자 입력 및 실시간 타이핑(스트리밍) 응답 처리 ---
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
            
            # 실시간 타이핑 애니메이션
            for chunk in stream_response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            # 완성된 답변 출력
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
            st.warning("💡 팁: NVIDIA 사이트에서 해당 모델의 권한(EULA) 동의가 필요할 수 있습니다.")
