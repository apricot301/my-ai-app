import os
import json
import datetime
import streamlit as st
from openai import OpenAI

# 1. API 키 불러오기
try:
    NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

st.set_page_config(page_title="My Multi-AI Hub", page_icon="🚀", layout="wide")
st.title("🚀 나만의 최상위 AI 비서")

if not NVIDIA_API_KEY:
    st.error("API 키가 설정되지 않았습니다.")
    st.stop()

# 2. 클라이언트 설정
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

# 3. 💡 멀티 채팅방(다중 세션) 저장용 데이터베이스 관리
HISTORY_FILE = "multi_chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 전체 데이터베이스 불러오기
if "db" not in st.session_state:
    st.session_state.db = load_history()

# --- 사이드바 (메뉴 및 채팅방 관리) ---
with st.sidebar:
    st.header("⚙️ 모델 설정")
    selected_label = st.selectbox("1️⃣ 사용할 모델 선택:", list(MODELS.keys()))
    selected_model = MODELS[selected_label]
    
    st.divider()
    st.header("📂 채팅방 관리")
    
    # 해당 모델의 데이터 방이 없으면 '기본 대화방'을 하나 만듭니다.
    if selected_model not in st.session_state.db:
         st.session_state.db[selected_model] = {"기본 대화방": []}
         save_history(st.session_state.db)
    
    # 현재 선택된 모델의 채팅방 목록 가져오기
    model_db = st.session_state.db[selected_model]
    room_names = list(model_db.keys())
    
    # 💡 과거 대화방(A대화, B대화)을 마음대로 선택해서 넘나드는 메뉴
    selected_room = st.selectbox("2️⃣ 대화방(주제) 선택:", room_names)
    
    # 새 대화방 만들기 버튼
    if st.button("➕ 새 대화방 만들기", use_container_width=True):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_room_name = f"새 대화 ({now})"
        st.session_state.db[selected_model][new_room_name] = []
        save_history(st.session_state.db)
        st.rerun() # 화면 새로고침

    # 현재 대화방 삭제 버튼
    if st.button("🗑️ 현재 대화방 지우기", use_container_width=True):
        if len(room_names) > 1:
            del st.session_state.db[selected_model][selected_room]
        else:
            st.session_state.db[selected_model][selected_room] = [] # 마지막 방은 내용만 삭제
        save_history(st.session_state.db)
        st.rerun()

    st.divider()
    # 전체 기록 다운로드
    chat_data = json.dumps(st.session_state.db, ensure_ascii=False, indent=2)
    st.download_button(
        label="💾 모든 기록 다운로드 (백업)",
        data=chat_data,
        file_name="all_models_history.json",
        mime="application/json",
        use_container_width=True
    )

# --- 💡 메인 채팅 화면 (선택된 모델의, 선택된 방의 대화만 보여줌) ---
# 짧은 변수로 지정하여 코드 가독성 높임
messages = st.session_state.db[selected_model][selected_room]

for message in messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 사용자 입력 및 응답 ---
if prompt := st.chat_input(f"'{selected_room}'에 메시지 보내기..."):
    # 사용자 질문 저장
    messages.append({"role": "user", "content": prompt})
    save_history(st.session_state.db)

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
                    for m in messages
                ],
                temperature=0.7,
                stream=True  
            )
            
            for chunk in stream_response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # AI 답변 저장
            messages.append({"role": "assistant", "content": full_response})
            save_history(st.session_state.db)
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
