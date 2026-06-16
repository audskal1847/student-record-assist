import streamlit as st
import google.generativeai as genai
import PyPDF2, pandas as pd, glob, os, re

st.set_page_config(page_title="개별화된 학생부 입력을 위한 어시스트", layout="wide")

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
        st.success(f"✅ 엑셀 사전 로드 (표현 {len(df_guide)}개 / 동사 {len(df_verbs)}개)")
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
    st.link_button("📖 교과 선택 가이드북(2026)", "https://ebook.dsummer.co.kr/books/yxly/#p=1", use_container_width=True)
    st.link_button("📄 선택과목 안내서 보러가기", "https://ebook.dsummer.co.kr/books/exkt/#p=1", use_container_width=True)

# ===== 6. 메인 화면 =====
st.title("📝 학생부 입력 어시스트")
st.caption("학생을 설명할 수 있는 핵심 키워드와 희망 진로를 입력하면, 학생별 맞춤형 학생부 기록이 생성됩니다.")

# [섹션 1] 기본 정보 (가로 3단)
st.markdown("#### 1. 학생 기본 정보")
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    subject = st.text_input("📖 과목/활동 영역 (참고용)", placeholder="예: 세계시민과 지리, 물리학1")
with col_b2:
    aspiration = st.text_input("🎓 진학 희망 학과/계열 ⭐", placeholder="예: 도시공학과 / 사회학과")
with col_b3:
    if df_guide is not None:
        col0 = df_guide.columns[0]
        options = ["AI에게 알아서 맡기기"] + df_guide[col0].dropna().unique().tolist()
        focus = st.selectbox("🎯 강조 역량", options)
    else:
        focus = "AI에게 알아서 맡기기"

st.markdown("---")

# [섹션 2] 구체적인 활동 입력 (가로 2단, 최대 4개)
st.markdown("#### 2. 구체적인 활동 및 상세 내용 (최대 4개)")
st.caption("진행한 활동의 개수만큼 입력하세요. 2단 구성으로 스크롤을 최소화했습니다.")

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
    
    st.markdown("**🔹 활동 4 (전공지식 확장을 위한 주제탐구보고서 작성)**")
    act4_name = st.text_input("활동명 4", placeholder="", label_visibility="collapsed")
    act4_desc = st.text_area("활동 4 상세 내용", placeholder="활동 상세 내용 입력", height=100)

st.markdown("---")

# [섹션 3] 추가 반영사항 및 교과 키워드 (가로 2단)
st.markdown("#### 3. 추가 반영사항 및 핵심 키워드")
col_add1, col_add2 = st.columns(2)

with col_add1:
    st.markdown("**🧠 교과 핵심 아이디어 및 내용 요소**")
    st.caption("해당 교과에서 강조하고 싶은 키워드를 입력하세요.")
    subject_keywords = st.text_area("핵심 키워드 입력", placeholder="예: 세계시민역량, 표층순환, DNA와 유전자, 빛과 물질의 이중성, 공유결합의 극성 ", height=100, label_visibility="collapsed")

