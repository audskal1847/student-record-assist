import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="학생부 입력 어시스트", layout="wide")

# 2. 사이드바 구성 (기존 UI 유지)
with st.sidebar:
    st.header("🔑 기본 설정")
    api_key = st.text_input("Google AI API 키", type="password")
    st.markdown("[🔗 무료 API 키 발급](https://aistudio.google.com/)")
    
    st.markdown("---")
    
    # 체크박스 및 인포 박스 유지
    load_excel = st.checkbox("✅ 엑셀 사전 로드 (표현 90개 / 동사 10개)", value=True)
    load_pdf = st.checkbox("✅ PDF 가이드북 1개 로드", value=True)
    
    st.info("🎯 목표: 1420~1470 바이트 (약 450~500자)")
    remove_numbers = st.checkbox("🔢 구체적 숫자 자동 제거")
    
    st.markdown("---")
    st.markdown("### 📥 자료실 및 관련 링크")
    st.link_button("📖 신선여자고등학교 가이드북(2026)", "https://ebook.dsummer.co.kr/books/yxly/#p=1", use_container_width=True)
    st.link_button("📖 신선여자고등학교 가이드북(2025)", "https://books.dsummer.co.kr/books/lfyk/#p=1", use_container_width=True)
    st.link_button("📖 신선여고 계열별 학과 안내", "https://ebook.dsummer.co.kr/books/exkt/#p=1", use_container_width=True)
    st.link_button("📄 선택과목 안내서 보러가기", "https://ebook.dsummer.co.kr/books/exkt/#p=1", use_container_width=True)

# 3. 메인 화면 타이틀
st.title("📝 학생부 입력 어시스트")
st.caption("학생을 설명할 수 있는 핵심 키워드와 희망 진로를 입력하면, 학생별 맞춤형 학생부 기록이 생성됩니다.")

# 4. 본문 레이아웃 (2컬럼)
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 학생 활동 입력")
    
    subject_name = st.text_input("📖 과목/활동 영역 (참고용)", placeholder="예: 세계시민과 지리, 물리학1, 영어독해와 작문")
    major_name = st.text_input("🎓 진학 희망 학과/계열 ⭐", placeholder="예: 도시공학과 / 사회학과 / 전자공학과")
    selected_competency = st.selectbox("🎯 강조 역량", ["AI에게 알아서 맡기기", "학업 역량", "진로 역량", "공동체 역량"])
    
    st.markdown("---")
    st.markdown("**🎯 구체적인 활동명 입력 (최대 4개)**")
    st.caption("진행한 활동의 개수만큼 입력하세요. AI가 개수에 맞춰 분량을 자동 배분합니다.")
    
    # ⭐ [수정된 부분] 4개의 개별 활동명 입력창
    activity_1 = st.text_input("활동명 1 (필수)", placeholder="예: 커뮤니티 매핑 지도 만들기")
    activity_2 = st.text_input("활동명 2 (선택)", placeholder="예: 지속가능한 도시 개발 보고서 작성")
    activity_3 = st.text_input("활동명 3 (선택)", placeholder="예: 기후 변화 대응 캠페인")
    activity_4 = st.text_input("활동명 4 (선택)", placeholder="")
    
    st.markdown("---")
    
    st.markdown("**🧠 교과 핵심 아이디어 및 내용 요소 (선택과목 안내서 참고)**")
    subject_keywords = st.text_area(
        "해당 교과의 핵심 키워드를 입력하세요.", 
        placeholder="예: [물리학] 역학적 에너지 보존, 시공간의 이해",
        height=80,
        label_visibility="collapsed"
    )
    
    raw_text = st.text_area("✍️ 학생 활동 핵심 키워드 및 상세 내용", height=150, 
                            placeholder="위에서 입력한 활동(들)에 대한 학생의 구체적인 역할, 배우고 느낀 점, 성취 등을 자세히 적어주세요.")

