import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import PyPDF2, pandas as pd, glob, os, re
import base64
import io

try:
    from PIL import Image
except ImportError:
    pass

st.set_page_config(page_title="개별화된 학생부 입력을 위한 어시스트", layout="wide")

# 상태 유지를 위한 Session State 초기화
for k in ['a1n', 'a1d', 'a2n', 'a2d', 'a3n', 'a3d', 'a4n', 'a4d', 'book_title', 'book_desc']:
    if k not in st.session_state:
        st.session_state[k] = ""

# ===== 0. 교육과정 데이터베이스 (2015 vs 2022 분리) =====
CURRICULUM_DATA_2015 = {
    "국어군": { "국어": ["듣기·말하기의 본질", "읽기의 과정과 방법", "글쓰기의 원리와 과정", "문학의 수용과 생산", "국어의 규범과 변천"], "화법과 작문": ["화법과 작문의 본질/원리", "정보 전달", "설득", "자기 표현과 사회적 상호작용"], "독서": ["독서의 본질", "독서의 방법", "독서의 분야", "독서의 태도", "비판적/추론적 읽기"], "언어와 매체": ["음운과 단어", "문장과 담화", "국어사", "매체의 소통 방식", "매체 자료의 수용과 생산"], "문학": ["문학의 본질", "문학의 갈래와 역사", "문학과 삶", "문학의 인접 분야", "작품의 맥락"] },
    "수학군": { "수학": ["다항식", "방정식과 부등식", "도형의 방정식", "집합과 명제", "함수와 그래프", "경우의 수"], "수학Ⅰ": ["지수함수와 로그함수", "삼각함수", "수열"], "수학Ⅱ": ["함수의 극한과 연속", "미분", "적분"], "미적분": ["수열의 극한", "미분법", "적분법"], "확률과 통계": ["경우의 수", "확률", "통계"], "기하": ["이차곡선", "평면벡터", "공간도형과 공간좌표"] },
    "영어군": { "영어": ["주제·요지 파악", "세부 정보 파악", "논리적 관계 파악", "맥락 추론"], "영어 회화": ["사실적/추론적 이해", "종합적 이해", "표현 및 전달"], "영어Ⅰ": ["맥락/주제 파악", "세부 정보 파악", "함축 의미 추론"], "영어 독해와 작문": ["글의 구조와 논리", "다양한 목적의 글쓰기"] },
    "사회군": { "통합사회": ["인간, 사회, 환경과 행복", "자연환경과 인간", "시장 경제와 금융", "문화와 다양성"], "한국지리": ["국토 인식과 지리 정보", "지형 환경과 생태계", "거주 공간의 변화"], "사회·문화": ["사회·문화 현상의 탐구", "개인과 사회 구조", "현대의 사회 변동"], "생활과 윤리": ["생명과 윤리", "사회와 윤리", "과학과 윤리", "평화와 공존의 윤리"] },
    "과학군": { "통합과학": ["물질의 규칙성", "시스템과 상호작용", "변화와 다양성", "환경과 에너지"], "물리학Ⅰ": ["힘과 운동", "열과 에너지", "전기와 자기", "파동과 정보 통신"], "화학Ⅰ": ["원자의 세계", "화학 결합과 분자의 세계", "역동적인 화학 반응"], "생명과학Ⅰ": ["사람의 물질대사", "항상성과 몸의 조절", "방어 작용", "유전"], "지구과학Ⅰ": ["고체 지구", "대기와 해양", "우주"] },
    "기타(생활/교양/예체능)": { "기술·가정": ["인간 발달과 가족", "기술 시스템"], "정보": ["정보 문화", "문제 해결과 프로그래밍"], "보건": ["건강의 이해", "질병 예방과 관리"], "심리학": ["심리학의 이해", "나의 이해", "타인의 이해"] }
}

