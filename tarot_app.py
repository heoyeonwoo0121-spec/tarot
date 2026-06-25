import streamlit as st
import json
import random
import os
from deep_translator import GoogleTranslator

# [초기 설정]
st.set_page_config(page_title="운명의 타로 상담소", layout="wide")
translator = GoogleTranslator(source='en', target='ko')

BASE_DIR = r"D:\tarot"
JSON_PATH = os.path.join(BASE_DIR, "tarot-images.json")
TXT_PATH = os.path.join(BASE_DIR, "tarot_data.txt")
BACK_IMAGE = os.path.join(BASE_DIR, "back_tarot_image.png")

@st.cache_data
def load_data():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['cards']

# [텍스트 파일 해석 데이터 로드 함수 - 파일명 분리 로직 적용]
@st.cache_data
def load_txt_interpretations(file_path):
    interpretations = {}
    if not os.path.exists(file_path):
        return interpretations
    
    current_card = None
    # utf-8-sig를 사용하여 윈도우 메모장 BOM 문제 해결
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 1. 괄호로 시작하고 끝나는 줄 찾기
            if line.startswith('[') and line.endswith(']'):
                raw_name = line[1:-1].strip() # 예: 'w14.jpg_King of Wands'
                
                # 2. 언더바(_)가 있다면 언더바 뒤의 카드 이름만 추출하여 소문자로 저장
                if '_' in raw_name:
                    card_name = raw_name.split('_', 1)[-1].strip().lower()
                else:
                    card_name = raw_name.lower()
                
                current_card = card_name
                interpretations[current_card] = {}
                
            # 카테고리별 해석 인식
            elif current_card and ':' in line:
                cat, text = line.split(':', 1)
                interpretations[current_card][cat.strip()] = text.strip()
                
    return interpretations

tarot_data = load_data()
txt_interpretations = load_txt_interpretations(TXT_PATH)

# 세션 초기화
if 'deck' not in st.session_state:
    indices = list(range(len(tarot_data)))
    random.shuffle(indices)
    st.session_state.deck = indices
if 'picked' not in st.session_state:
    st.session_state.picked = []

st.title("🔮 직접 뽑는 타로 상담소")

with st.sidebar:
    st.header("상담 설정")
    user_question = st.text_input("고민을 입력하세요.", value="")
    category = st.selectbox("운세 카테고리", ["종합운", "연애운", "진로/직업", "금전운", "학업운", "건강운", "인간관계운"])

st.markdown(f"### 📋 상담 주제: [{category}]")
st.subheader(f"🃏 카드 선택: {len(st.session_state.picked)} / 3")

# [카드 배치]
if len(st.session_state.picked) < 3:
    chunk_size = 10 
    for i in range(0, len(st.session_state.deck), chunk_size):
        cols = st.columns(chunk_size)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(st.session_state.deck):
                card_idx = st.session_state.deck[idx]
                with col:
                    if os.path.exists(BACK_IMAGE):
                        st.image(BACK_IMAGE, use_container_width=True)
                        if st.button(f"선택 {idx}", key=f"btn_{idx}"):
                            st.session_state.picked.append(card_idx)
                            st.rerun()

# [결과 출력]
else:
    st.balloons()
    st.divider()
    
    cols = st.columns(3)
    labels = ["🕰️ 과거", "🎯 현재", "🚀 미래"]
    
    for i, idx in enumerate(st.session_state.picked):
        with cols[i]:
            card = tarot_data[idx]
            card_name = card['name']
            st.markdown(f"#### {labels[i]}: {card_name}")
            
            img_path = os.path.join(BASE_DIR, card['img'])
            if os.path.exists(img_path): 
                st.image(img_path, use_container_width=True)
            
            st.write(f"📖 **{category} 상세 해석:**")
            
            # 카드 이름을 소문자로 변환하여 매칭 (매칭률을 높이기 위함)
            card_name_lower = card_name.lower()
            interpretation_text = txt_interpretations.get(card_name_lower, {}).get(category, None)
            
            if interpretation_text:
                # 사용자가 텍스트 파일에 작성한 해석 내용 출력
                st.info(interpretation_text)
            else:
                # 텍스트 파일에 내용이 누락되었을 경우를 대비한 자동 번역 기본 로직
                with st.spinner('해석을 준비하는 중입니다...'):
                    try:
                        base_meaning = translator.translate(card['meanings']['light'][0])
                        kw1 = translator.translate(card['keywords'][0])
                        kw2 = translator.translate(card['keywords'][1])
                        
                        question_text = user_question if user_question else "현재 상황"
                        
                        st.warning(f"'{card_name}' 카드는 {category}에서 중요한 메시지를 던지고 있습니다. "
                                   f"이 카드는 주로 '{base_meaning}'을(를) 상징하며, 당신의 고민인 '{question_text}'과(와) 맞물려 새로운 국면을 예고합니다. "
                                   f"이 기운을 {category}에 대입해보면, 무작정 앞으로 나아가기보다 내면의 '{kw1}'와(과) '{kw2}'을(를) 먼저 점검할 시기입니다. "
                                   f"과거의 경험이 현재의 상황에 밑거름이 되어, 미래에는 긍정적인 방향으로 나아갈 수 있습니다.")
                    except Exception as e:
                        st.error("해석을 가져오는 데 문제가 발생했습니다.")

    if st.button("🔄 다시 뽑기"):
        st.session_state.picked = []
        random.shuffle(st.session_state.deck)
        st.rerun()