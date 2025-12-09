import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import plotly.graph_objects as go # 👈 강력한 차트 도구 추가

# 1. 페이지 설정
st.set_page_config(
    page_title="작전주 헌터",
    page_icon="🦅",
    layout="centered"
)

# --- 스타일(CSS) ---
st.markdown("""
    <style>
    .main-title { font-size: 1.8rem !important; color: #1E1E1E; text-align: center; font-weight: 800; margin-bottom: 5px; }
    .sub-text { font-size: 0.9rem; color: #555; text-align: center; margin-bottom: 20px; }
    .profit-badge-plus { background-color: #ffebee; color: #d32f2f; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    .profit-badge-minus { background-color: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 함수
@st.cache_data(ttl=60)
def load_data():
    try:
        json_key = os.environ.get('GOOGLE_JSON')
        if not json_key: return None
        creds_dict = json.loads(json_key)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sh = client.open("작전주_포착_로그")
        worksheet = sh.sheet1
        data = worksheet.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        header = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=header)
        return df
    except:
        return pd.DataFrame()

# 3. 미니 차트 데이터 가져오기 (30일치)
@st.cache_data(ttl=3600)
def get_mini_chart_data(code):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=50) # 넉넉히 가져옴
        df = fdr.DataReader(code, start=start_date)
        return df['Close'].tail(30) # 최근 30개만
    except:
        return None

# 4. [NEW] 줌인 차트 그리기 함수 (Plotly 사용)
def plot_sparkline(data, color_hex):
    # 차트 그릴 캔버스 생성
    fig = go.Figure()
    
    # 선 그리기
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data.values, 
        mode='lines', 
        line=dict(color=color_hex, width=2), # 선 두께 조절
        hoverinfo='y' # 마우스 올리면 가격 보임
    ))
    
    # 차트 꾸미기 (핵심: 여백 제거 및 줌인)
    min_val = data.min()
    max_val = data.max()
    padding = (max_val - min_val) * 0.1 # 위아래 10% 여유

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0), # 여백 0 (꽉 차게)
        height=80, # 높이 고정
        paper_bgcolor='rgba(0,0,0,0)', # 배경 투명
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False), # X축(날짜) 숨김
        # 👇 여기가 핵심! (0부터가 아니라 최소값~최대값으로 범위 한정)
        yaxis=dict(visible=False, range=[min_val - padding, max_val + padding]) 
    )
    return fig

def clean_data(df):
    if df.empty: return df
    if '수익률(%)' in df.columns:
        df['수익률_숫자'] = df['수익률(%)'].astype(str).str.replace('%', '').str.replace(',', '')
        df['수익률_숫자'] = pd.to_numeric(df['수익률_숫자'], errors='coerce').fillna(0)
    if '현재가(Live)' in df.columns:
        df['현재가_표시'] = df['현재가(Live)'].astype(str).str.replace('코드확인', '-')
    return df

# --- 메인 화면 ---

st.markdown('<div class="main-title">🦅 작전주 헌터 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">세력의 매집 흔적과 추세를 추적합니다</div>', unsafe_allow_html=True)

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button('🔄 최신 데이터 새로고침', use_container_width=True):
        st.cache_data.clear()

raw_df = load_data()

if raw_df is not None and not raw_df.empty:
    df = clean_data(raw_df)
    if '탐색일' in df.columns:
        df = df.sort_values(by='탐색일', ascending=False)

    total = len(df)
    today_cnt = len(df[df['탐색일'] == df['탐색일'].iloc[0]])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("총 포착", f"{total}건")
    m2.metric("오늘 발견", f"{today_cnt}건")
    m3.metric("업데이트", df['탐색일'].iloc[0][5:])

    st.divider()

    st.subheader("📋 포착 종목 리스트")
    
    for index, row in df.iterrows():
        profit = row['수익률_숫자']
        profit_str = row['수익률(%)']
        price = row['현재가_표시']
        code = row['코드'].replace("'", "")
        
        try:
            price_fmt = f"{int(str(price).replace(',','')): ,}원"
        except:
            price_fmt = price

        badge_class = "profit-badge-plus" if profit >= 0 else "profit-badge-minus"
        
        with st.container(border=True):
            col_info, col_chart = st.columns([1.8, 1.2])
            
            with col_info:
                st.markdown(f"**{row['종목명']}** <span style='color:#888; font-size:0.8em;'>({code})</span> <span class='{badge_class}'>{profit_str}</span>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:5px; font-size:0.95em; font-weight:bold;'>{price_fmt}</div>", unsafe_allow_html=True)
                st.caption(f"{row['탐색일']} 포착 | {row['거래량급증']}")
            
            with col_chart:
                chart_data = get_mini_chart_data(code)
                if chart_data is not None and not chart_data.empty:
                    # 색상 결정
                    color_hex = '#d32f2f' if profit >= 0 else '#1976d2'
                    
                    # [NEW] 줌인 차트 그리기
                    fig = plot_sparkline(chart_data, color_hex)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.caption("차트 로딩 실패")

    with st.expander("📊 전체 데이터 엑셀형태로 보기"):
        st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("데이터를 불러오는 중입니다... (잠시 후 다시 시도해주세요)")
