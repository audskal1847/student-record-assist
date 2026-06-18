import streamlit as st
import google.generativeai as genai
import PyPDF2, pandas as pd, glob, os, re

st.set_page_config(page_title="개별화된 학생부 입력을 위한 어시스트", layout="wide")

# ===== 0. 교육과정 데이터베이스 (2015 vs 2022 분리) =====
CURRICULUM_DATA_2015 = {
    "국어군": {
        "국어": ["듣기·말하기의 본질", "읽기의 과정과 방법", "글쓰기의 원리와 과정", "문학의 수용과 생산", "국어의 규범과 변천"],
        "화법과 작문": ["화법과 작문의 본질/원리", "정보 전달", "설득", "자기 표현과 사회적 상호작용"],
        "독서": ["독서의 본질", "독서의 방법", "독서의 분야", "독서의 태도", "비판적/추론적 읽기"],
        "언어와 매체": ["음운과 단어", "문장과 담화", "국어사", "매체의 소통 방식", "매체 자료의 수용과 생산"],
        "문학": ["문학의 본질", "문학의 갈래와 역사", "문학과 삶", "문학의 인접 분야", "작품의 맥락"]
    },
    "수학군": {
        "수학": ["다항식", "방정식과 부등식", "도형의 방정식", "집합과 명제", "함수와 그래프"],
        "수학Ⅰ": ["지수함수와 로그함수", "삼각함수", "수열", "수학적 귀납법"],
        "수학Ⅱ": ["함수의 극한과 연속", "미분", "적분", "다항함수의 미적분"],
        "미적분": ["수열의 극한", "미분법", "적분법", "초월함수의 미적분"],
        "확률과 통계": ["경우의 수", "순열과 조합", "확률", "통계", "확률분포와 통계적 추정"],
        "기하": ["이차곡선", "평면벡터", "공간도형과 공간좌표"]
    },
    "영어군": {
        "영어": ["주제·요지 파악", "세부 정보 파악", "논리적 관계 파악", "맥락 추론", "의사소통 전략"],
        "영어Ⅰ": ["맥락/주제 파악", "세부 정보 파악", "함축 의미 추론", "영어 구문 이해"],
        "영어Ⅱ": ["심화된 주제 파악", "복잡한 논리적 관계 추론", "학술적 지문 이해"],
        "영어 독해와 작문": ["글의 구조와 논리", "다양한 목적의 글쓰기", "문화적 배경 이해"]
    },
    "사회군": {
        "통합사회": ["인간, 사회, 환경과 행복", "자연환경과 인간", "생활공간과 사회", "인권 보장과 헌법", "시장 경제와 금융", "사회 정의와 불평등", "문화와 다양성", "글로벌화와 평화"],
        "한국지리": ["국토 인식과 지리 정보", "지형 환경과 생태계", "기후 환경과 생활", "거주 공간의 변화", "생산과 소비의 공간", "인구 변화와 다문화 공간"],
        "세계지리": ["세계화와 지역 이해", "세계의 자연환경", "세계의 인문환경", "몬순 아시아와 오세아니아", "건조 아시아와 북부 아프리카", "유럽과 북부 아메리카"],
        "세계사": ["인류의 출현과 문명", "동아시아 지역의 역사", "서아시아/인도 지역의 역사", "유럽/아메리카 지역의 역사", "제국주의와 두 차례 세계 대전"],
        "사회·문화": ["사회·문화 현상의 탐구", "개인과 사회 구조", "문화와 일상생활", "사회 계층과 불평등", "현대의 사회 변동"],
        "생활과 윤리": ["현대의 윤리적 문제", "생명과 윤리", "사회와 윤리", "과학과 윤리", "문화와 윤리", "평화와 공존의 윤리"]
    },
    "과학군": {
        "통합과학": ["물질의 규칙성", "시스템과 상호작용", "변화와 다양성", "환경과 에너지"],
        "물리학Ⅰ": ["힘과 운동", "시공간과 새로운 역학", "열과 에너지", "전기와 자기", "파동과 정보 통신", "빛과 물질의 이중성"],
        "화학Ⅰ": ["화학의 첫걸음", "원자의 세계", "화학 결합과 분자의 세계", "역동적인 화학 반응", "산화 환원과 중화 반응"],
        "생명과학Ⅰ": ["생명 과학의 이해", "사람의 물질대사", "항상성과 몸의 조절", "방어 작용", "유전", "생태계와 상호 작용"],
        "지구과학Ⅰ": ["고체 지구", "판구조론과 지각 변동", "대기와 해양", "대기와 해양의 상호 작용", "우주", "별과 외계 행성계"]
    },
    "기타(생활/교양/예체능)": {
        "기술·가정": ["인간 발달과 가족", "가정생활과 안전", "자원 관리와 자립", "기술 시스템", "기술 활용"],
        "정보": ["정보 문화", "자료와 정보", "문제 해결과 프로그래밍", "컴퓨팅 시스템"],
        "보건": ["건강의 이해", "질병 예방과 관리", "약물 오남용 예방", "성과 건강", "정신 건강"]
    }
}

