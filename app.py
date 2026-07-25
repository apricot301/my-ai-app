import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# .env 환경변수 로드
load_dotenv()

# 웹페이지 기본 설정
st.set_page_config(page_title="My Multi-AI Hub", page_icon="🤖", layout="wide")
st.title("🤖 My Private AI Assistant")

# NVIDIA API 키 설정 (클라우드 및 로컬 모두 지원)
NVIDIA_API_KEY = st.secrets.get("NVIDIA_API_KEY", os.getenv("NVIDIA_API_KEY"))
if not NVIDIA_API_KEY:
    st.error(".env 파일에 NVIDIA_API_KEY가 설정되어 있지 않습니다.")
    st.stop()

# 클라이언트 초기화
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# 지원할 AI 모델 목록
MODELS = {
    "⚡ DeepSeek V4 Flash (초고속 추론)": "deepseek-v4-flash",
    "🧠 Qwen 3.5 397B (고급 추론/지식)": "qwen3.5-397b-a17b",
    "💻 MiniMax M3 (코드 작성/디버깅)": "minimax-m3",
    "🔗 Kimi K2.6 (긴 텍스트/에이전트)": "kimi-k2.6",
    "🤖 GLM 5.1 (일상 대화)": "glm-5.1"
}

# --- 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 모델 설정")
    selected_label = st.selectbox("사용할 AI 모델을 선택하세요:", list(MODELS.keys()))
    selected_model = MODELS[selected_label]
    
    st.divider()
    if st.button("🗑️ 대화 내역 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 대화 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내역 화면에 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 사용자 입력 및 스트리밍 응답 처리 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    # 1. 사용자 질문 세션 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 2. AI 응답 스트리밍 출력
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # 글자가 업데이트될 빈 공간 생성
        full_response = ""
        
        try:
            # 💡 핵심: stream=True 옵션 추가
            stream_response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=0.7,
                stream=True  
            )
            
            # 💡 핵심: 응답(chunk)이 도착할 때마다 실시간으로 화면 업데이트
            for chunk in stream_response:
                # 데이터가 비어있지 않은 경우에만 처리
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    # 끝에 깜빡이는 커서(▌)를 달아서 타이핑되는 느낌을 줍니다.
                    message_placeholder.markdown(full_response + "▌")
            
            # 스트리밍이 끝나면 커서를 지우고 최종 텍스트만 출력
            message_placeholder.markdown(full_response)
            
            # 3. 완성된 AI 답변을 대화 세션에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
