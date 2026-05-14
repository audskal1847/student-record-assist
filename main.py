import streamlit as st
import google.generativeai as genai
import PyPDF2, pandas as pd, glob, os, re

st.set_page_config(page_title="학생부 입력 어시스트", layout="wide")

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
    for keys in [("1.5","flash","8b"), ("1.5","flash"), ("2.5","flash"), ("2.0","flash"), ("flash",), ("pro",)]:
        for m in models:
            if any(s in m for s in ["vision","embedding","exp","thinking","tts","image"]): continue
            if all(k in m for k in keys): return m
    return models[0] if models else None

# ===== 3. 구체적 숫자 자동 치환 =====
def remove_numbers(text):
    """검증되지 않은 활동 관련 숫자를 자연스러운 정성적 표현으로 치환"""
    
    # "약 N", "N여" 같은 어림 표현 먼저 처리
    text = re.sub(r'약\s*\d+\s*여?\s*명의?', '여러 명의', text)
    text = re.sub(r'약\s*\d+\s*여?\s*곳을?', '여러 곳을', text)
    text = re.sub(r'약\s*\d+\s*여?\s*개의?', '여러', text)
    text = re.sub(r'\d+\s*여\s*명', '여러 명', text)
    text = re.sub(r'\d+\s*여\s*곳', '여러 곳', text)
    text = re.sub(r'\d+\s*여\s*개', '여러 개', text)
    text = re.sub(r'\d+\s*여\s*편', '여러 편', text)
    text = re.sub(r'\d+\s*여\s*권', '여러 권', text)
    text = re.sub(r'\d+\s*여\s*건', '여러 건', text)
    
    # 사람 단위
    text = re.sub(r'\d+\s*명의', '여러 명의', text)
    text = re.sub(r'\d+\s*명과', '여러 명과', text)
    text = re.sub(r'\d+\s*명을', '여러 명을', text)
    text = re.sub(r'\d+\s*명에게', '여러 명에게', text)
    text = re.sub(r'\d+\s*명', '여러 명', text)
    
    # 장소 단위
    text = re.sub(r'\d+\s*곳을', '여러 곳을', text)
    text = re.sub(r'\d+\s*곳의', '여러 곳의', text)
    text = re.sub(r'\d+\s*곳에', '여러 곳에', text)
    text = re.sub(r'\d+\s*곳', '여러 곳', text)
    text = re.sub(r'\d+\s*군데', '여러 군데', text)
    text = re.sub(r'\d+\s*점포', '여러 점포', text)
    text = re.sub(r'\d+\s*개\s*점포', '여러 점포', text)
    
    # 자료/물건 단위
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
    
    # 횟수 단위
    text = re.sub(r'\d+\s*회의?', '수차례', text)
    text = re.sub(r'\d+\s*차례', '수차례', text)
    text = re.sub(r'\d+\s*번의?', '여러 번', text)
    
    # SNS/온라인 단위
    text = re.sub(r'\d+\s*개의?\s*게시물', '여러 게시물', text)
    text = re.sub(r'\d+\s*건의?\s*게시물', '여러 게시물', text)
    
    # 어림 표현 정리
    text = re.sub(r'약\s+여러', '여러', text)
    text = re.sub(r'약\s+다수', '다수', text)
    text = re.sub(r'약\s+수차례', '수차례', text)
    
    # 남은 어색한 패턴 정리
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)
    
    return text

# ===== 4. 결과 정화 =====
def clean(text, subject=""):
    # 마크다운 제거
    for pat in [r'\*\*(.*?)\*\*', r'\*(.*?)\*', r'__(.*?)__', r'`(.*?)`']:
        text = re.sub(pat, r'\1', text)
    text = re.sub(r'^#+\s*|^[\-\*\+]\s+', '', text, flags=re.MULTILINE)
    # 과목명 제거
    if subject:
        for pat in [f"{subject} 수업을 통해", f"{subject} 시간에", f"{subject}에서", f"{subject} 교과", subject]:
            text = re.sub(pat + r'\s*,?\s*', '', text)
    # '학생은/이' 제거
    for pat in [r'본\s*학생[은이]\s*', r'해당\s*학생[은이]\s*', r'이\s*학생[은이]\s*', r'학생[은이을]\s*', r'학생에게\s*']:
        text = re.sub(pat, '', text)
    # 줄바꿈 → 공백
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'^[은는이가을를에]\s+', '', text.strip())
    # 숫자 제거
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
    st.caption("🔢 구체적 숫자 자동 제거")
    

# ===== 6. 메인 화면 =====
st.title("📝 학생부 입력 어시스트")
st.caption("키워드와 진로를 입력하면, 학생별 맞춤형 학생부 문장을 AI가 생성합니다.")