CURRICULUM_DATA_2022 = {
    "국어군": {
        "공통국어1/2": ["듣기·말하기의 본질", "읽기의 과정과 방법", "글쓰기의 원리와 과정", "문학의 수용과 생산", "국어의 규범과 변천", "매체의 이해"],
        "화법과 언어": ["화법의 본질과 원리", "국어의 구조와 역사", "매체와 소통"],
        "독서와 작문": ["독서의 목적과 방법", "작문의 과정과 원리", "다양한 주제의 글 읽기와 쓰기"],
        "문학": ["문학의 수용과 생산", "한국 문학의 특질과 흐름", "문학과 매체"],
        "매체 의사소통": ["매체의 특성", "매체 자료의 수용과 생산", "매체 문화와 윤리"]
    },
    "수학군": {
        "공통수학1/2": ["다항식", "방정식과 부등식", "도형의 방정식", "집합과 명제", "함수와 그래프", "경우의 수"],
        "대수": ["지수함수와 로그함수", "삼각함수", "수열"],
        "미적분Ⅰ": ["함수의 극한과 연속", "미분", "적분"],
        "미적분Ⅱ": ["수열의 극한", "미분법", "적분법"],
        "확률과 통계": ["경우의 수", "확률", "통계"],
        "기하": ["이차곡선", "공간도형과 공간좌표", "벡터"]
    },
    "영어군": {
        "공통영어1/2": ["일상적 의사소통", "주제·요지 파악", "세부 정보 파악", "문화적 배경 이해"],
        "영어Ⅰ": ["맥락 추론", "논리적 관계 파악", "다양한 주제의 글 이해"],
        "영어Ⅱ": ["심화된 주제 파악", "복잡한 논리적 관계 추론", "학술적 지문 이해"],
        "영어 독해와 작문": ["글의 구조와 논리", "목적에 맞는 글쓰기", "매체 융합적 표현"]
    },
    "사회군": {
        "통합사회1/2": ["인간, 사회, 환경과 행복", "자연환경과 인간", "생활공간과 사회", "인권 보장과 헌법", "시장 경제와 금융", "사회 정의와 불평등", "문화와 다양성", "글로벌화와 평화"],
        "세계시민과 지리": ["세계화와 세계시민", "다양한 문화와 공간", "글로벌 환경 문제와 지속가능성"],
        "세계사": ["인류의 출현과 문명", "지역 세계의 형성과 교류", "근대 세계의 전개", "현대 세계의 변화"],
        "사회와 문화": ["사회·문화 현상의 탐구", "개인과 사회 구조", "문화와 일상생활", "사회 불평등과 변동"],
        "정치": ["민주주의와 헌법", "국가 기관과 정치 과정", "국제 정치"],
        "경제": ["경제생활과 경제 문제", "시장과 경제 활동", "국가와 세계 경제"]
    },
    "과학군": {
        "통합과학1/2": ["물질과 규칙성", "시스템과 상호작용", "변화와 다양성", "환경과 에너지"],
        "과학탐구실험1/2": ["역사 속의 과학 탐구", "생활 속의 과학 탐구", "첨단 과학 탐구"],
        "물리학": ["힘과 운동", "전기와 자기", "파동과 정보 통신"],
        "화학": ["물질의 구성", "화학 결합과 분자의 세계", "화학 반응의 세계"],
        "생명과학": ["생명 과학의 이해", "생명 시스템과 조절", "생명 연속성과 다양성"],
        "지구과학": ["고체 지구", "대기와 해양", "우주"]
    },
    "기타(생활/교양/예체능)": {
        "기술·가정": ["인간 발달과 가족", "가정생활과 안전", "기술 시스템", "기술 활용"],
        "정보": ["컴퓨팅 시스템", "자료와 정보", "알고리즘과 프로그래밍", "인공지능과 데이터"],
        "보건": ["건강의 이해", "질병 예방", "약물 예방", "정신 건강"],
        "인공지능 기초": ["인공지능의 이해", "데이터와 기계학습", "인공지능의 사회적 영향"]
    }
}