with col_add2:
    st.markdown("**🔍 개별화를 위한 추가 강조 포인트**")
    st.caption("AI가 특별히 신경 써야 할 학생만의 강점을 적어주세요.")
    extra = st.text_area("추가 포인트 입력", placeholder="예: 탐구력과 자기주도성 강조, 창의력과 문제해결력 강조", height=100, label_visibility="collapsed")

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
    elif df_guide is None: st.error("data.xlsx 파일이 필요합니다!")
    else:
        box = st.empty()
        try:
            box.info("🔍 최적의 AI 모델 탐색 중...")
            model_name = find_model(api_key)
            if not model_name: raise Exception("사용 가능한 모델 없음")
            model = genai.GenerativeModel(model_name)
            
            col0 = df_guide.columns[0]
            guide = df_guide[df_guide[col0] == focus].to_string(index=False) if focus != "AI에게 알아서 맡기기" else df_guide.to_string(index=False)
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
            
            keyword_part = f"""
            🧠 교과 핵심 키워드: {subject_keywords}
            """ if subject_keywords.strip() else ""
            
            # 🔥 핵심 변경: 첫 문장 역량 평가형 서술 지시 강력 추가
            prompt = f"""당신은 20년 경력의 베테랑 학생부 작성 교사입니다. 학생 활동 내역을 바탕으로 풍성한 학생부 문장을 작성해 주세요.

            🚨🚨🚨 [어투 및 종결어미 절대 규칙] 🚨🚨🚨
            모든 문장의 끝은 무조건 '~함', '~임', '~됨'으로 끝나는 개조식(명사형) 종결어미로 작성하세요!
            ❌ 금지: '~습니다', '~해요', '~다' 등 서술형 어미 절대 금지.

            🚨 [작성 및 배치 절대 규칙 - 매우 중요!!!] 🚨
            1. 첫 문장 고정: [교과 핵심 키워드]가 제공된 경우, 반드시 전체 글의 첫 번째 문장에 작성하세요. 
               ❌ 단순한 개념 설명이나 사전적 정의로 끝내지 마세요! (예: "~은 중요한 역량임" 절대 금지)
               ✅ 반드시 "이러한 교과 핵심 개념(또는 역량)을 바탕으로 ~한 능력을 탁월하게 보여줌(발휘함)"과 같이 **해당 학생이 실제로 그 역량을 갖추고 있음을 평가하는 문장**으로 서술하세요.
            2. 활동명 원문 보존: 제공된 [활동 내역]의 '활동명'은 절대 임의로 바꾸거나 생략하지 마세요! 생성되는 문장 내에 작은따옴표('')로 묶어 원문 그대로 출력하고, 그 뒤에 활동 상세 내용을 유기적으로 풀어쓰세요. (예: '{act1_name}'에 참여하여 ~을 탐구함)
            3. 문장 길이와 호흡: 문장이 너무 짧은 단답형으로 툭툭 끊어지지 않도록 주의하세요. 적절한 연결 어미(~하며, ~고, ~을 통해 등)를 사용하여 호흡이 길고 매끄러운 학술적인 문장으로 구성하세요.

            🚨 [필수 분량] 한글 정확히 {target_chars}자(±8자) / 1420~1470바이트 / 한 단락(줄바꿈 절대 금지)!

            🚨 [구체적 숫자 절대 금지!]
            검증되지 않은 수치(예: "주민 7명", "사진 10장", "3차례 회의") 절대 금지! 
            ✅ 대신 "여러 명의", "다수의", "수차례" 등 정성적 표현 사용.

            🚨 [기타 절대 금지]
            1. 과목명('{subject}' 등) 출력 금지
            2. 마크다운(별표, #, - 등) 사용 금지  
            3. '학생은/학생이/해당 학생에게서' 등 주어 표현 금지 (한국어 생기부 작성 원칙에 따라 주어는 생략할 것)

            {aspiration_part}
            {keyword_part}

            [활동 내역 및 세부 내용] (총 {num_activities}개)
            {activities_str}

            [작성 규칙]
            - {num_activities}개의 활동을 유기적으로 연결하여 균형 있게 배분할 것. 
            - 엑셀 핵심 표현 2~3개, 권장 동사 3~4개 자연스럽게 활용.

            [엑셀 핵심 표현]
            {guide}

            [권장 동사]
            {verbs}

            [PDF 가이드북 참고]
            {pdf_text}

            [추가 지시]
            {extra if extra else "없음"}

            → 줄바꿈 없는 한 단락으로 본문만 출력! 문장 호흡 길게! 활동명 그대로 출력! 첫 문장은 핵심 키워드를 활용한 역량 평가!"""
            
            box.warning(f"🤖 '{model_name}'로 최적의 문장 생성 중...")
            response = model.generate_content(prompt)
            result = clean(response.text.strip(), subject)
            cb = byte_count(result)
            
            # 🔥 핵심 변경: 분량 조절(압축/팽창) 시 첫 문장의 '역량 평가형태 유지' 규칙 추가
            if not (target_min <= cb <= target_max):
                if cb > target_max:
                    box.warning(f"📏 분량 압축 중... ({cb}바이트 → 목표 {target_byte})")
                    adj_prompt = f"""아래 원본 문장을 한글 {target_chars}자 분량으로 압축하세요. 
                    🚨 [압축 시 절대 규칙]
                    1. 모든 문장 끝은 무조건 '~함', '~임' 명사형 종결어미 유지.
                    2. 첫 번째 문장의 내용(교과 핵심 키워드)은 단순 개념 정의가 아닌 학생의 역량 평가 형태로 전체 글 맨 앞에 그대로 유지할 것.
                    3. 작은따옴표('')로 묶인 고유 활동명은 원문 그대로 반드시 보존할 것.
                    4. 문장이 단답형으로 툭툭 끊기지 않게 연결어미 활용하여 매끄럽게 이을 것. 구체적 숫자 금지.
                    [원본]\n{result}\n→ 본문만 출력!"""
                elif cb < target_min:
                    box.warning(f"📏 분량 확장 중... ({cb}바이트 → 목표 {target_byte})")
                    adj_prompt = f"""아래 원본 문장을 한글 {target_chars}자 분량으로 확장하세요. 
                    🚨 [확장 시 절대 규칙]
                    1. 모든 문장 끝은 무조건 '~함', '~임' 명사형 종결어미 유지.
                    2. 첫 번째 문장의 내용(교과 핵심 키워드)은 단순 개념 정의가 아닌 학생의 역량 평가 형태로 전체 글 맨 앞에 그대로 유지할 것.
                    3. 작은따옴표('')로 묶인 고유 활동명은 원문 그대로 반드시 보존할 것.
                    4. 문장이 툭툭 끊기지 않도록 호흡이 길고 매끄러운 문장으로 확장할 것. 구체적 숫자 금지.
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
            
            box.success(f"✅ 생성 완료! (연결된 AI 모델: {model_name})")
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
                st.info("✅ 구체적 수치 없이 대학이 선호하는 정성적이고 학술적인 개조식 표현으로 작성되었습니다!")
                
        except Exception as e:
            box.error(f"오류가 발생했습니다: {e}")
            st.info("💡 API 키 재입력 또는 잠시 후 다시 시도해 주세요.")

# ===== 8. 푸터 =====
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px; font-size: 15px;'>
    🏫 <b>학생부 입력 어시스트 시스템 v3.4</b><br>
    만든이: 신선여자고등학교 김명남<br>
</div>
""", unsafe_allow_html=True)
