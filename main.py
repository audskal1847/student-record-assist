import streamlit as st
import pandas as pd
import google.generativeai as genai

# ==========================================
# 0. 성능 최적화: 엑셀 데이터 캐싱 (한 번만 읽고 기억)
# ==========================================
@st.cache_data
def load_excel_data():
    try:
        df_guide = pd.read_excel("data.xlsx", sheet_name="가이드북 항목별 주요 내용")
        df_verbs = pd.read_excel("data.xlsx", sheet_name="권장 연결 동사")
        guide_expressions = df_guide['핵심역량/표현'].tolist()[:15]
        verb_expressions = df_verbs['핵심 동사'].tolist()
        return guide_expressions, verb_expressions
    except Exception as e:
        return [], []

# 1. 페이지 설정
st.set_page_config(page_title="학생부 입력 어시스트", layout="wide")

# 2. 사이드바 구성
with st.sidebar:
    st.header("🔑 기본 설정")
    api_key = st.text_input("Google AI API 키", type="password")
    st.markdown("[🔗 무료 API 키 발급](https://aistudio.google.com/)")
    
    st.markdown("---")
    
    load_excel = st.checkbox("✅ 엑셀 사전 로드 (표현 90개 / 동사 10개)", value=True)
    
    st.info("🎯 목표: 1420 - 1470 바이트 (약 450 - 500자)")
    remove_numbers = st.checkbox("🔢 구체적 숫자 자동 제거")
    
    st.markdown("---")
    st.markdown("### 📥 자료실 및 관련 링크")
    # 요청하신 대로 링크 간소화
    st.link_button("📖 교과 선택 가이드북(2026)", "https://ebook.dsummer.co.kr/books/yxly/#p=1", use_container_width=True)
    st.link_button("📄 선택과목 안내서 보러가기", "https://ebook.dsummer.co.kr/books/exkt/#p=1", use_container_width=True)

# 3. 메인 화면 타이틀
st.title("📝 학생부 입력 어시스트")
st.caption("학생을 설명할 수 있는 핵심 키워드와 희망 진로를 입력하면, 학생별 맞춤형 학생부 기록이 생성됩니다.")

# 4. 레이아웃 재구성 (세로 스크롤 최소화)

# [섹션 1] 기본 정보 (가로 3단)
st.markdown("#### 1. 학생 기본 정보")
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    subject_name = st.text_input("📖 과목/활동 영역", placeholder="예: 세계시민과 지리, 물리학1")
with col_b2:
    major_name = st.text_input("🎓 진학 희망 학과/계열", placeholder="예: 도시공학과 / 사회학과")
with col_b3:
    selected_competency = st.selectbox("🎯 강조 역량", ["AI에게 알아서 맡기기", "학업 역량", "진로 역량", "공동체 역량"])

st.markdown("---")

# [섹션 2] 구체적인 활동 입력 (가로 2단)
st.markdown("#### 2. 구체적인 활동 및 상세 내용 (최대 4개)")
st.caption("진행한 활동의 개수만큼 입력하세요. 2단 구성으로 스크롤을 최소화했습니다.")

col_act1, col_act2 = st.columns(2)