COMPETENCIES_2015 = ["AI에게 알아서 맡기기", "자기관리 역량", "지식정보처리 역량", "창의적 사고 역량", "심미적 감성 역량", "의사소통 역량", "공동체 역량"]
COMPETENCIES_2022 = ["AI에게 알아서 맡기기", "자기관리 역량", "지식정보처리 역량", "창의적 사고 역량", "심미적 감성 역량", "협력적 소통 역량", "공동체 역량"]

# ===== 1. 데이터 로딩 =====
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

# ===== 2. AI 모델 자동 탐색 =====
def find_model(api_key):
    genai.configure(api_key=api_key)
    models = [m.name.replace("models/", "") for m in genai.list_models()
              if 'generateContent' in m.supported_generation_methods]
    for keys in [("1.5","flash","8b"), ("1.5","flash"), ("2.5","flash"),
                 ("2.0","flash"), ("flash",), ("pro",)]:
        for m in models:
            if any(s in m for s in ["vision","embedding","exp","thinking","tts","image"]): continue
            if all(k in m for k in keys): return m
    return models[0] if models else None

# ===== 3. 구체적 숫자 자동 치환 =====
def remove_numbers(text):
    text = re.sub(r'약\s*\d+\s*여?\s*명의?', '여러 명의', text)
    text = re.sub(r'약\s*\d+\s*여?\s*곳을?', '여러 곳을', text)
    text = re.sub(r'약\s*\d+\s*여?\s*개의?', '여러', text)
    text = re.sub(r'\d+\s*여\s*명', '여러 명', text)
    text = re.sub(r'\d+\s*여\s*곳', '여러 곳', text)
    text = re.sub(r'\d+\s*여\s*개', '여러 개', text)
    text = re.sub(r'\d+\s*여\s*편', '여러 편', text)
    text = re.sub(r'\d+\s*여\s*권', '여러 권', text)
    text = re.sub(r'\d+\s*여\s*건', '여러 건', text)
    text = re.sub(r'\d+\s*명의', '여러 명의', text)
    text = re.sub(r'\d+\s*명과', '여러 명과', text)
    text = re.sub(r'\d+\s*명을', '여러 명을', text)
    text = re.sub(r'\d+\s*명에게', '여러 명에게', text)
    text = re.sub(r'\d+\s*명', '여러 명', text)
    text = re.sub(r'\d+\s*곳을', '여러 곳을', text)
    text = re.sub(r'\d+\s*곳의', '여러 곳의', text)
    text = re.sub(r'\d+\s*곳에', '여러 곳에', text)
    text = re.sub(r'\d+\s*곳', '여러 곳', text)
    text = re.sub(r'\d+\s*군데', '여러 군데', text)
    text = re.sub(r'\d+\s*점포', '여러 점포', text)
    text = re.sub(r'\d+\s*개\s*점포', '여러 점포', text)
    text = re.sub(r'\d+\s*장의', '다수의', text)
    text = re.sub(r'\d+\s*장을', '다수의 사진을', text)
    text = re.sub(r'\d+\s*장', '다수', text)
    text = re.sub(r'\d+\s*편의', '여러 편의', text)
    text = re.sub(r'\d+\s*편을', '여러 편을', text)
    text = re.sub(r'\d+\s*편', '여러 편', text)
    text = re.sub(r'\d+\s*권의', '여러 권의', text)
    text = re.sub(r'\d+\s*권을', '여러 권을', text)
    text = re.sub(r'\d+\s*권', '여러 권', text)
    text = re.sub(r'\d+\s*건의', '여러 건의', text)
    text = re.sub(r'\d+\s*건을', '여러 건을', text)
    text = re.sub(r'\d+\s*건', '여러 건', text)
    text = re.sub(r'\d+\s*종의', '여러 종류의', text)
    text = re.sub(r'\d+\s*종', '여러 종류', text)
    text = re.sub(r'\d+\s*개의', '여러', text)
    text = re.sub(r'\d+\s*개를', '여러 개를', text)
    text = re.sub(r'\d+\s*개', '여러 개', text)
    text = re.sub(r'\d+\s*가지의?', '여러 가지', text)
    text = re.sub(r'\d+\s*회의?', '수차례', text)
    text = re.sub(r'\d+\s*차례', '수차례', text)
    text = re.sub(r'\d+\s*번의?', '여러 번', text)
    text = re.sub(r'\d+\s*개의?\s*게시물', '여러 게시물', text)
    text = re.sub(r'\d+\s*건의?\s*게시물', '여러 게시물', text)
    text = re.sub(r'약\s+여러', '여러', text)
    text = re.sub(r'약\s+다수', '다수', text)
    text = re.sub(r'약\s+수차례', '수차례', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)
    return text

