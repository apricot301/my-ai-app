import os
import json
import streamlit as st
from openai import OpenAI

# 1. API 키 불러오기
try:
    NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

st.set_page_config(page_title="My AI Hub", page_icon="✨", layout="wide")

if not NVIDIA_API_KEY:
    st.error("API 키가 설정되지 않았습니다.")
    st.stop()

# 2. 클라이언트 및 💡 새롭게 구성된 7개 모델 라인업
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

MODELS = {
    "👑 Nemotron 3 Ultra (550B)": "nvidia/nemotron-3-ultra-550b-a55b",
    "⚡ DeepSeek V4 Flash": "deepseek-ai/deepseek-v4-flash",
    "🤖 GLM 5.2 (Zhipu AI)": "z-ai/glm-5.2",
    "💻 MiniMax M3": "minimaxai/minimax-m3",
    "🌐 GPT OSS 120B": "openai/gpt-oss-120b",
    "🌟 Gemma 4 (31B IT)": "google/gemma-4-31b-it",
    "🏊 Poolside Laguna XS": "poolside/laguna-xs-2.1"
}

# 3. 데이터베이스 (대화 기록) 관리
HISTORY_FILE = "chatgpt_style_history.json"

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

# 💡 앱 최초 실행 시 '새 대화(빈 창)' 상태로 세팅
if "current_model_label" not in st.session_state:
    default_label = list(MODELS.keys())[0]
    st.session_state.current_model_label = default_label
    st.session_state.sidebar_model_select = default_label
    st.session_state.main_model_radio = default_label

if "current_room" not in st.session_state:
    st.session_state.current_room = None # None이면 '빈 대화창'을 의미함

# 💡 모델 변경 시 발생하는 이벤트 (무조건 새 대화창으로 리셋)
def handle_model_change(new_label):
    st.session_state.current_model_label = new_label
    st.session_state.sidebar_model_select = new_label
    st.session_state.main_model_radio = new_label
    st.session_state.current_room = None # 모델 바꾸면 새 대화창 띄우기

def sync_model_main(): handle_model_change(st.session_state.main_model_radio)
def sync_model_sidebar(): handle_model_change(st.session_state.sidebar_model_select)

# 현재 선택된 모델 ID 가져오기 (DB 생성)
current_model_id = MODELS[st.session_state.current_model_label]
if current_model_id not in st.session_state.db:
    st.session_state.db[current_model_id] = {}

# --- ⚙️ 왼쪽 사이드바 (모델 선택 및 Tree 메뉴) ---
with st.sidebar:
    st.selectbox("🚀 AI 엔진 선택", list(MODELS.keys()), key="sidebar_model_select", on_change=sync_model_sidebar)
    
    # 새 대화 시작 버튼 (ChatGPT의 상단 'New Chat' 버튼 역할)
    if st.button("➕ 새 대화 시작", use_container_width=True, type="primary"):
        st.session_state.current_room = None
        st.rerun()
        
    st.divider()
    st.markdown(f"### 🗂️ {st.session_state.current_model_label.split(' ')[1]} 대화 목록")
    
    # 💡 Tree 메뉴 역할 (과거 대화 목록을 최신순으로 정렬)
    room_names = list(st.session_state.db[current_model_id].keys())
    options = ["➕ 현재 새 대화 중..."] + list(reversed(room_names))
    
    # 라디오 버튼 상태 동기화
    if st.session_state.current_room in options:
        st.session_state.room_radio = st.session_state.current_room
    else:
        st.session_state.room_radio = "➕ 현재 새 대화 중..."
        
    def on_room_change():
        if st.session_state.room_radio == "➕ 현재 새 대화 중...":
            st.session_state.current_room = None
        else:
            st.session_state.current_room = st.session_state.room_radio

    # Tree 메뉴 출력
    st.radio("과거 대화", options, key="room_radio", on_change=on_room_change, label_visibility="collapsed")
    
    st.divider()
    # 현재 보고 있는 과거 대화 삭제 기능
    if st.session_state.current_room is not None:
        if st.button("🗑️ 이 대화 삭제", use_container_width=True):
            del st.session_state.db[current_model_id][st.session_state.current_room]
            save_history(st.session_state.db)
            st.session_state.current_room = None
            st.rerun()

    # 페르소나 설정 (숨김 처리 형태)
    with st.expander("🛠️ 고급 설정 (페르소나)"):
        system_prompt = st.text_area("AI 역할 부여", value="당신은 유능하고 친절한 AI 어시스턴트입니다.")

