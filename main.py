import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="학생부 입력 어시스트", layout="wide")

# 2. 사이드바 구성
with st.sidebar:
    st.header("🔑 기본 설정")
    api_key = st.text_input("Google AI API 키", type="password")
    st.markdown("[🔗 무료 API 키 발급](https://aistudio.google.com/)")
    
    st.markdown("---")
    st.markdown("### 📥 자료실 및 관련 링크")
    
    # 기존 링크 유지 및 '선택과목 안내서' 추가 (링크 주소는 필요시 수정하세요)
    st.link_button("📖 신선여자고등학교 가이드북(2026)", "https://ebook.dsummer.co.kr/books/yxly/#p=1", use_container_width=True)
    st.link_button("📖 신선여자고등학교 가이드북(2025)", "https://books.dsummer.co.kr/books/lfyk/#p=1", use_container_width=True)
    st.link_button("📖 신선여고 계열별 학과 안내", "https://ebook.dsummer.co.kr/books/exkt/#p=1", use_container_width=True)
    st.link_button("📄 선택과목 안내서 다운로드", "https://ebook.dsummer.co.kr/books/exkt/#p=1", use_container_width=True) # 기존 링크를 임시로 넣었습니다. 변경 가능합니다.

# 3. 메인 화면 타이틀
st.title("📝 학생부 입력 어시스트")
st.caption("학생을 설명할 수 있는 핵심 키워드와 희망 진로를 입력하면, 가이드북과 교과 핵심 개념이 반영된 맞춤형 기록이 생성됩니다.")

# 4. 본문 레이아웃 (2컬럼)
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 학생 활동 입력")
    
    # UI 구성 (선생님 화면 디자인 반영)
    subject_name = st.text_input("📖 과목/활동 영역 (참고용)", placeholder="예: 세계시민과 지리, 물리학1, 화학, 미적분")
    activity_name = st.text_input("🎯 구체적인 활동명", placeholder="예: 커뮤니티 매핑을 통한 우리 동네 새로 고침 지도 만들기")
    major_name = st.text_input("🎓 진학 희망 학과/계열 ⭐", placeholder="예: 도시공학과 / 사회학과 / 화학공학과 / 기계공학과")
    
    # ⭐ [추가됨] 교과 핵심 아이디어 및 내용 요소 입력창
    st.markdown("🧠 **교과 핵심 아이디어 및 내용 요소 (가이드북 참고)**")
    subject_keywords = st.text_area(
        "선택과목 안내서에 명시된 해당 교과의 '핵심 아이디어'나 '내용 요소'를 입력하세요.", 
        placeholder="예: [물리학] 역학적 에너지 보존, 시공간의 이해 / [화학] 동적 평형, 물질의 구조와 성질",
        height=80
    )
    
    raw_text = st.text_area("✍️ 학생 활동 핵심 키워드 및 내용", height=150, 
                            placeholder="예시)\n- 세계 도시 mbti 조사\n- 인문과학 콘서트 참여\n- 태양광 자동차 제작 및 효율 분석")

with col2:
    st.subheader("2. 추가 반영사항")
    extra_info = st.text_area("🔍 개별화를 위한 추가 강조 포인트", height=150,
                               placeholder="예: 탐구력과 자기주도성 강조, 창의력과 문제해결력 강조")
    
    # 분석 시작 버튼
    st.markdown("<br>", unsafe_allow_html=True) # 버튼 위 간격 띄우기
    if st.button("🚀 학생 맞춤형 개별 문장 생성", use_container_width=True):
        if not api_key:
            st.error("왼쪽 사이드바에서 API 키를 먼저 입력해 주세요!")
        elif not raw_text:
            st.warning("학생 활동 핵심 키워드 및 내용을 입력해 주세요!")
        else:
            with st.spinner("교과 핵심 개념과 가이드북을 연계하여 문장을 생성 중입니다..."):
                try:
                    # 데이터 로드 (엑셀 파일 연동)
                    df_guide = pd.read_excel("data.xlsx", sheet_name="가이드북 항목별 주요 내용")
                    df_verbs = pd.read_excel("data.xlsx", sheet_name="권장 연결 동사")
                    
                    # API 설정
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # ⭐ [업데이트됨] AI 프롬프트 (교과 전문성 강화)
                    prompt = f"""
                    너는 고등학교 베테랑 교사이자 대학 입학사정관이야. 
                    다음 제공된 학생의 활동 내용과 '교과 핵심 키워드'를 바탕으로 학교생활기록부 세부능력 및 특기사항(세특) 문장을 작성해줘.
                    
                    [참고할 대학 권장 표현]: {df_guide['핵심역량/표현'].tolist()[:15]}
                    [마무리 권장 동사]: {df_verbs['핵심 동사'].tolist()}
                    
                    [학생 데이터]
                    - 과목 및 활동명: {subject_name} / {activity_name}
                    - 진학 희망 학과: {major_name}
                    - 학생 활동 내용: {raw_text}
                    - ⭐ 교과 핵심 키워드(내용 요소): {subject_keywords}
                    - 추가 강조 포인트: {extra_info}
                    
                    [작성 원칙]
                    1. 구조: [구체적 동기] -> [실천한 활동] -> [변화된 모습/성취] 순서로 논리적으로 작성할 것.
                    2. 어투: '~함', '~임'으로 끝나는 객관적인 명사형 종결 어미를 사용할 것.
                    3. 교과 전문성 (매우 중요): 제공된 [교과 핵심 키워드]를 학생의 [학생 활동 내용]과 유기적으로 연결하여, 해당 과목에 대한 깊이 있는 이해와 전공 적합성이 돋보이도록 작성할 것. 키워드의 단순 나열은 절대 피할 것.
                    4. 표현: [참고할 대학 권장 표현]을 자연스럽게 문맥에 녹여내고, 문장의 마무리는 가급적 [마무리 권장 동사]를 활용하여 학술적으로 완성할 것.
                    """
                    
                    # AI 호출 및 결과 출력
                    response = model.generate_content(prompt)
                    
                    st.success("✅ 문장 생성 완료!")
                    st.subheader("📝 최종 생성된 학생부 세특 기록")
                    st.info(response.text)
                    
                    # 글자 수 카운팅
                    st.divider()
                    st.caption(f"📏 공백 포함 약 {len(response.text)}자 (정확한 바이트 수는 나이스 시스템에서 최종 확인 요망)")
                    
                except Exception as e:
                    st.error(f"오류가 발생했습니다. 데이터 파일(data.xlsx)이나 API 키가 올바른지 확인해주세요.\n상세 오류: {e}")