with col2:
    st.subheader("2. 추가 반영사항")
    extra_info = st.text_area("🔍 개별화를 위한 추가 강조 포인트", height=150,
                               placeholder="예: 탐구력과 자기주도성 강조, 창의력과 문제해결력 강조")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 분석 시작 버튼
    if st.button("🚀 학생 맞춤형 개별 문장 생성", use_container_width=True):
        
        # 입력된 활동 목록 리스트화 (빈 칸 제외)
        activities = [act.strip() for act in [activity_1, activity_2, activity_3, activity_4] if act.strip()]
        
        if not api_key:
            st.error("왼쪽 사이드바에서 API 키를 먼저 입력해 주세요!")
        elif not activities:
            st.warning("최소 1개 이상의 구체적인 활동명을 입력해 주세요!")
        elif not raw_text:
            st.warning("학생 활동 핵심 키워드 및 상세 내용을 입력해 주세요!")
        else:
            with st.spinner("활동 개수와 교과 핵심 개념을 분석하여 맞춤형 분량으로 문장을 생성 중입니다..."):
                try:
                    guide_expressions = ""
                    verb_expressions = ""
                    
                    if load_excel:
                        df_guide = pd.read_excel("data.xlsx", sheet_name="가이드북 항목별 주요 내용")
                        df_verbs = pd.read_excel("data.xlsx", sheet_name="권장 연결 동사")
                        guide_expressions = df_guide['핵심역량/표현'].tolist()[:15]
                        verb_expressions = df_verbs['핵심 동사'].tolist()
                    
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    num_activities = len(activities)
                    activities_str = ", ".join(activities)
                    
                    # ⭐ [업데이트됨] 다중 활동 분량 배분 및 목표 바이트 설정 프롬프트
                    prompt = f"""
                    너는 고등학교 베테랑 교사이자 대학 입학사정관이야. 
                    제공된 학생의 데이터를 바탕으로 나이스(NEIS) 학교생활기록부 세부능력 및 특기사항 문장을 작성해줘.
                    
                    [참고할 대학 권장 표현]: {guide_expressions}
                    [마무리 권장 동사]: {verb_expressions}
                    
                    [학생 데이터]
                    - 과목명: {subject_name}
                    - 진학 희망 학과: {major_name}
                    - 강조 역량 설정: {selected_competency}
                    - 교과 핵심 키워드: {subject_keywords}
                    - 추가 강조 포인트: {extra_info}
                    
                    [활동 내역 및 세부 내용]
                    - 수행한 구체적 활동 목록 (총 {num_activities}개): {activities_str}
                    - 학생 활동 세부 내용: {raw_text}
                    
                    [작성 원칙 및 분량 배분 가이드] - 매우 중요
                    1. 전체 분량: 공백 포함 450자~500자 (약 1420~1470 바이트) 내외로 맞출 것.
                    2. 활동량 배분: 입력된 활동이 총 {num_activities}개입니다. 
                       - 1개일 경우: 해당 활동의 동기-과정-성취를 깊이 있게 작성하여 전체 분량(100%)을 채울 것.
                       - 2개 이상일 경우: 전체 분량을 {num_activities}개의 활동에 균등하게 배분(예: 2개면 50%씩, 3개면 33%씩)하여, 활동 간의 연결고리가 자연스럽게 이어지도록 유기적으로 엮어서 작성할 것. 특정 활동에만 치우치지 않게 할 것.
                    3. 교과 전문성: [교과 핵심 키워드]를 [활동 세부 내용]에 녹여내어 전공 적합성을 드러낼 것.
                    4. 구조 및 표현: 객관적인 명사형 종결 어미('~함', '~임')를 사용하고, [참고할 대학 권장 표현]과 [마무리 권장 동사]를 적절히 활용할 것.
                    """
                    
                    if remove_numbers:
                        prompt += "\n5. 주의: 문장 생성 시 구체적인 수치(예: 10%, 30명 등)는 제외하고 서술형으로 부드럽게 풀어 쓸 것."
                    
                    response = model.generate_content(prompt)
                    
                    st.success(f"✅ 총 {num_activities}개의 활동을 반영한 문장 생성 완료!")
                    st.subheader("📝 최종 생성된 학생부 세특 기록")
                    st.info(response.text)
                    
                    st.divider()
                    st.caption(f"📏 공백 포함 약 {len(response.text)}자 (1글자당 한글 3바이트, 공백/영어 1바이트 기준 약 {len(response.text)*2.8:.0f} 바이트 추정)")
                    
                except Exception as e:
                    st.error(f"오류가 발생했습니다. 상세 오류: {e}")