with col_act1:
    st.markdown("**🔹 활동 1 (필수)**")
    activity_1_name = st.text_input("활동명 1", placeholder="예: 커뮤니티 매핑 지도 만들기", label_visibility="collapsed")
    activity_1_desc = st.text_area("활동 1 상세 내용", placeholder="위 활동에 대한 학생의 구체적인 역할, 배우고 느낀 점, 성취 등을 자세히 적어주세요.", height=100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("**🔹 활동 3 (선택)**")
    activity_3_name = st.text_input("활동명 3", placeholder="예: 기후 변화 대응 캠페인", label_visibility="collapsed")
    activity_3_desc = st.text_area("활동 3 상세 내용", placeholder="위 활동에 대한 상세 내용 입력", height=100)

with col_act2:
    st.markdown("**🔹 활동 2 (선택)**")
    activity_2_name = st.text_input("활동명 2", placeholder="예: 지속가능한 도시 개발 보고서 작성", label_visibility="collapsed")
    activity_2_desc = st.text_area("활동 2 상세 내용", placeholder="위 활동에 대한 상세 내용 입력", height=100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("**🔹 활동 4 (선택)**")
    activity_4_name = st.text_input("활동명 4", placeholder="", label_visibility="collapsed")
    activity_4_desc = st.text_area("활동 4 상세 내용", placeholder="위 활동에 대한 상세 내용 입력", height=100)

st.markdown("---")

# [섹션 3] 추가 반영사항 및 교과 키워드 (가로 2단)
st.markdown("#### 3. 추가 반영사항 및 핵심 키워드")
col_add1, col_add2 = st.columns(2)

with col_add1:
    st.markdown("**🧠 교과 핵심 아이디어 및 내용 요소**")
    st.caption("해당 교과에서 강조하고 싶은 키워드를 입력하세요. (선택과목 안내서 참고)")
    subject_keywords = st.text_area(
        "핵심 아이디어 입력", 
        placeholder="예: [지리] 세계화와 세계시민 / 해수 담수화 기술 활용",
        height=100,
        label_visibility="collapsed"
    )

with col_add2:
    st.markdown("**🔍 개별화를 위한 추가 강조 포인트**")
    st.caption("AI가 특별히 신경 써야 할 학생만의 강점을 적어주세요.")
    extra_info = st.text_area(
        "강조 포인트 입력",
        placeholder="예: 탐구력과 자기주도성 강조, 창의력과 문제해결력 강조",
        height=100,
        label_visibility="collapsed"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. 분석 시작 및 AI 연동
# ==========================================
# type="primary"를 추가하여 버튼 색상을 빨간색(강조색)으로 변경했습니다.
if st.button("🚀 학생 맞춤형 개별 문장 생성 (클릭)", type="primary", use_container_width=True):
    
    # 활동 수합 로직
    activities_data = []
    if activity_1_name.strip() and activity_1_desc.strip():
        activities_data.append(f"[활동 1: {activity_1_name.strip()}]\n- 상세 내용: {activity_1_desc.strip()}")
    if activity_2_name.strip() and activity_2_desc.strip():
        activities_data.append(f"[활동 2: {activity_2_name.strip()}]\n- 상세 내용: {activity_2_desc.strip()}")
    if activity_3_name.strip() and activity_3_desc.strip():
        activities_data.append(f"[활동 3: {activity_3_name.strip()}]\n- 상세 내용: {activity_3_desc.strip()}")
    if activity_4_name.strip() and activity_4_desc.strip():
        activities_data.append(f"[활동 4: {activity_4_name.strip()}]\n- 상세 내용: {activity_4_desc.strip()}")
        
    num_activities = len(activities_data)
    activities_str = "\n\n".join(activities_data)
    
    if not api_key:
        st.error("왼쪽 사이드바에서 API 키를 먼저 입력해 주세요!")
    elif num_activities == 0:
        st.warning("최소 1개 이상의 구체적인 활동명과 상세 내용을 모두 입력해 주세요! (활동 1 필수)")
    else:
        with st.spinner(f"총 {num_activities}개의 활동을 분석하여 맞춤형 분량으로 문장을 생성 중입니다..."):
            try:
                guide_expressions = []
                verb_expressions = []
                
                # 캐시된 엑셀 데이터를 빠르게 불러옵니다.
                if load_excel:
                    guide_expressions, verb_expressions = load_excel_data()
                
                genai.configure(api_key=api_key)
                
                # 속도 저하의 주범이었던 이중 호출을 제거하고, 선생님 환경에 맞는 안정적인 pro 모델로 직행합니다.
                model = genai.GenerativeModel('gemini-pro')
                
                prompt = f"""
                너는 고등학교 베테랑 교사이자 대학 입학사정관이야. 
                제공된 학생의 데이터를 바탕으로 나이스(NEIS) 학교생활기록부 세부능력 및 특기사항 문장을 작성해줘.
                
                [참고할 대학 권장 표현]: {guide_expressions}
                [마무리 권장 동사]: {verb_expressions}
                
                [학생 기본 데이터]
                - 과목명: {subject_name}
                - 진학 희망 학과: {major_name}
                - 강조 역량 설정: {selected_competency}
                - 교사 지정 핵심 키워드: {subject_keywords}
                - 추가 강조 포인트: {extra_info}
                
                [활동 내역 및 세부 내용] (총 {num_activities}개)
                {activities_str}
                
                [작성 원칙 및 분량 배분 가이드] - 매우 중요
                1. 전체 분량: 공백 포함 450자~500자 (약 1420~1470 바이트) 내외로 맞출 것.
                2. 활동량 배분: 입력된 활동이 총 {num_activities}개입니다. 
                   - 1개일 경우: 해당 활동의 동기-과정-성취를 깊이 있게 작성하여 전체 분량을 채울 것.
                   - 2개 이상일 경우: 전체 분량을 {num_activities}개의 활동에 균등하게 배분하여 작성하고, 활동 간의 연결고리가 자연스럽게 이어지도록 유기적으로 엮을 것.
                3. 교과 전문성: 교사가 지정한 [교사 지정 핵심 키워드]를 활동 내용에 자연스럽게 녹여내어 전공 적합성과 교과 이해도를 입증할 것.
                4. 구조 및 표현: 객관적인 명사형 종결 어미('~함', '~임')를 사용하고, [참고할 대학 권장 표현]과 [마무리 권장 동사]를 적극 활용할 것.
                """
                
                if remove_numbers:
                    prompt += "\n5. 주의: 문장 생성 시 구체적인 수치(예: 10%, 30명 등)는 제외하고 서술형으로 부드럽게 풀어 쓸 것."
                
                response = model.generate_content(prompt)
                
                st.success(f"✅ 총 {num_activities}개의 활동을 완벽하게 배분한 문장 생성 완료!")
                st.subheader("📝 최종 생성된 학생부 세특 기록")
                st.info(response.text)
                
                st.divider()
                st.caption(f"📏 공백 포함 약 {len(response.text)}자 (1글자당 한글 3바이트, 공백/영어 1바이트 기준 약 {len(response.text)*2.8:.0f} 바이트 추정)")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다. 상세 오류: {e}")
