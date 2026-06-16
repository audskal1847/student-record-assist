import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="학생부 입력 어시스트", layout="wide")

# 2. 사이드바 구성 (선생님의 기존 UI 완벽 복원)
with st.sidebar:
    st.header("🔑 기본 설정")
    api_key = st.text_input("Google AI API 키", type="password")
    st.markdown("[🔗 무료 API 키 발급](https://aistudio.google.com/)")
    
    st.markdown("---")
    
    # 선생님이 만드신 체크박스와 인포 박스 유지
    load_excel = st.checkbox("✅ 엑셀 사전 로드 (표현 90개 / 동사 10개)", value=True)
    load_pdf = st.checkbox("✅ PDF 가이드북 1개 로드", value=True)
    
    st.info("🎯 목표: 1420~1470 바이트")
    remove_numbers = st.checkbox("🔢 구체적 숫자 자동 제거")
    
    st.markdown("---")
    st.markdown("### 📥 자료실 및 관련 링크")
    # 기존 링크 + 새로운 '선택과목 안내서' 링크 추가
    st.link_button("📖 신선여자고등학교 가이드북(2026)", "https://ebook.dsummer.co.kr/books/yxly/#p=1", use_container_width=True)
    st.link_button("📖 신선여자고등학교 가이드북(2025)", "https://books.dsummer.co.kr/books/lfyk/#p=1", use_container_width=True)
    st.link_button("📖 신선여고 계열별 학과 안내", "https://ebook.dsummer.co.kr/books/exkt/#p=1", use_container_width=True)
    st.link_button("📄 선택과목 안내서 보러가기", "여기에_링크를_넣어주세요", use_container_width=True)

# 3. 메인 화면 타이틀
st.title("📝 학생부 입력 어시스트")
st.caption("학생을 설명할 수 있는 핵심 키워드와 희망 진로를 입력하면, 학생별 맞춤형 학생부 기록이 생성됩니다.")

# 4. 본문 레이아웃 (2컬럼)
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 학생 활동 입력")
    
    # 기존 UI 요소 유지
    subject_name = st.text_input("📖 과목/활동 영역 (참고용)", placeholder="예: 세계시민과 지리, 물리학1, 영어독해와 작문, 미적분")
    activity_name = st.text_input("🎯 구체적인 활동명", placeholder="예: 커뮤니티 매핑을 통한 우리 동네 새로 고침 지도 만들기")
    major_name = st.text_input("🎓 진학 희망 학과/계열 ⭐", placeholder="예: 도시공학과 / 사회학과 / 전자공학과 / 기계공학과")
    
    # 선생님이 만드신 '강조 역량' 드롭다운 유지
    selected_competency = st.selectbox("🎯 강조 역량", ["AI에게 알아서 맡기기", "학업 역량", "진로 역량", "공동체 역량"])
    
    # ⭐ [새롭게 추가된 부분] 교과 핵심 아이디어 및 내용 요소
    st.markdown("**🧠 교과 핵심 아이디어 및 내용 요소 (선택과목 안내서 참고)**")
    subject_keywords = st.text_area(
        "안내서에 명시된 해당 교과의 핵심 키워드를 입력하세요.", 
        placeholder="예: [물리학] 역학적 에너지 보존, 시공간의 이해 / [화학] 동적 평형, 물질의 구조와 성질",
        height=80,
        label_visibility="collapsed"
    )
    
    raw_text = st.text_area("✍️ 학생 활동 핵심 키워드 및 내용", height=150, 
                            placeholder="예시)\n- 세계 도시 mbti 조사\n- 인문과학 콘서트\n- 디지털 지도 제작")

with col2:
    st.subheader("2. 추가 반영사항")
    extra_info = st.text_area("🔍 개별화를 위한 추가 강조 포인트", height=150,
                               placeholder="예: 탐구력과 자기주도성 강조, 창의력과 문제해결력 강조")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 분석 시작 버튼
    if st.button("🚀 학생 맞춤형 개별 문장 생성", use_container_width=True):
        if not api_key:
            st.error("왼쪽 사이드바에서 API 키를 먼저 입력해 주세요!")
        elif not raw_text:
            st.warning("학생 활동 핵심 키워드 및 내용을 입력해 주세요!")
        else:
            with st.spinner("가이드북과 교과 핵심 개념을 연계하여 문장을 생성 중입니다..."):
                try:
                    # 엑셀 데이터 로드 로직
                    guide_expressions = ""
                    verb_expressions = ""
                    
                    if load_excel:
                        df_guide = pd.read_excel("data.xlsx", sheet_name="가이드북 항목별 주요 내용")
                        df_verbs = pd.read_excel("data.xlsx", sheet_name="권장 연결 동사")
                        guide_expressions = df_guide['핵심역량/표현'].tolist()[:15]
                        verb_expressions = df_verbs['핵심 동사'].tolist()
                    
                    # API 설정
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # 프롬프트 구성 (기존 기능 + 숫자 제거 옵션 + 교과 키워드 반영)
                    prompt = f"""
                    너는 고등학교 베테랑 교사이자 대학 입학사정관이야. 
                    다음 제공된 학생의 활동 내용과 '교과 핵심 키워드'를 바탕으로 학교생활기록부 세부능력 및 특기사항 문장을 작성해줘.
                    
                    [참고할 대학 권장 표현]: {guide_expressions}
                    [마무리 권장 동사]: {verb_expressions}
                    
                    [학생 데이터]
                    - 과목 및 활동명: {subject_name} / {activity_name}
                    - 진학 희망 학과: {major_name}
                    - 강조 역량 설정: {selected_competency}
                    - 학생 활동 내용: {raw_text}
                    - ⭐ 교과 핵심 키워드(내용 요소): {subject_keywords}
                    - 추가 강조 포인트: {extra_info}
                    
                    [작성 원칙]
                    1. 구조: [동기] -> [활동] -> [성취] 순서로 논리적으로 작성할 것.
                    2. 어투: '~함', '~임'으로 끝나는 객관적인 명사형 종결 어미를 사용할 것.
                    3. 교과 전문성 (매우 중요): 제공된 [교과 핵심 키워드]를 단순 나열하지 말고, [학생 활동 내용]에 자연스럽게 녹여내어 전공 적합성과 깊이 있는 학업 역량을 보여줄 것.
                    """
                    
                    # '구체적 숫자 자동 제거' 체크박스가 켜져 있을 때의 조건 추가
                    if remove_numbers:
                        prompt += "\n4. 주의: 문장 생성 시 구체적인 수치(예: 10%, 30명 등)는 제외하고 서술형으로 부드럽게 풀어 쓸 것."
                    
                    # AI 호출 및 결과 출력
                    response = model.generate_content(prompt)
                    
                    st.success("✅ 문장 생성 완료!")
                    st.subheader("📝 최종 생성된 학생부 세특 기록")
                    st.info(response.text)
                    
                    st.divider()
                    st.caption(f"📏 공백 포함 약 {len(response.text)}자 (정확한 바이트 수는 나이스 시스템에서 확인하세요)")
                    
                except Exception as e:
                    st.error(f"오류가 발생했습니다. 상세 오류: {e}")
