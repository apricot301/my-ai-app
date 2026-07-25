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

st.set_page_config(page_title="My Multi-AI Hub", page_icon="🤖", layout="wide")
st.title("🤖 My Private AI Assistant")

if not NVIDIA_API_KEY:
    st.error("API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해 주세요.")
    st.stop()

# 2. OpenAI 클라이언트 초기화
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# 3. 💡 핵심: NVIDIA 서버에서 내 키로 쓸 수 있는 '모든 모델 목록' 실시간 가져오기
@st.cache_data(ttl=3600)
def get_model_list():
    try:
        models = client.models.list()
        # 서버에서 받아온 진짜 모델 ID들을 알파벳 순으로 정렬해서 반환
        return sorted([m.id for m in models.data])
    except Exception as e:
        return ["minimaxai/minimax-m3"] # 실패 시 작동 확인된 모델만 출력

all_models = get_model_list()

# --- 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 모델 설정")
    st.success("NVIDIA 서버와 연결되었습니다!")
    # 수동 입력 대신, 서버에서 가져온 전체 모델을 드롭다운으로 표시
    selected_model = st.selectbox("사용할 AI 모델을 선택하세요:", all_models)
    
    st.divider()
    if st.button("🗑️ 대화 내역 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 대화 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 사용자 입력 및 스트리밍 응답 처리 ---
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
