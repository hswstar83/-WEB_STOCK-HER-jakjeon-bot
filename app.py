import streamlit as st
import pandas as pd

# 1. 페이지 설정 (제목, 아이콘)
st.set_page_config(page_title="작전주 헌터 대시보드", page_icon="📈")

# 2. 제목과 설명 쓰기
st.title("📈 작전주 헌터 : 세력 포착 시스템")
st.markdown("매일 **오후 3:40**, 세력의 매집 흔적이 있는 종목을 자동으로 찾아냅니다.")

# 3. 가짜 데이터로 표 만들어보기 (테스트용)
st.subheader("🔍 오늘 포착된 종목 (예시)")

data = {
    '탐색일': ['2025-12-09', '2025-12-09'],
    '종목명': ['슈프리마', '진흥기업'],
    '현재가': ['37,950원', '700원'],
    '포착이유': ['재출발(과거 매집봉 2개)', '오늘 거래량 10배 폭발']
}
df = pd.DataFrame(data)

# 4. 화면에 표 그리기
st.dataframe(df, use_container_width=True)

# 5. 마무리 멘트
st.info("현재는 테스트 페이지입니다. 곧 실제 구글 시트 데이터가 연동됩니다!")