# --- 💬 메인 화면 (빈 화면 또는 과거 대화) ---
# [Perplexity 스타일] 대화창 바로 위 도구 모음
tool_col1, tool_col2 = st.columns(2)
file_content = ""

with tool_col1:
    short_name = st.session_state.current_model_label.split(' ')[1] 
    with st.popover(f"🚀 현재 엔진: {short_name}", use_container_width=True):
        st.radio("대화할 AI 빠른 전환", list(MODELS.keys()), key="main_model_radio", on_change=sync_model_main)

with tool_col2:
    with st.popover("📎 파일 / 음성 입력", use_container_width=True):
        st.write("📄 **문서 첨부 (txt, csv, md)**")
        uploaded_file = st.file_uploader("문서를 올려주세요", type=['txt', 'csv', 'md'], label_visibility="collapsed")
        if uploaded_file:
            file_content = uploaded_file.getvalue().decode('utf-8')
            st.success("✅ 파일 인식 완료!")
        st.divider()
        st.write("🎙️ **음성 입력**")
        audio_val = st.audio_input("음성 녹음", label_visibility="collapsed")

# 💡 대화창 표시 로직 (새 대화 vs 기존 대화)
if st.session_state.current_room is None:
    # 1. 처음 켰거나 새 대화를 누른 경우: 빈 대화창 UI
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>무엇을 도와드릴까요?</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray;'>선택된 AI: {st.session_state.current_model_label}</p><br><br>", unsafe_allow_html=True)
    messages = []
else:
    # 2. Tree 메뉴에서 과거 대화를 선택한 경우: 대화 내역 출력
    messages = st.session_state.db[current_model_id][st.session_state.current_room]
    for message in messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])

# 퀵 프롬프트 (새 대화일 때만 표시)
quick_prompt = None
if st.session_state.current_room is None:
    q_col1, q_col2, q_col3 = st.columns(3)
    if q_col1.button("🔍 코드 리뷰", use_container_width=True): quick_prompt = "코드의 오류나 개선점을 찾아줘."
    if q_col2.button("📝 3줄 요약", use_container_width=True): quick_prompt = "지금까지의 대화 내용을 3줄로 핵심만 요약해 줘."
    if q_col3.button("🌐 영어 번역", use_container_width=True): quick_prompt = "방금 네가 한 대답을 비즈니스 영어로 번역해 줘."

# --- 🚀 사용자 입력 및 AI 응답 ---
prompt = st.chat_input("메시지를 입력하세요...") or quick_prompt

if prompt:
    # 💡 첫 질문 시 자동으로 방 제목(Tree 메뉴 이름) 생성
    if st.session_state.current_room is None:
        title = prompt[:15] + "..." if len(prompt) > 15 else prompt
        
        # 중복 이름 방지
        base_title = title
        counter = 1
        while title in st.session_state.db[current_model_id]:
            title = f"{base_title} ({counter})"
            counter += 1
            
        st.session_state.current_room = title
        st.session_state.db[current_model_id][title] = []
        messages = st.session_state.db[current_model_id][title]

    # 시스템 프롬프트 업데이트
    if not messages or messages[0].get("role") != "system" or messages[0].get("content") != system_prompt:
        messages = [m for m in messages if m["role"] != "system"]
        messages.insert(0, {"role": "system", "content": system_prompt})

    # 첨부 파일 내용 융합
    display_prompt = prompt
    actual_prompt = prompt
    if file_content:
        actual_prompt = f"다음 문서 내용을 참고해서 답변해 줘:\n\n{file_content}\n\n[내 질문]: {prompt}"
        display_prompt = f"📄 *(문서 첨부됨)* {prompt}"
    if audio_val:
        display_prompt = f"🎙️ *(음성 첨부됨)* {prompt}"

    # 사용자 질문 저장 및 출력
    messages.append({"role": "user", "content": actual_prompt})
    save_history(st.session_state.db)

    with st.chat_message("user"):
        st.write(display_prompt)

    # AI 응답 처리
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
            
            # AI 답변 저장
            messages.append({"role": "assistant", "content": full_response})
            st.session_state.db[current_model_id][st.session_state.current_room] = messages
            save_history(st.session_state.db)
            
            st.rerun() # 제목 생성을 위해 화면을 즉시 새로고침
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