# ===== 4. 결과 정화 =====
def clean(text, subject=""):
    for pat in [r'\*\*(.*?)\*\*', r'\*(.*?)\*', r'__(.*?)__', r'`(.*?)`']:
        text = re.sub(pat, r'\1', text)
    text = re.sub(r'^#+\s*|^[\-\*\+]\s+', '', text, flags=re.MULTILINE)
    if subject:
        for pat in [f"{subject} 수업을 통해", f"{subject} 시간에", f"{subject}에서", f"{subject} 교과", subject]:
            text = re.sub(pat + r'\s*,?\s*', '', text)
    for pat in [r'본\s*학생[은이]\s*', r'해당\s*학생[은이]\s*', r'이\s*학생[은이]\s*', r'학생[은이을를]\s*', r'학생에게\s*']:
        text = re.sub(pat, '', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'^[은는이가을를에]\s+', '', text.strip())
    text = remove_numbers(text)
    return text.strip()

def byte_count(text):
    return len(text.encode('utf-8'))

# ===== 5. 사이드바 =====
with st.sidebar:
    st.header("🔑 기본 설정")
    api_key = st.text_input("Google AI API 키", type="password")
    st.markdown("[🔗 무료 API 키 발급](https://aistudio.google.com/app/apikey)")
    st.divider()
    
    df_guide, df_verbs = load_excel()
    if df_guide is not None:
        st.success(f"✅ 엑셀 사전 로드 (동사 {len(df_verbs)}개 활용)")
    else:
        st.error("❌ data.xlsx 없음")
        
    pdf_files = glob.glob("*.pdf")
    if pdf_files:
        st.success(f"✅ PDF 가이드북 {len(pdf_files)}개 로드")
        
    st.divider()
    st.info("🎯 목표: 1420~1470 바이트")
    st.caption("🔢 구체적 숫자 자동 제거 적용 중")
    
    st.markdown("---")
    st.markdown("### 📥 자료실 및 관련 링크")
    st.link_button("📖 2026 교과 선택 가이드북", "https://ebook.dsummer.co.kr/books/yxly/#p=1", use_container_width=True)
    st.link_button("📄 2025 교과 선택 가이드북", "https://books.dsummer.co.kr/books/lfyk/#p=1", use_container_width=True)

# ===== 6. 메인 화면 =====
st.title("📝 학생부 입력 어시스트")
st.caption("선택한 교육과정과 교과 핵심 키워드를 기반으로 유기적으로 연결된 개별화 학생부 기록이 생성됩니다.")