c1, c2 = st.columns(2)
with c1:
    st.subheader("1. 학생 활동 입력")
    subject = st.text_input("📖 과목/활동 영역 (참고용)", placeholder="예: 여행지리")
    project_title = st.text_input("🎯 프로젝트 정식 명칭", placeholder="예: 커뮤니티 매핑을 통한 우리 동네 새로 고침 지도 만들기")
    aspiration = st.text_input("🎓 진학 희망 학과/계열 ⭐", placeholder="예: 도시공학과 / 사회학과")
    if df_guide is not None:
        col0 = df_guide.columns[0]
        options = ["AI에게 알아서 맡기기"] + df_guide[col0].dropna().unique().tolist()
        focus = st.selectbox("🎯 강조 역량", options)
    else:
        focus = "AI에게 알아서 맡기기"
    raw_text = st.text_area("✍️ 학생 활동 키워드", height=180, placeholder="예시)\n- 우리 동네 안전 사각지대 발굴\n- 주민 인터뷰\n- 디지털 지도 제작")

with c2:
    st.subheader("2. 추가 지시사항")
    extra = st.text_area("🔍 강조 포인트", height=180, placeholder="예: 탐구력과 자기주도성 강조")
    st.write("")
    submit = st.button("🚀 맞춤형 문장 생성", type="primary", use_container_width=True)

st.divider()

