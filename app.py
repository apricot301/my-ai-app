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

# 2. 클라이언트 및 모델 설정
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

# 3. 데이터베이스 및 상태 동기화 (Sync) 관리
HISTORY_FILE = "multi_chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if "db" not in st.session_state:
    st.session_state.db = load_history()

# 앱 최초 실행 시 기본 상태(State) 세팅
if "current_model_label" not in st.session_state:
    default_label = list(MODELS.keys())[0]
    st.session_state.current_model_label = default_label
    st.session_state.sidebar_model_select = default_label
    st.session_state.main_model_radio = default_label

# 💡 모델 전환 시 채팅방 목록 에러를 방지하고 두 화면(사이드바/메인)을 동기화하는 핵심 함수
def handle_model_change(new_model_label):
    st.session_state.current_model_label = new_model_label
    st.session_state.sidebar_model_select = new_model_label
    st.session_state.main_model_radio = new_model_label
    
    selected_model_id = MODELS[new_model_label]
    if selected_model_id not in st.session_state.db:
        st.session_state.db[selected_model_id] = {"기본 대화방": []}
        
    room_names = list(st.session_state.db[selected_model_id].keys())
    st.session_state.current_room = room_names[0]
    st.session_state.sidebar_room_select = room_names[0]

def sync_model_main(): handle_model_change(st.session_state.main_model_radio)
def sync_model_sidebar(): handle_model_change(st.session_state.sidebar_model_select)
def sync_room_sidebar(): st.session_state.current_room = st.session_state.sidebar_room_select

# 현재 모델과 방 이름 가져오기
current_model_id = MODELS[st.session_state.current_model_label]
if current_model_id not in st.session_state.db:
    st.session_state.db[current_model_id] = {"기본 대화방": []}

model_db = st.session_state.db[current_model_id]
room_names = list(model_db.keys())

if "current_room" not in st.session_state or st.session_state.current_room not in room_names:
    st.session_state.current_room = room_names[0]
    st.session_state.sidebar_room_select = room_names[0]

# --- ⚙️ 사이드바 (기존 메뉴 유지) ---
with st.sidebar:
    st.header("⚙️ 기본 설정")
    # 사이드바용 모델 선택기
    st.selectbox("1️⃣ 사용할 모델 선택:", list(MODELS.keys()), key="sidebar_model_select", on_change=sync_model_sidebar)
    
    system_prompt = st.text_area("🧠 AI 페르소나 (역할 부여)", value="당신은 도움이 되는 친절한 AI 어시스턴트입니다.")
    
    st.divider()
    st.header("📂 채팅방 관리")
    st.selectbox("2️⃣ 대화방(주제) 선택:", room_names, key="sidebar_room_select", on_change=sync_room_sidebar)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 새 방 만들기", use_container_width=True):
            now = datetime.datetime.now().strftime("%m-%d %H:%M")
            st.session_state.db[current_model_id][f"새 대화 ({now})"] = []
            save_history(st.session_state.db)
            st.rerun()
    with col2:
        if st.button("🗑️ 방 지우기", use_container_width=True):
            if len(room_names) > 1:
                del st.session_state.db[current_model_id][st.session_state.current_room]
            else:
                st.session_state.db[current_model_id][st.session_state.current_room] = []
            save_history(st.session_state.db)
            st.session_state.current_room = list(st.session_state.db[current_model_id].keys())[0]
            st.rerun()

# --- 💬 메인 채팅 화면 ---
messages = st.session_state.db[current_model_id][st.session_state.current_room]

# 과거 대화 내역 출력
for message in messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

st.markdown("<br>", unsafe_allow_html=True) # UI 여백

# --- 🚀 [Perplexity 스타일] 대화창 바로 위 도구 모음 ---
tool_col1, tool_col2 = st.columns(2)
file_content = ""

with tool_col1:
    # 버튼 이름에 현재 모델을 짧게 표시 (예: 🚀 엔진: Nemotron)
    short_name = st.session_state.current_model_label.split(' ')[1] 
    with st.popover(f"🚀 엔진: {short_name}", use_container_width=True):
        st.radio("대화할 AI 빠른 전환", list(MODELS.keys()), key="main_model_radio", on_change=sync_model_main)

with tool_col2:
    with st.popover("📎 파일 / 음성 입력", use_container_width=True):
        st.write("📄 **문서 첨부**")
        uploaded_file = st.file_uploader("문서(txt, csv, md)를 올려주세요", type=['txt', 'csv', 'md'])
        if uploaded_file:
            file_content = uploaded_file.getvalue().decode('utf-8')
            st.success("✅ 파일 인식 완료!")
        
        st.divider()
        st.write("🎙️ **음성 입력**")
        audio_val = st.audio_input("음성으로 질문하기")
        if audio_val:
            st.info("💡 녹음본이 첨부되었습니다.")

# 퀵 프롬프트
quick_col1, quick_col2, quick_col3 = st.columns(3)
quick_prompt = None
if quick_col1.button("🔍 코드 리뷰", use_container_width=True): quick_prompt = "코드의 오류나 개선점을 찾아줘."
if quick_col2.button("📝 3줄 요약", use_container_width=True): quick_prompt = "지금까지의 대화 내용을 3줄로 핵심만 요약해 줘."
if quick_col3.button("🌐 영어 번역", use_container_width=True): quick_prompt = "방금 네가 한 대답을 비즈니스 영어로 번역해 줘."

# --- 사용자 입력 및 응답 ---
prompt = st.chat_input(f"'{st.session_state.current_room}'에 질문하기...") or quick_prompt

if prompt:
    # 시스템 프롬프트 주입 로직
    if not messages or messages[0].get("role") != "system" or messages[0].get("content") != system_prompt:
        messages = [m for m in messages if m["role"] != "system"]
        messages.insert(0, {"role": "system", "content": system_prompt})

    # 첨부 파일 내용 숨겨서 전송하기
    display_prompt = prompt
    actual_prompt = prompt
    if file_content:
        actual_prompt = f"다음 문서 내용을 참고해서 답변해 줘:\n\n[문서 내용]\n{file_content}\n\n[내 질문]\n{prompt}"
        display_prompt = f"📄 *(문서 첨부됨)* {prompt}"
    if audio_val:
        display_prompt = f"🎙️ *(음성 첨부됨)* {prompt}"

    messages.append({"role": "user", "content": actual_prompt})
    st.session_state.db[current_model_id][st.session_state.current_room] = messages
    save_history(st.session_state.db)

    with st.chat_message("user"):
        st.write(display_prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            stream_response = client.chat.completions.create(
                model=current_model_id,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                temperature=0.7,
                stream=True  
            )
            
            for chunk in stream_response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            messages.append({"role": "assistant", "content": full_response})
            st.session_state.db[current_model_id][st.session_state.current_room] = messages
            save_history(st.session_state.db)
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