CURRICULUM_DATA_2022 = {
    "국어군": { "공통국어1/2": ["듣기·말하기의 본질", "읽기의 과정과 방법", "글쓰기의 원리와 과정", "문학의 수용과 생산"], "화법과 언어": ["화법의 본질과 원리", "국어의 구조와 역사"], "독서와 작문": ["독서의 목적과 방법", "작문의 과정과 원리"], "문학": ["문학의 수용과 생산", "한국 문학의 특질과 흐름"] },
    "수학군": { "공통수학1/2": ["다항식", "방정식과 부등식", "도형의 방정식", "경우의 수"], "대수": ["지수함수와 로그함수", "삼각함수", "수열"], "미적분Ⅰ": ["함수의 극한과 연속", "미분", "적분"], "확률과 통계": ["경우의 수", "확률", "통계"] },
    "영어군": { "공통영어1/2": ["일상적 의사소통", "주제·요지 파악"], "영어 의사소통": ["다양한 상황의 의사소통", "협력적 소통"], "영어 독해와 작문": ["글의 구조와 논리", "목적에 맞는 글쓰기"] },
    "사회군": { "통합사회1/2": ["인간, 사회, 환경과 행복", "인권 보장과 헌법", "시장 경제와 금융"], "세계시민과 지리": ["세계화와 세계시민", "글로벌 환경 문제"], "사회와 문화": ["사회·문화 현상의 탐구", "문화와 일상생활"] },
    "과학군": { "통합과학1/2": ["물질과 규칙성", "시스템과 상호작용", "환경과 에너지"], "물리학": ["힘과 운동", "파동과 정보 통신"], "화학": ["물질의 구성", "화학 반응의 세계"], "생명과학": ["생명 시스템과 조절", "생명 연속성과 다양성"], "지구과학": ["고체 지구", "대기와 해양", "우주"] },
    "기타(생활/교양/예체능)": { "기술·가정": ["인간 발달과 가족"], "정보": ["컴퓨팅 시스템", "알고리즘과 프로그래밍"], "인공지능 기초": ["데이터와 기계학습", "인공지능의 사회적 영향"] }
}

COMPETENCIES_2015 = ["AI에게 알아서 맡기기", "자기관리 역량", "지식정보처리 역량", "창의적 사고 역량", "심미적 감성 역량", "의사소통 역량", "공동체 역량"]
COMPETENCIES_2022 = ["AI에게 알아서 맡기기", "자기관리 역량", "지식정보처리 역량", "창의적 사고 역량", "심미적 감성 역량", "협력적 소통 역량", "공동체 역량"]

# ===== 1. 보조 함수 =====
@st.cache_data(show_spinner=False)
def load_pdfs(pdfs):
    text = ""
    for p in pdfs:
        with open(p, "rb") as f:
            for page in PyPDF2.PdfReader(f).pages:
                t = page.extract_text()
                if t: text += t + "\n"
    return text

@st.cache_data(show_spinner=False)
def load_excel():
    if not os.path.exists("data.xlsx"): return None, None
    try:
        g = pd.read_excel("data.xlsx", sheet_name="가이드북 항목별 주요 내용")
        v = pd.read_excel("data.xlsx", sheet_name="권장 연결 동사")
        return g, v
    except: return None, None

def remove_numbers(text):
    text = re.sub(r'\d+\s*(명|곳|개|편|권|건|점포|장|종|가지|회|차례|번|시간)', '다수', text)
    text = re.sub(r'약\s*다수', '다수', text)
    return text.strip()

def clean(text, subject=""):
    for pat in [r'\*\*(.*?)\*\*', r'\*(.*?)\*', r'__(.*?)__', r'`(.*?)`']:
        text = re.sub(pat, r'\1', text)
    text = re.sub(r'^#+\s*|^[\-\*\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r' +', ' ', text)
    return remove_numbers(text)

def byte_count(text):
    return len(text.encode('utf-8'))

# 🔥 연동 엔진 (오픈라우터 및 네이티브 분기 구조 최적화)
def generate_student_record(api_key, prompt_text, selected_model):
    if api_key.startswith("sk-or-"):
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, default_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "Assist"})
        response = client.chat.completions.create(model=selected_model, max_tokens=2000, messages=[{"role": "user", "content": prompt_text}])
        return response.choices[0].message.content
    else:
        genai.configure(api_key=api_key)
        # 1.5-pro 제외 요청에 따라 네이티브 백엔드도 gemini-3.5-pro로 매핑 교체
        model = genai.GenerativeModel("gemini-3.5-pro")
        response = model.generate_content(prompt_text)
        return response.text

