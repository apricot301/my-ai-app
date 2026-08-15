import os
import datetime
import streamlit as st
from openai import OpenAI
from supabase import create_client, Client

st.set_page_config(page_title="My AI Hub", page_icon="✨", layout="wide")

# 1. API 키 및 Supabase 비밀키 불러오기
try:
    NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception as e:
    st.error("Streamlit Secrets에 NVIDIA_API_KEY, SUPABASE_URL, SUPABASE_KEY 설정을 확인해 주세요.")
    st.stop()

# 2. 클라이언트 초기화
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# 3. 💡 최신화된 모델 라인업 (DeepSeek 삭제, 신규 모델 2종 추가, Nemotron 3.5 최상단 배치)
MODELS = {
    "⚡ Nemotron 3.5 Lightning (30B)": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "👑 Nemotron 3 Ultra (550B)": "nvidia/nemotron-3-ultra-550b-a55b",
    "✨ Muse Glimmer (30B)": "meta/muse-glimmer-30b",
    "🤖 GLM 5.2 (Zhipu AI)": "z-ai/glm-5.2",
    "💻 MiniMax M3": "minimaxai/minimax-m3",
    "🌐 GPT OSS 120B": "openai/gpt-oss-120b",
    "🌟 Gemma 4 (31B IT)": "google/gemma-4-31b-it",
    "🏊 Poolside Laguna XS": "poolside/laguna-xs-2.1"
}

# 4. 💾 Supabase DB 읽기 / 쓰기 함수 (강력 방어벽 적용)
def load_history_from_db():
    try:
        res = supabase.table("chat_history").select("data").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("data", {})
        else:
            return {} 
    except Exception as e:
        st.error(f"🚨 데이터베이스(Supabase)가 수면 모드이거나 응답하지 않습니다.\n데이터 증발을 막기 위해 앱 구동을 일시 정지합니다.\n\n[해결방법] Supabase 대시보드에 로그인해서 'Restore Project'를 눌러 서버를 깨워주세요!\n상세 오류: {e}")
        st.stop() 

def save_history_to_db(data):
    try:
        supabase.table("chat_history").update({"data": data}).eq("id", 1).execute()
    except Exception as e:
        st.error(f"DB 데이터 저장 오류: {e}")

# 세션 상태 DB 로드
if "db" not in st.session_state:
    st.session_state.db = load_history_from_db()

# 최초 실행 시 상태 설정 (항상 빈 화면으로 시작)
if "current_model_label" not in st.session_state:
    default_label = list(MODELS.keys())[0] # 자동으로 첫 번째 모델(Nemotron 3.5)이 선택됨
    st.session_state.current_model_label = default_label
    st.session_state.sidebar_model_select = default_label
    st.session_state.main_model_radio = default_label

if "current_room" not in st.session_state:
    st.session_state.current_room = None

# 모델 변경 이벤트
def handle_model_change(new_label):
    st.session_state.current_model_label = new_label
    st.session_state.sidebar_model_select = new_label
    st.session_state.main_model_radio = new_label
    st.session_state.current_room = None

def sync_model_main(): handle_model_change(st.session_state.main_model_radio)
def sync_model_sidebar(): handle_model_change(st.session_state.sidebar_model_select)

current_model_id = MODELS[st.session_state.current_model_label]
if current_model_id not in st.session_state.db:
    st.session_state.db[current_model_id] = {}

# --- ⚙️ 왼쪽 사이드바 ---
with st.sidebar:
    st.selectbox("🚀 AI 엔진 선택", list(MODELS.keys()), key="sidebar_model_select", on_change=sync_model_sidebar)
    
    if st.button("➕ 새 대화 시작", use_container_width=True, type="primary"):
        st.session_state.current_room = None
        st.rerun()
        
    st.divider()
    st.markdown(f"### 🗂️ {st.session_state.current_model_label.split(' ')[1]} 대화 목록")
    
    room_names = list(st.session_state.db[current_model_id].keys())
    options = ["➕ 현재 새 대화 중..."] + list(reversed(room_names))
    
    if st.session_state.current_room in options:
        st.session_state.room_radio = st.session_state.current_room
    else:
        st.session_state.room_radio = "➕ 현재 새 대화 중..."
        
    def on_room_change():
        if st.session_state.room_radio == "➕ 현재 새 대화 중...":
            st.session_state.current_room = None
        else:
            st.session_state.current_room = st.session_state.room_radio

    st.radio("과거 대화", options, key="room_radio", on_change=on_room_change, label_visibility="collapsed")
    
    st.divider()
    if st.session_state.current_room is not None:
        if st.button("🗑️ 이 대화 삭제", use_container_width=True):
            del st.session_state.db[current_model_id][st.session_state.current_room]
            save_history_to_db(st.session_state.db)
            st.session_state.current_room = None
            st.rerun()

    with st.expander("🛠️ 고급 설정 (페르소나)"):
        system_prompt = st.text_area("AI 역할 부여", value="당신은 유능하고 친절한 AI 어시스턴트입니다.")

# --- 💬 메인 화면 ---
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

if st.session_state.current_room is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>무엇을 도와드릴까요?</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray;'>선택된 AI: {st.session_state.current_model_label}</p><br><br>", unsafe_allow_html=True)
    messages = []
else:
    messages = st.session_state.db[current_model_id][st.session_state.current_room]
    for message in messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])

quick_prompt = None
if st.session_state.current_room is None:
    q_col1, q_col2, q_col3 = st.columns(3)
    if q_col1.button("🔍 코드 리뷰", use_container_width=True): quick_prompt = "코드의 오류나 개선점을 찾아줘."
    if q_col2.button("📝 3줄 요약", use_container_width=True): quick_prompt = "지금까지의 대화 내용을 3줄로 핵심만 요약해 줘."
    if q_col3.button("🌐 영어 번역", use_container_width=True): quick_prompt = "방금 네가 한 대답을 비즈니스 영어로 번역해 줘."

# --- 🚀 사용자 입력 및 AI 응답 처리 ---
prompt = st.chat_input("메시지를 입력하세요...") or quick_prompt

if prompt:
    if st.session_state.current_room is None:
        title = prompt[:15] + "..." if len(prompt) > 15 else prompt
        base_title = title
        counter = 1
        while title in st.session_state.db[current_model_id]:
            title = f"{base_title} ({counter})"
            counter += 1
            
        st.session_state.current_room = title
        st.session_state.db[current_model_id][title] = []
        messages = st.session_state.db[current_model_id][title]

    if not messages or messages[0].get("role") != "system" or messages[0].get("content") != system_prompt:
        messages = [m for m in messages if m["role"] != "system"]
        messages.insert(0, {"role": "system", "content": system_prompt})

    display_prompt = prompt
    actual_prompt = prompt
    if file_content:
        actual_prompt = f"다음 문서 내용을 참고해서 답변해 줘:\n\n{file_content}\n\n[내 질문]: {prompt}"
        display_prompt = f"📄 *(문서 첨부됨)* {prompt}"
    if audio_val:
        display_prompt = f"🎙️ *(음성 첨부됨)* {prompt}"

    messages.append({"role": "user", "content": actual_prompt})
    save_history_to_db(st.session_state.db)

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
            save_history_to_db(st.session_state.db)
            
            st.rerun() 
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