# 🔥 교육과정 선택 UI (크고 굵게 강조)
st.markdown("### 📘 **적용 교육과정 선택**")
curriculum_version = st.radio("적용 교육과정 선택", ["2015 개정 교육과정", "2022 개정 교육과정"], horizontal=True, label_visibility="collapsed")

# 선택된 교육과정에 따른 변수 할당
if curriculum_version == "2015 개정 교육과정":
    current_curriculum_data = CURRICULUM_DATA_2015
    current_competencies = COMPETENCIES_2015
else:
    current_curriculum_data = CURRICULUM_DATA_2022
    current_competencies = COMPETENCIES_2022

st.markdown("---")

# [섹션 1] 학생 기본 정보 (가로 3단)
st.markdown("#### 1. 학생 기본 정보")
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    aspiration = st.text_input("🎓 진학 희망 학과/계열 ⭐", placeholder="예: 도시공학과 / 사회학과")
with col_b2:
    focus = st.selectbox(f"🎯 6대 핵심 역량 ({curriculum_version})", current_competencies)
with col_b3:
    extra = st.text_area("🔍 학생별 개별화 강조 포인트", placeholder="예: 탐구력과 자기주도성 강조, 창의력과 문제해결력 강조", height=68)

st.markdown("---")

# [섹션 2] 교과 관련 정보 (가로 3단)
st.markdown("#### 2. 교과 관련 정보")
col_s1, col_s2, col_s3 = st.columns([1, 1, 2])

with col_s1:
    subject_group = st.selectbox("📚 교과군 선택", ["직접 입력", "국어군", "수학군", "영어군", "사회군", "과학군", "기타(생활/교양/예체능)"])

with col_s2:
    if subject_group != "직접 입력":
        subject_dropdown = st.selectbox(f"📖 과목명", ["직접 입력"] + list(current_curriculum_data[subject_group].keys()))
        if subject_dropdown == "직접 입력":
            subject = st.text_input("과목명 직접 입력", placeholder="과목명을 입력하세요", label_visibility="collapsed")
        else:
            subject = subject_dropdown
    else:
        subject = st.text_input("📖 과목/활동 영역 (참고용)", placeholder="예: 창의적체험활동- 자율활동")

with col_s3:
    selected_concepts = []
    if subject_group != "직접 입력" and subject in current_curriculum_data[subject_group]:
        concept_options = current_curriculum_data[subject_group][subject]
        selected_concepts = st.multiselect(f"🧠 교과 핵심 아이디어 및 내용 요소", concept_options, placeholder="안내서 기준 핵심 개념을 선택하세요.")
    
    manual_keywords = st.text_input("핵심 키워드 직접 입력", placeholder="예: 세계시민역량, 표층순환, 빛과 물질의 이중성 등 (직접 입력 시 작성)")
    
    subject_keywords = ", ".join(selected_concepts)
    if manual_keywords.strip():
        subject_keywords += (" / " if subject_keywords else "") + manual_keywords.strip()

st.markdown("---")

# [섹션 3] 구체적인 활동 입력 (가로 2단, 최대 4개)
st.markdown("#### 3. 구체적인 활동 및 상세 내용 (최대 4개)")
st.caption("진행한 활동의 개수만큼 입력하세요. 입력한 활동의 개수와 내용에 맞춰 목표 바이트에 근접한 문장을 생성합니다.")

col_act1, col_act2 = st.columns(2)

