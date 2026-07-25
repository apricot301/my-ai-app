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
st.title("🚀 나만의 최상위 멀티모달 AI 비서")

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

# 3. 데이터베이스 관리
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

if "db" not in st.session_state:
    st.session_state.db = load_history()

# --- 사이드바 (방 관리 및 💡편의기능: 페르소나 설정) ---
with st.sidebar:
    st.header("⚙️ 기본 설정")
    selected_label = st.selectbox("1️⃣ 사용할 모델 선택 (언제든 변경 가능):", list(MODELS.keys()))
    selected_model = MODELS[selected_label]
    
    # 🎁 편의기능 1: AI 역할(페르소나) 부여
    system_prompt = st.text_area(
        "🧠 AI 페르소나 (역할 부여)", 
        value="당신은 도움이 되는 친절한 AI 어시스턴트입니다.",
        help="예: '너는 20년 차 부동산 투자 전문가야', '너는 파이썬 자동화 스크립트 작성 전문가야'"
    )
    
    st.divider()
    st.header("📂 채팅방 관리")
    
    if selected_model not in st.session_state.db:
         st.session_state.db[selected_model] = {"기본 대화방": []}
         save_history(st.session_state.db)
    
    model_db = st.session_state.db[selected_model]
    room_names = list(model_db.keys())
    selected_room = st.selectbox("2️⃣ 대화방(주제) 선택:", room_names)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 새 방 만들기", use_container_width=True):
            now = datetime.datetime.now().strftime("%m-%d %H:%M")
            st.session_state.db[selected_model][f"새 대화 ({now})"] = []
            save_history(st.session_state.db)
            st.rerun()
    with col2:
        if st.button("🗑️ 현재 방 지우기", use_container_width=True):
            if len(room_names) > 1:
                del st.session_state.db[selected_model][selected_room]
            else:
                st.session_state.db[selected_model][selected_room] = []
            save_history(st.session_state.db)
            st.rerun()

# --- 메인 채팅 화면 ---
messages = st.session_state.db[selected_model][selected_room]

for message in messages:
    # 시스템 프롬프트는 화면에 표시하지 않음
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# 🎁 편의기능 2: 단축 프롬프트 버튼
st.markdown("💡 **빠른 질문 (클릭하면 바로 입력됩니다)**")
quick_col1, quick_col2, quick_col3 = st.columns(3)
quick_prompt = None
if quick_col1.button("🔍 파이썬 코드 리뷰해 줘", use_container_width=True): quick_prompt = "작성한 파이썬 코드를 리뷰하고, 오류나 개선점을 알려줘."
if quick_col2.button("📝 대화 내용 요약해 줘", use_container_width=True): quick_prompt = "지금까지의 대화 내용을 3줄로 핵심만 요약해 줘."
if quick_col3.button("🌐 영어로 번역해 줘", use_container_width=True): quick_prompt = "방금 네가 한 대답을 자연스러운 비즈니스 영어로 번역해 줘."

# --- 입력창 주변 도구 모음 (파일업로드 & 음성인식) ---
file_content = ""
with st.popover("📎 첨부 및 도구 (파일 / 음성)"):
    st.write("**파일 업로드 (텍스트, CSV, Markdown)**")
    uploaded_file = st.file_uploader("파일을 올려주시면 AI가 읽고 대답합니다.", type=['txt', 'csv', 'md'])
    if uploaded_file:
        file_content = uploaded_file.getvalue().decode('utf-8')
        st.success("✅ 파일 내용이 준비되었습니다! 입력창에 질문을 남겨주세요.")
    
    st.divider()
    st.write("**🎙️ 음성 입력 (Streamlit 최신 기능)**")
    # Streamlit 1.38+ 에 추가된 오디오 입력 (현재는 녹음본을 저장/재생하는 UI 제공)
    audio_val = st.audio_input("음성 녹음하기")
    if audio_val:
        st.info("💡 녹음이 완료되었습니다. (참고: 음성을 텍스트로 자동 변환하려면 Whisper STT API 연동이 추가로 필요합니다.)")

# --- 사용자 입력 및 응답 ---
# 사용자가 직접 타이핑하거나 퀵 버튼을 누른 경우 처리
prompt = st.chat_input(f"'{selected_room}' 방에 메시지 보내기...") or quick_prompt

if prompt:
    # 시스템 프롬프트가 설정되어 있다면, 대화 시작(또는 변경) 시 AI에게 몰래 주입
    if not messages or messages[0].get("role") != "system" or messages[0].get("content") != system_prompt:
        # 기존 시스템 프롬프트가 있으면 제거하고 새 것으로 업데이트
        messages = [m for m in messages if m["role"] != "system"]
        messages.insert(0, {"role": "system", "content": system_prompt})

    # 파일이 업로드 되어 있다면 프롬프트에 몰래 텍스트를 끼워 넣음
    display_prompt = prompt
    actual_prompt = prompt
    if file_content:
        actual_prompt = f"다음 문서 내용을 참고해서 답변해 줘:\n\n[문서 내용]\n{file_content}\n\n[내 질문]\n{prompt}"
        display_prompt = f"📄 *(문서 첨부됨)* {prompt}"

    messages.append({"role": "user", "content": actual_prompt})
    st.session_state.db[selected_model][selected_room] = messages
    save_history(st.session_state.db)

    with st.chat_message("user"):
        st.write(display_prompt)

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
            
            messages.append({"role": "assistant", "content": full_response})
            st.session_state.db[selected_model][selected_room] = messages
            save_history(st.session_state.db)
            
        except Exception as e:
            message_placeholder.error(f"오류가 발생했습니다: {e}")