# ===== 7. 생성 로직 =====
if submit:
    if not api_key: st.error("API 키를 입력해 주세요!")
    elif not raw_text: st.warning("학생 활동 키워드를 입력해 주세요!")
    elif df_guide is None: st.error("data.xlsx 파일이 필요합니다!")
    else:
        box = st.empty()
        try:
            box.info("🔍 AI 모델 탐색 중...")
            model_name = find_model(api_key)
            if not model_name: raise Exception("사용 가능한 모델 없음")
            model = genai.GenerativeModel(model_name)
            
            # 자료 준비
            col0 = df_guide.columns[0]
            guide = df_guide[df_guide[col0] == focus].to_string(index=False) if focus != "AI에게 알아서 맡기기" else df_guide.to_string(index=False)
            verbs = df_verbs.to_string(index=False) if df_verbs is not None else ""
            pdf_text = load_pdfs(pdf_files)[:3000] if pdf_files else ""
            
            # 목표 바이트
            target_byte, target_min, target_max = 1445, 1420, 1470
            target_chars = 481
            
            project_part = f"\n🎯 모든 활동은 '{project_title}' 프로젝트의 일환임. 본문 첫 문장에서 작은따옴표('')로 감싸 프로젝트명을 명시. 이후 '해당 프로젝트', '본 활동' 등으로 호명." if project_title.strip() else ""
            
            aspiration_part = f"""
🎓 진학 희망: '{aspiration}'
- 이 학과·계열 관점에서 활동을 재해석하여 강조
- 결말부 약 15%를 '{aspiration}' 관련 학문적 호기심·후속 탐구 의지로 자연스럽게 마무리
- ❌ "○○학과 진학 희망" 같은 직접 선언 금지!
- ✅ "○○ 분야에 대한 관심을 심화함" 등 우회 표현 사용
""" if aspiration.strip() else ""
            
            prompt = f"""당신은 20년 경력의 베테랑 학생부 작성 교사입니다. 학생 활동 키워드를 바탕으로 풍성한 학생부 문장을 작성해 주세요.

🚨 [필수 분량] 한글 정확히 {target_chars}자(±8자) / 1420~1470바이트 / 한 단락(줄바꿈 절대 금지)!

🚨🚨🚨 [가장 중요한 금지 사항 - 구체적 숫자 절대 금지!] 🚨🚨🚨
검증되지 않은 활동 수치를 절대 만들어내지 마세요!

❌ 절대 쓰지 말 것:
- "주민 7명을 인터뷰" ❌
- "사진 10장 촬영" ❌  
- "점포 30개 방문" ❌
- "게시물 100여 건 분석" ❌
- "5곳의 소품샵" ❌
- "3차례 회의" ❌
- "10편의 논문" ❌
- 그 어떤 구체적 숫자(1, 2, 3, ...100 등) 포함 표현 모두 금지!

✅ 대신 이렇게 쓸 것:
- "여러 명의 주민을 인터뷰" ✅
- "다수의 사진을 촬영" ✅
- "여러 점포를 방문" ✅
- "관련 게시물을 분석" ✅
- "여러 소품샵을 답사" ✅
- "수차례 회의를 거쳐" ✅
- "관련 문헌을 폭넓게 탐독" ✅

📌 이유: 검증되지 않은 허구의 수치는 학생부 작성 윤리에 어긋남.
📌 정성적 표현('여러', '다수의', '수차례', '폭넓게', '심도 있게')으로 풍성함을 만들 것!

🚨 [기타 절대 금지]
1. 과목명('{subject}' 등) 출력 금지
2. 마크다운(별표, #, - 등) 사용 금지  
3. '학생은/학생이' 등 주어 표현 금지
4. 진학 직접 선언 금지

{project_part}
{aspiration_part}

[작성 규칙]
- 명사형 종결('~함', '~임', '~보여줌')
- 5단계 구조: 동기(15%) → 탐구과정(25%) → 협력·문제해결(25%) → 성장(20%) → 진로 연계(15%)
- 핵심 표현 2~3개, 권장 동사 3~4개 자연스럽게 활용
- 디테일은 숫자가 아닌 '행동·태도·과정 묘사'로 표현
  (예: "꼼꼼히 분석함", "심층적으로 탐구함", "다각도로 검토함")

[엑셀 핵심 표현]
{guide}

[권장 동사]
{verbs}

[PDF 가이드북 참고]
{pdf_text}

[학생 활동 키워드]
{raw_text}

[추가 지시]
{extra if extra else "없음"}

→ 줄바꿈 없는 한 단락으로 본문만 출력! 구체적 숫자 절대 금지!"""
            
            box.warning(f"🤖 '{model_name}'로 생성 중...")
            response = model.generate_content(prompt)
            result = clean(response.text.strip(), subject)
            cb = byte_count(result)
            
            # 자동 조절
            if not (target_min <= cb <= target_max):
                if cb > target_max:
                    box.warning(f"📏 압축 중... ({cb}바이트 → 목표 {target_byte})")
                    adj_prompt = f"""아래 문장을 정확히 한글 {target_chars}자로 압축하세요. 구체적 숫자(N명, N곳, N장 등) 사용 금지, 별표·과목명·'학생은' 금지, 명사형 종결, 한 단락 유지.

[원본]
{result}

→ 본문만 출력!"""
                elif cb < target_min:
                    box.warning(f"📏 확장 중... ({cb}바이트 → 목표 {target_byte})")
                    adj_prompt = f"""아래 문장을 정확히 한글 {target_chars}자로 확장하세요. 구체적 숫자 절대 금지(대신 '여러', '다수의', '수차례' 사용), 별표·과목명·'학생은' 금지, 명사형 종결, 한 단락 유지. 활동 디테일은 '행동·태도 묘사'로 풍성하게.

[원본]
{result}

→ 본문만 출력!"""
                
                try:
                    new_result = clean(model.generate_content(adj_prompt).text.strip(), subject)
                    new_cb = byte_count(new_result)
                    if abs(new_cb - target_byte) < abs(cb - target_byte):
                        result, cb = new_result, new_cb
                except: pass
            
            # 최종 안전장치
            if cb > target_max:
                sentences = re.split(r'(?<=[.!?])\s+', result)
                trimmed = ""
                for s in sentences:
                    test = trimmed + (" " if trimmed else "") + s
                    if byte_count(test) <= target_max:
                        trimmed = test
                    else: break
                if trimmed: result, cb = trimmed.strip(), byte_count(trimmed)
            
            # 결과 출력
            box.success(f"✅ 생성 완료! (모델: {model_name})")
            st.subheader(f"📋 생성된 문장{' - ' + aspiration + ' 맞춤' if aspiration else ''}")
            st.text_area("결과:", value=result, height=350, label_visibility="collapsed")
            
            # 통계
            c_a, c_b, c_c, c_d = st.columns(4)
            c_a.metric("📊 글자", f"{len(result)}자")
            c_b.metric("💾 바이트", f"{cb}byte")
            c_c.metric("🎯 목표", "1420~1470")
            
            if target_min <= cb <= target_max:
                c_d.metric("✅ 상태", "완벽")
                st.success("✨ 목표 범위(1420~1470) 완벽 달성! 나이스에 바로 입력 가능!")
            elif cb <= 1500:
                c_d.metric("📝 상태", "사용가능")
                st.info(f"📝 나이스 한도(1500) 이내. 그대로 사용 가능!")
            elif cb < target_min:
                c_d.metric("⚠️ 상태", f"-{target_min - cb}")
                st.warning(f"⚠️ 목표보다 {target_min - cb}바이트 부족. 다시 생성을 권장합니다.")
            else:
                c_d.metric("⚠️ 상태", "초과")
                st.error("⚠️ 한도 초과! 다시 생성을 권장합니다.")
            
            # 숫자 잔존 확인
            remaining_numbers = re.findall(r'\d+\s*(?:명|곳|장|편|권|회|개|건|종|차례|번|점포|군데|가지|시간)', result)
            if remaining_numbers:
                st.warning(f"⚠️ 일부 수치 표현이 남아있을 수 있음: {', '.join(remaining_numbers[:5])} - 확인 후 수정해 주세요.")
            else:
                st.info("✅ 구체적 수치 없이 정성적 표현으로 깔끔하게 작성되었습니다!")
                
        except Exception as e:
            box.error(f"오류: {e}")
            st.info("💡 1~2분 후 재시도 또는 새 API 키 발급")

# ===== 푸터(만든이 정보) =====
st.divider()
st.markdown("""
<div style='text-align: center; color: #333333; padding: 20px; font-size: 17px; font-weight: bold;'>
    🏫 학교생활기록부 입력 어시스트 시스템 v3.0<br>
    만든이: 신선여자고등학교 김명남<br>
    🗓️ 2026.03
</div>
""", unsafe_allow_html=True)