with col_act1:
    st.markdown("**🔹 활동 1 (필수)**")
    act1_name = st.text_input("활동명 1", placeholder="예: 커뮤니티 매핑 지도 만들기", label_visibility="collapsed")
    act1_desc = st.text_area("활동 1 상세 내용", placeholder="위 활동에 대한 구체적인 역할, 성취 등을 입력하세요.", height=100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("**🔹 활동 3 (선택)**")
    act3_name = st.text_input("활동명 3", placeholder="예: 기후 변화 대응 캠페인", label_visibility="collapsed")
    act3_desc = st.text_area("활동 3 상세 내용", placeholder="활동 상세 내용 입력", height=100)

with col_act2:
    st.markdown("**🔹 활동 2 (선택)**")
    act2_name = st.text_input("활동명 2", placeholder="예: 지속가능한 도시 개발 보고서 작성", label_visibility="collapsed")
    act2_desc = st.text_area("활동 2 상세 내용", placeholder="활동 상세 내용 입력", height=100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("**🔹 활동 4 (선택)**")
    act4_name = st.text_input("활동명 4", placeholder="예: 전공지식 확장을 위한 주제탐구보고서 작성", label_visibility="collapsed")
    act4_desc = st.text_area("활동 4 상세 내용", placeholder="활동 상세 내용 입력", height=100)

st.markdown("<br>", unsafe_allow_html=True)

submit = st.button("🚀 학생 맞춤형 개별 문장 생성", type="primary", use_container_width=True)
st.divider()

# ===== 7. 생성 로직 =====
if submit:
    activities_data = []
    if act1_name.strip() and act1_desc.strip(): activities_data.append(f"[활동명: {act1_name.strip()}]\n- 상세 내용: {act1_desc.strip()}")
    if act2_name.strip() and act2_desc.strip(): activities_data.append(f"[활동명: {act2_name.strip()}]\n- 상세 내용: {act2_desc.strip()}")
    if act3_name.strip() and act3_desc.strip(): activities_data.append(f"[활동명: {act3_name.strip()}]\n- 상세 내용: {act3_desc.strip()}")
    if act4_name.strip() and act4_desc.strip(): activities_data.append(f"[활동명: {act4_name.strip()}]\n- 상세 내용: {act4_desc.strip()}")
        
    num_activities = len(activities_data)
    activities_str = "\n\n".join(activities_data)

    if not api_key: st.error("API 키를 입력해 주세요!")
    elif num_activities == 0: st.warning("최소 1개 이상의 구체적인 활동명과 상세 내용을 입력해 주세요! (활동 1 필수)")
    else:
        box = st.empty()
        try:
            box.info("🔍 최적의 AI 모델 탐색 중...")
            model_name = find_model(api_key)
            if not model_name: raise Exception("사용 가능한 모델 없음")
            model = genai.GenerativeModel(model_name)
            
            verbs = df_verbs.to_string(index=False) if df_verbs is not None else ""
            pdf_text = load_pdfs(pdf_files)[:3000] if pdf_files else ""
            
            target_byte, target_min, target_max = 1445, 1420, 1470
            target_chars = 481
            
            aspiration_part = f"""
            🎓 진학 희망: '{aspiration}'
            - 이 학과·계열 관점에서 활동을 재해석하여 강조
            - 결말부를 '{aspiration}' 관련 학문적 호기심·후속 탐구 의지로 자연스럽게 마무리
            - ❌ "○○학과 진학 희망" 직접 선언 금지!
            """ if aspiration.strip() else ""
            
            competency_part = f"""
            🌟 교육과정 핵심 역량: '{focus}'
            - 이 역량을 기반으로 학생의 성장을 평가하는 문장을 구성하세요.
            """ if focus != "AI에게 알아서 맡기기" else ""

            keyword_part = f"""
            🧠 교과 핵심 키워드: {subject_keywords}
            - 이 핵심 키워드를 단순 나열하지 말고, 뒤에 나오는 구체적인 '활동(활동명)'들의 원동력이 되거나 그 활동들을 관통하는 주제가 되도록 스토리를 묶어주세요.
            """ if subject_keywords.strip() else ""
            
            prompt = f"""당신은 20년 경력의 베테랑 학생부 작성 교사입니다. 아래 학생 데이터를 바탕으로 가장 이상적인 학생부 문장을 작성해 주세요.

            🚨 [학생부 서술 3단계 완벽 구조 - 반드시 지킬 것!!!] 🚨
            대학 입학사정관이 가장 선호하는 형태인 "교과 ➡️ 활동 ➡️ 진로"의 유기적 연계 구조로 작성하세요.

            1. 도입부 (교과 기반 역량 평가):
               - 첫 문장은 반드시 제공된 [교과 핵심 키워드] 및 [핵심 역량]을 활용하여, "학생이 교과 핵심 개념인 ~에 대한 깊은 이해를 바탕으로 ~한 역량이 우수함(충분함)"이라는 식의 명확한 '역량 평가' 문장으로 시작하세요. (사전적 정의 형태 절대 금지)
            
            2. 전개부 (역량과 활동의 유기적 연계):
               - 앞서 언급한 교과 역량과 지적 호기심이 뒤따르는 구체적인 [활동명]으로 어떻게 이어졌는지 자연스럽게 연결하세요. 
               - 예: "이러한 역량을 토대로 '[활동명]'에 참여하여..." 혹은 "이 개념에 대한 호기심을 바탕으로 '[활동명]'을 주도하며..."
               - 앞 문장과 뒤 문장이 뚝뚝 끊어지지 않고 반드시 하나의 스토리(인과관계)로 이어져야 합니다.

            3. 결속 및 마무리 (진로 연계의 의미 부여):
               - 마지막 문장은 학생의 이러한 구체적이고 개별적인 활동 결과물이 지원 희망하는 [진학 희망 학과/계열]의 특성에 완벽히 부합하며, 그렇기에 매우 유의미한 학업적 성취를 이루었다는 식으로 매듭지으세요. 
               - 단, "○○학과 진학을 희망함" 식의 일차원적 직접 선언은 절대 금지합니다.

            🚨🚨🚨 [어투 및 종결어미 절대 규칙] 🚨🚨🚨
            모든 문장의 끝은 무조건 '~함', '~임', '~됨'으로 끝나는 개조식(명사형) 종결어미로 작성하세요!
            ❌ 금지: '~습니다', '~해요', '~다' 등 서술형 어미 절대 금지.

            🚨 [기타 절대 금지 규칙]
            1. 구체적 숫자(예: "주민 7명", "3차례 회의") 절대 금지! ✅ 대신 "여러 명의", "다수의" 등 정성적 표현 사용.
            2. 마크다운 기호(별표, #, - 등) 사용 금지.
            3. '학생은/학생이/해당 학생에게서' 등 주어 표현 금지.
            4. 활동명은 반드시 작은따옴표('')로 묶어서 원래 이름 그대로 출력할 것.

            🚨 [필수 분량] 
            - 한글 정확히 {target_chars}자(±8자) / 1420~1470바이트 이내.
            - 반드시 하나의 단락으로 작성(엔터/줄바꿈 금지).

            [학생 기본 데이터]
            - 적용 교육과정: {curriculum_version}
            {competency_part}
            {aspiration_part}
            {keyword_part}

            [활동 내역 및 세부 내용] (총 {num_activities}개)
            {activities_str}

            [참고: 권장 동사]
            {verbs}

            [참고: PDF 가이드북 내용 일부]
            {pdf_text}
            
            [추가 지시]
            {extra if extra else "없음"}

            → 줄바꿈 없는 한 단락으로 본문만 출력! 3단계 인과 구조 엄수!"""
            
            box.warning(f"🤖 최적의 문장 생성 중...")
            response = model.generate_content(prompt)
            result = clean(response.text.strip(), subject)
            cb = byte_count(result)
            
            if not (target_min <= cb <= target_max):
                if cb > target_max:
                    box.warning(f"📏 분량 압축 중... ({cb}바이트 → 목표 {target_byte})")
                    adj_prompt = f"""아래 원본 문장을 한글 {target_chars}자 분량으로 압축하세요. 
                    🚨 [압축 시 절대 규칙]
                    1. 모든 문장 끝은 무조건 '~함', '~임' 명사형 종결어미 유지.
                    2. 첫 문장(교과 핵심 개념 바탕 역량 우수함) ➡️ 중간(그 역량을 바탕으로 '[활동명]' 참여) ➡️ 끝 문장(희망 전공 특성에 부합하는 유의미한 결과)의 **3단계 인과 구조와 스토리텔링을 절대 훼손하지 말고 그대로 유지할 것.**
                    3. 작은따옴표('')로 묶인 고유 활동명은 원문 그대로 반드시 보존할 것.
                    4. 문장이 단답형으로 툭툭 끊기지 않게 연결어미 활용. 구체적 숫자 금지.
                    [원본]\n{result}\n→ 본문만 출력!"""
                elif cb < target_min:
                    box.warning(f"📏 분량 확장 중... ({cb}바이트 → 목표 {target_byte})")
                    adj_prompt = f"""아래 원본 문장을 한글 {target_chars}자 분량으로 확장하세요. 
                    🚨 [확장 시 절대 규칙]
                    1. 모든 문장 끝은 무조건 '~함', '~임' 명사형 종결어미 유지.
                    2. 첫 문장(교과 핵심 개념 바탕 역량 우수함) ➡️ 중간(그 역량을 바탕으로 '[활동명]' 참여) ➡️ 끝 문장(희망 전공 특성에 부합하는 유의미한 결과)의 **3단계 인과 구조와 스토리텔링을 절대 훼손하지 말고 그대로 유지할 것.**
                    3. 작은따옴표('')로 묶인 고유 활동명은 원문 그대로 반드시 보존할 것.
                    4. 문장이 단답형으로 툭툭 끊기지 않게 연결어미 활용. 구체적 숫자 금지.
                    [원본]\n{result}\n→ 본문만 출력!"""
                
                try:
                    new_result = clean(model.generate_content(adj_prompt).text.strip(), subject)
                    new_cb = byte_count(new_result)
                    if abs(new_cb - target_byte) < abs(cb - target_byte):
                        result, cb = new_result, new_cb
                except: pass
            
            if cb > target_max:
                sentences = re.split(r'(?<=[.!?])\s+', result)
                trimmed = ""
                for s in sentences:
                    test = trimmed + (" " if trimmed else "") + s
                    if byte_count(test) <= target_max:
                        trimmed = test
                    else: break
                if trimmed: result, cb = trimmed.strip(), byte_count(trimmed)
            
            box.success(f"✅ 학생 맞춤형 개별 문장 생성이 완료되었습니다!")
            st.subheader(f"📋 최종 생성된 학생부 기록{' - ' + aspiration + ' 맞춤' if aspiration else ''}")
            st.text_area("결과:", value=result, height=250, label_visibility="collapsed")
            
            c_a, c_b, c_c, c_d = st.columns(4)
            c_a.metric("📊 글자수", f"{len(result)}자")
            c_b.metric("💾 바이트", f"{cb}byte")
            c_c.metric("🎯 목표구간", "1420~1470")
            
            if target_min <= cb <= target_max:
                c_d.metric("✅ 상태", "완벽")
                st.success("✨ 목표 범위(1420~1470) 완벽 달성! 나이스(NEIS)에 바로 입력할 수 있습니다.")
            elif cb <= 1500:
                c_d.metric("📝 상태", "사용가능")
                st.info(f"📝 나이스 한도(1500바이트) 이내입니다. 그대로 사용하셔도 좋습니다.")
            elif cb < target_min:
                c_d.metric("⚠️ 상태", f"부족 (-{target_min - cb})")
                st.warning(f"⚠️ 목표보다 {target_min - cb}바이트 부족합니다. 추가 내용을 넣어 다시 생성해 보세요.")
            else:
                c_d.metric("⚠️ 상태", "초과")
                st.error("⚠️ 한도 초과! 활동 내용을 조금 줄여서 다시 생성해 주세요.")
            
            remaining_numbers = re.findall(r'\d+\s*(?:명|곳|장|편|권|회|개|건|종|차례|번|점포|군데|가지|시간)', result)
            if remaining_numbers:
                st.warning(f"⚠️ 시스템이 수치를 정성적으로 치환했으나, 일부 숫자 표현이 남아있을 수 있습니다: {', '.join(remaining_numbers[:5])} - 확인 후 직접 수정해 주세요.")
            else:
                st.info("✅ '교과 역량 ➡️ 심화 탐구(활동) ➡️ 진로 의미'가 완벽하게 연계된 3단계 구조로 작성되었습니다!")
                
        except Exception as e:
            box.error(f"오류가 발생했습니다: {e}")
            st.info("💡 API 키 재입력 또는 잠시 후 다시 시도해 주세요.")

# ===== 8. 푸터 =====
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px; font-size: 15px;'>
    🏫 <b>학생부 입력 어시스트 시스템 v4.5</b><br>
    만든이: 신선여자고등학교 김명남<br>
</div>
""", unsafe_allow_html=True)