# 🔥 파일 OCR 및 자동 요약 함수
def summarize_uploaded_file(file, api_key, selected_model):
    name = file.name.lower()
    content_text = ""
    img_b64, img_pil = None, None
    try:
        if name.endswith('.txt'): content_text = file.getvalue().decode("utf-8")
        elif name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                ext = page.extract_text()
                if ext: content_text += ext + "\n"
        elif name.endswith(('.png', '.jpg', '.jpeg')):
            file_bytes = file.getvalue()
            img_b64 = base64.b64encode(file_bytes).decode('utf-8')
            if not api_key.startswith("sk-or-"): img_pil = Image.open(io.BytesIO(file_bytes))
    except Exception as e: return f"파일 읽기 오류: {e}"

    sys_prompt = """다음 자료를 분석하여 생기부의 '활동 상세 내용'으로 쓸 수 있도록 3~4문장으로 완벽히 요약하세요.
    1. 핵심 성과, 구체적 탐구 내용, 알게 된 점 추출.
    2. 무조건 '~함', '~임' 명사형 종결어미 사용.
    3. 결과 안내, 인사말, 서론("다음은 요약본입니다" 등)을 절대 출력하지 마세요. 즉시 본문만 출력하세요."""

    if img_b64 and api_key.startswith("sk-or-"):
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, default_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "Assist"})
        response = client.chat.completions.create(model=selected_model, messages=[{"role": "user", "content": [{"type": "text", "text": sys_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}])
        return response.choices[0].message.content
    elif img_pil and not api_key.startswith("sk-or-"):
        genai.configure(api_key=api_key)
        # 요약 엔진도 3.5 pro로 매핑 교체
        model = genai.GenerativeModel("gemini-3.5-pro")
        response = model.generate_content([sys_prompt, img_pil])
        return response.text
    else:
        return generate_student_record(api_key, sys_prompt + "\n\n" + content_text[:15000], selected_model)

# ===== 2. 사이드바 =====
with st.sidebar:
    st.header("🔑 기본 설정")
    api_key = st.text_input("API 키 입력 (Google/OpenRouter)", type="password")
    st.markdown("[🔗 OpenRouter 키 발급](https://openrouter.ai/keys)")
    st.divider()
    
    # 🔥 에러를 유발하는 1.5 버전을 완전히 제외하고, 최신 3.5 버전을 리스트에 세팅
    model_options = {
        "🎁 [무료] OpenAI GPT-OSS 120B": "openai/gpt-oss-120b:free",
        "🎁 [무료] Google Gemma 4 31B": "google/gemma-4-31b-it:free",
        "⚡ [유료] Google Gemini 3.5 Flash": "google/gemini-3.5-flash",
        "🔥 [유료] Anthropic Claude 5 Sonnet": "anthropic/claude-sonnet-5",
        "🧠 [유료] Anthropic Claude 4.8 Opus": "anthropic/claude-opus-4.8",
        "🚀 [유료] DeepSeek V4 Pro": "deepseek/deepseek-v4-pro",
        "💥 [유료] Qwen 3.7 Plus": "qwen/qwen3.7-plus",
        "🔮 [유료] Z-AI GLM 5.2": "z-ai/glm-5.2"
    }
    # 기본값을 Gemini 3.5 Pro (인덱스 3)으로 지정
    selected_model_label = st.selectbox("🤖 사용할 AI 모델 선택 (OpenRouter 전용)", list(model_options.keys()), index=3)
    selected_model = model_options[selected_model_label]
    st.caption("*(참고: 구글 API 키 입력 시에는 자동으로 gemini-3.5-pro 네이티브 모델로 작동합니다)*")
    st.divider()
    
    df_guide, df_verbs = load_excel()
    pdf_files = glob.glob("*.pdf")
    use_pdf = st.checkbox("✅ PDF 가이드북 로드", value=False) if pdf_files else False
    st.divider()
    st.info("🎯 목표: 1420~1470 바이트")

# ===== 3. 메인 화면 =====
st.title("📝 학생부 입력 어시스트")
st.caption("선택한 교육과정과 교과 핵심 키워드를 기반으로 유기적으로 연결된 개별화 학생부 기록이 생성됩니다.")

st.markdown("### 📘 **적용 교육과정 선택**")
curriculum_version = st.radio("적용 교육과정 선택", ["2015 개정 교육과정", "2022 개정 교육과정"], horizontal=True, label_visibility="collapsed")
current_curriculum_data = CURRICULUM_DATA_2015 if curriculum_version == "2015 개정 교육과정" else CURRICULUM_DATA_2022
current_competencies = COMPETENCIES_2015 if curriculum_version == "2015 개정 교육과정" else COMPETENCIES_2022

st.markdown("---")

st.markdown("#### 1. 학생 기본 정보")
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1: aspiration = st.text_input("🎓 진학 희망 학과/계열 ⭐", placeholder="예: 도시공학과 / 사회학과")
with col_b2: focus = st.selectbox(f"🎯 6대 핵심 역량 ({curriculum_version})", current_competencies)
with col_b3: extra = st.text_area("🔍 개별화 강조 포인트", placeholder="예: 탐구력, 자기주도성 강조", height=68)

st.markdown("---")

st.markdown("#### 2. 교과 관련 정보")
col_s1, col_s2, col_s3 = st.columns([1, 1, 2])
with col_s1: subject_group = st.selectbox("📚 교과군 선택", ["직접 입력"] + list(current_curriculum_data.keys()))
with col_s2:
    if subject_group != "직접 입력":
        subject_dropdown = st.selectbox("📖 과목명", ["직접 입력"] + list(current_curriculum_data[subject_group].keys()))
        subject = st.text_input("과목명 직접 입력", label_visibility="collapsed") if subject_dropdown == "직접 입력" else subject_dropdown
    else: subject = st.text_input("📖 과목명 (직접 입력)")
with col_s3:
    concept_options = current_curriculum_data[subject_group][subject] if subject_group != "직접 입력" and subject in current_curriculum_data[subject_group] else []
    selected_concepts = st.multiselect("🧠 교과 핵심 아이디어", concept_options, placeholder="핵심 개념 선택")
    manual_keywords = st.text_input("키워드 직접 입력", placeholder="추가 키워드 작성")
    subject_keywords = " / ".join(filter(None, [", ".join(selected_concepts), manual_keywords.strip()]))

st.markdown("---")

# [섹션 3] 구체적인 활동 입력 및 엑셀 일괄 업로드
st.markdown("#### 3. 구체적인 활동 및 독서 연계 내용")
st.caption("직접 입력, 파일 업로드(OCR 요약), 또는 **엑셀 일괄 업로드를 통한 전체 학생 자동 완성**을 지원합니다.")

with st.expander("📁 엑셀 파일 업로드 및 전체 학생 일괄 자동 생성 패널 (클릭)", expanded=False):
    st.markdown("**[💡 권장 엑셀 양식 열 제목]:** `이름`(학번/성명), `활동명1`, `내용1`, `활동명2`, `내용2`, `도서명`, `독서활동`")
    uploaded_excel = st.file_uploader("학생 명렬표/활동 데이터 파일 업로드", type=['xlsx', 'csv'])
    
    student_list = ["직접 입력 (빈칸으로 초기화)"]
    df_students = None
    name_col = None

    if uploaded_excel:
        try:
            df_students = pd.read_csv(uploaded_excel) if uploaded_excel.name.endswith('.csv') else pd.read_excel(uploaded_excel)
            for col in df_students.columns:
                if any(x in str(col) for x in ['이름', '학번', '성명']): name_col = col; break
            if name_col:
                student_list.extend(df_students[name_col].astype(str).tolist())
                st.success(f"✅ 총 {len(student_list)-1}명의 학생 데이터를 안전하게 인식했습니다.")
            else: st.error("⚠️ 엑셀 첫 번째 행에 '이름', '학번', '성명' 중 하나의 열 제목이 있어야 합니다.")
        except Exception as e: st.error(f"엑셀 파일 읽기 오류: {e}")
    
    # 기능 1: 단건 개별 불러오기
    st.markdown("---")
    st.markdown("#### 👤 방법 A: 학생 1명씩 선택하여 화면에 불러오기")
    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1: selected_student = st.selectbox("데이터 불러올 학생 선택", student_list, label_visibility="collapsed")
    with col_sel2:
        if st.button("⬇️ 화면에 내용 채우기", use_container_width=True):
            for k in ['a1n', 'a1d', 'a2n', 'a2d', 'a3n', 'a3d', 'a4n', 'a4d', 'book_title', 'book_desc']: st.session_state[k] = ""
            if selected_student != "직접 입력 (빈칸으로 초기화)" and df_students is not None and name_col:
                row = df_students[df_students[name_col].astype(str) == selected_student].iloc[0]
                for col in df_students.columns:
                    c = str(col).replace(" ", "")
                    if pd.notna(row[col]):
                        val = str(row[col]).strip()
                        if '활동명1' in c: st.session_state['a1n'] = val
                        elif '내용1' in c: st.session_state['a1d'] = val
                        elif '활동명2' in c: st.session_state['a2n'] = val
                        elif '내용2' in c: st.session_state['a2d'] = val
                        elif '활동명3' in c: st.session_state['a3n'] = val
                        elif '내용3' in c: st.session_state['a3d'] = val
                        elif '활동명4' in c: st.session_state['a4n'] = val
                        elif '내용4' in c: st.session_state['a4d'] = val
                        elif '도서명' in c: st.session_state['book_title'] = val
                        elif '독서' in c: st.session_state['book_desc'] = val
                st.rerun()

    # 🔥 기능 2: 전교생 일괄 생성 및 다운로드 (안내 멘트 절대 차단본)
    st.markdown("---")
    st.markdown("#### 🚀 방법 B: 업로드한 엑셀 내 모든 학생 일괄 자동 생성 및 파일 다운로드")
    
    if st.button("🔥 엑셀 내 모든 학생 일괄 자동 완성 시작", type="secondary", use_container_width=True):
        if not api_key: st.error("API 키를 먼저 입력해 주세요!")
        elif df_students is None: st.error("일괄 작성을 위한 엑셀 파일을 먼저 업로드해 주세요!")
        else:
            batch_box = st.empty()
            progress_bar = st.progress(0)
            total_rows = len(df_students)
            generated_list = []
            
            verbs = df_verbs.to_string(index=False) if df_verbs is not None else ""
            target_byte, target_min, target_max = 1445, 1420, 1470
            
            for index, row in df_students.iterrows():
                s_name = str(row[name_col]) if name_col in row else f"{index+1}번 학생"
                batch_box.info(f"⏳ [{index+1}/{total_rows}] '{s_name}' 학생의 세특 기록 자동 빌드 중...")
                
                b_a1n, b_a1d, b_a2n, b_a2d, b_bk, b_bd = "", "", "", "", "", ""
                for col in df_students.columns:
                    c = str(col).replace(" ", "")
                    if pd.notna(row[col]):
                        val = str(row[col]).strip()
                        if '활동명1' in c: b_a1n = val
                        elif '내용1' in c: b_a1d = val
                        elif '활동명2' in c: b_a2n = val
                        elif '내용2' in c: b_a2d = val
                        elif '도서명' in c: b_bk = val
                        elif '독서' in c: b_bd = val
                
                b_acts = []
                if b_a1n and b_a1d: b_acts.append(f"'{b_a1n}'에 참여하여 {b_a1d}")
                if b_a2n and b_a2d: b_acts.append(f"이와 연계하여 '{b_a2n}' 프로젝트를 통해 {b_a2d}")
                
                b_book_str = f"이후 주제를 한 단계 심화 확장하고자 '{b_bk}'를 분석하고 {b_bd} 탐구하며 학업적 성취를 거둠." if b_bk and b_bd else ""
                
                if not b_acts and not b_book_str:
                    generated_list.append("⚠️ 입력된 활동 및 독서 데이터가 부족하여 작성이 생략되었습니다.")
                    progress_bar.progress((index + 1) / total_rows)
                    continue
                    
                b_prompt = f"""당신은 20년 경력의 고등학교 부장 교사입니다. 다음 원본 데이터를 활용하여 학교생활기록부용 교과세특 문장을 작성하세요.

                🚨 [서술 불변의 철칙] 🚨
                1. 활동 기호 금지: 활동명과 도서명 양옆에 대괄호([ ]), 콜론(:) 등을 절대로 쓰지 마세요. 오직 작은따옴표('')만 사용해야 합니다.
                2. 서술 분량 1:1:1 절대 균형: '활동명1', '활동명2', '도서명'의 탐구 묘사 분량과 중요도를 균등하게 33%씩 배분하세요.
                3. 고유 명칭 누락 차단: '{b_a1n}', '{b_a2n}', '{b_bk}'는 절대로 생략하지 말고 작은따옴표 안에 감싸 문맥에 고스란히 노출하세요.
                4. 독서 연계 종결: 마지막 문장은 반드시 책 '{b_bk}'를 읽고 심화 탐구한 과정으로 장식되어야 합니다.
                5. 메타 발언 및 대화형 응답 금지: "다음은 요약본입니다", "작성된 문장입니다", "공백을 포함하여~" 등과 같은 인사말, 설명, 안내 문구를 절대 쓰지 마세요. 오직 세특 본문만 출력하세요.

                - 어조: 무조건 '~함', '~임', '~됨' 개조식 명사형 종결어미. 주어 생략.
                - 분량: 한글 공백 포함 480~500자 (1420~1470바이트 구간 타격) 필수 요구.

                [기본 데이터]
                - 핵심 키워드: {subject_keywords}
                - 진로 희망: {aspiration}
                
                [활동 서사]
                {" ".join(b_acts)}
                
                [독서 심화 활동 데이터]
                {b_book_str}
                
                → 서론, 결론, 설명문 없이 완벽한 한 단락의 교과세특 결과물 본문만 즉시 출력하세요."""
                
                try:
                    b_raw = generate_student_record(api_key, b_prompt, selected_model)
                    b_res = clean(b_raw.strip(), subject)
                    b_cb = byte_count(b_res)
                    
                    if b_cb < target_min:
                        b_adj = f"문장 분량이 많이 부족합니다. 모든 활동명과 도서명을 작은따옴표('') 안에 명시하면서 1:1 비율로 풍성하게 확장하여 정확히 1450바이트로 교정하세요.\n🚨 주의: 설명, 인사말, 결과 안내(예: '확장된 결과입니다') 문구를 절대 작성하지 마세요. 오직 본문만 출력하세요.\n\n[원본 데이터]\n{b_acts}\n{b_book_str}\n\n[현재 문장]\n{b_res}"
                        b_raw = generate_student_record(api_key, b_adj, selected_model)
                        b_res = clean(b_raw.strip(), subject)
                        b_cb = byte_count(b_res)
                    
                    if b_cb > target_max:
                        sents = re.split(r'(?<=[.!?])\s+', b_res)
                        t_str = ""
                        for s in sents:
                            if byte_count(t_str + (" " if t_str else "") + s) <= target_max: t_str += (" " if t_str else "") + s
                            else: break
                        if t_str: b_res = t_str.strip()
                        
                    generated_list.append(b_res)
                except Exception as b_err:
                    generated_list.append(f"⚠️ 생성 실패: {b_err}")
                
                progress_bar.progress((index + 1) / total_rows)
                
            df_students['⚙️ 생성된_학생부_최종기록'] = generated_list
            batch_box.success("🎉 전교생 세특 일괄 자동 완성이 성공적으로 끝났습니다!")
            
            towrite = io.BytesIO()
            with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
                df_students.to_excel(writer, index=False, sheet_name='최종결과물')
            towrite.seek(0)
            
            st.download_button("📥 일괄 완성된 학생부 엑셀 파일 다운로드 받기", data=towrite, file_name=f"최종본_학생부_일괄완성본.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# 개별 활동 UI 아키텍처
col_act1, col_act2 = st.columns(2)

def render_activity_ui(i, col_obj):
    with col_obj:
        req = "(필수)" if i == 1 else "(선택)"
        st.markdown(f"**🔹 활동 {i} {req}**")
        st.text_input(f"활동명 {i}", key=f"a{i}n", placeholder=f"예: 활동 {i} 주제명", label_visibility="collapsed")
        file_i = st.file_uploader(f"📎 활동 {i} 파일 업로드", type=['pdf', 'txt', 'png', 'jpg', 'jpeg'], key=f"f{i}", label_visibility="collapsed")
        if file_i:
            if st.button(f"✨ 활동 {i} 파일 AI 자동 요약", key=f"b{i}", use_container_width=True):
                if not api_key: st.error("API 키가 필요합니다!")
                else:
                    with st.spinner(f"파일 요약 중..."):
                        summary = summarize_uploaded_file(file_i, api_key, selected_model)
                        st.session_state[f'a{i}d'] = summary
                        st.rerun()
        st.text_area(f"활동 {i} 상세 내용", key=f"a{i}d", placeholder="내용을 쓰거나 파일을 업로드해 요약 버튼을 누르세요.", height=130, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

render_activity_ui(1, col_act1)
render_activity_ui(2, col_act2)

# 독서 연계 심화 활동 UI
st.markdown("---")
st.markdown("#### 📚 독서 연계 심화 활동 (선택)")
st.caption("활동의 연장선상에서 탐구한 도서가 있다면 기재하세요. 생성 시 유기적으로 연결됩니다.")
col_bk1, col_bk2 = st.columns([1, 2])
with col_bk1:
    st.text_input("도서명", key="book_title", placeholder="예: 이기적 유전자 (리처드 도킨스)")
with col_bk2:
    st.text_area("독서 관련 활동 내용 및 알게 된 점", key="book_desc", placeholder="책을 읽고 느낀 점이나 심화 탐구한 내용을 적어주세요.", height=68)

st.markdown("<br>", unsafe_allow_html=True)
submit = st.button("🚀 학생 맞춤형 개별 문장 생성 (화면 단건용)", type="primary", use_container_width=True)
st.divider()

# ===== 6. 단건 생성 로직 =====
if submit:
    activities_data = []
    for i in range(1, 3):
        if st.session_state[f'a{i}n'].strip() and st.session_state[f'a{i}d'].strip():
            activities_data.append(f"활동명 '{st.session_state[f'a{i}n'].strip()}'에 참여하여 핵심 수행한 내용: {st.session_state[f'a{i}d'].strip()}")
            
    book_title_val = st.session_state['book_title'].strip()
    book_desc_val = st.session_state['book_desc'].strip()
    book_data_str = f"이후 지적 확장을 위해 도서 '{book_title_val}'를 탐독하고 {book_desc_val}" if book_title_val and book_desc_val else ""
            
    num_activities = len(activities_data)
    activities_str = "\n\n".join(activities_data)

    if not api_key: st.error("API 키를 입력해 주세요!")
    elif num_activities == 0 and not book_data_str: st.warning("최소 1개 이상의 활동이나 독서 내용을 입력해 주세요!")
    else:
        box = st.empty()
        try:
            box.info("🔍 화면 데이터 기준 문장 구성 중...")
            verbs = df_verbs.to_string(index=False) if df_verbs is not None else ""
            target_byte, target_min, target_max = 1445, 1420, 1470
            
            prompt = f"""당신은 고등학교 베테랑 진학 교사입니다. 아래 데이터를 바탕으로 완벽한 학생부 교과세특 문장을 작성해 주세요.
            
            🚨 [서술 불변의 철칙 - 오차 없이 엄수] 🚨
            1. 메타 발언 금지: "결과입니다", "공백을 포함하여", "작성된 문장입니다" 등의 챗봇 같은 인사말과 설명문을 절대 쓰지 마세요. 무조건 세특 본문만 바로 시작하세요.
            2. 대괄호 기호 완전 금지: 결과물 문장 어디에도 대괄호([ ])나 콜론(:) 기호가 노출되어서는 안 됩니다. 명칭들은 오직 작은따옴표('') 기호로만 감싸세요.
            3. 1:1:1 완벽 서술 밸런스: 활동 내용들과 '도서명' 연계 묘사의 글자 수 비율을 1:1:1로 정확히 배분하세요.
            4. 독서 서사 완성형 매듭: 독서 심화 데이터가 있다면 문장의 최종반부는 반드시 책 내용을 기반으로 심화 탐구한 행동으로 끝나야 합니다.
            
            - 무조건 '~함', '~임' 명사형 종결어미 사용. 주어 생략. 한 단락 작성.
            - 분량: 공백 포함 480~500자 (1420~1470바이트) 절대 사수.

            [기본 데이터]
            - 진로 희망 학과: {aspiration}
            - 교과 핵심 키워드: {subject_keywords}
            
            [활동 데이터]
            {activities_str}
            
            [독서 연계 심화 데이터]
            {book_data_str}
            
            → 서론, 안내, 설명 문구 없이 오직 꽉 찬 본문 한 단락만 바로 출력하세요."""
            
            raw_response = generate_student_record(api_key, prompt, selected_model)
            result = clean(raw_response.strip(), subject)
            cb = byte_count(result)
            
            for attempt in range(2):
                if target_min <= cb <= target_max: break
                if cb > target_max:
                    adj_prompt = f"문장 분량이 초과되었습니다. 고유 명칭('')과 독서 서사를 유지하며 1450바이트로 압축하세요. 🚨안내 문구('압축된 결과입니다' 등) 절대 금지. 오직 본문만 출력.\n\n[문장]\n{result}"
                else:
                    adj_prompt = f"문장 분량이 부족합니다. 활동과 도서명의 서사 비중을 1:1로 맞추고 구체적 행동을 덧붙여 1450바이트로 확장하세요. 🚨안내 문구('확장된 내용입니다' 등) 절대 금지. 오직 본문만 출력.\n\n[원본 백업]\n{activities_str}\n{book_data_str}\n\n[문장]\n{result}"
                try:
                    adj_raw = generate_student_record(api_key, adj_prompt, selected_model)
                    result = clean(adj_raw.strip(), subject)
                    cb = byte_count(result)
                except: pass
            
            if cb > target_max:
                sentences = re.split(r'(?<=[.!?])\s+', result)
                trimmed = ""
                for s in sentences:
                    if byte_count(trimmed + (" " if trimmed else "") + s) <= target_max: trimmed += (" " if trimmed else "") + s
                    else: break
                if trimmed: result = trimmed.strip()
            
            box.success(f"✅ 학생 맞춤형 개별 문장 생성이 완료되었습니다!")
            st.subheader(f"📋 최종 생성된 학생부 기록")
            st.text_area("결과:", value=result, height=250, label_visibility="collapsed")
            
            c_a, c_b, c_c, c_d = st.columns(4)
            c_a.metric("📊 글자수", f"{len(result)}자")
            c_b.metric("💾 바이트", f"{byte_count(result)}byte")
            c_c.metric("🎯 목표구간", "1420~1470")
            
            if target_min <= byte_count(result) <= target_max: st.success("✨ 목표 범위 완벽 달성!")
            elif byte_count(result) <= 1500: st.info("📝 나이스 한도(1500바이트) 이내입니다. 사용 가능합니다.")
            else: st.error("⚠️ 한도 초과! 내용을 조금만 정돈해 주세요.")
                
        except Exception as e:
            box.error(f"오류가 발생했습니다: {e}")

# ===== 8. 푸터 고정 =====
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px; font-size: 15px;'>
    🏫 <b>학생부 입력 어시스트 시스템 v6.3</b><br>
    만든이: 신선여자고등학교 김명남<br>
</div>
""", unsafe_allow_html=True)
