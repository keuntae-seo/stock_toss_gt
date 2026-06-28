import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 기본 세팅 및 타이틀
st.title("✍️ 수기 포트폴리오 관리")
st.write("API 연동을 제외하고 개별 자산을 직접 관리할 수 있는 수기 전용 페이지입니다.")

# ====================================================================
# 📱 모바일 최적화 고정 스타일링 (기존 app.py 스타일 완벽 이식)
# ====================================================================
st.markdown(
    """
<style>
/* 전체 여백 축소 */
.block-container {
    padding-top: 1.0rem !important;
    padding-left: 0.65rem !important;
    padding-right: 0.65rem !important;
    padding-bottom: 2rem !important;
}

/* 제목 크기 조정 */
h1 { font-size: 1.35rem !important; font-weight: 850 !important; }
h2 { font-size: 1.08rem !important; }
h3 { font-size: 0.95rem !important; }

/* metric 카드 모바일 가독성 */
[data-testid="stMetric"] {
    background: rgba(250, 250, 250, 0.75);
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 14px;
    padding: 0.45rem 0.55rem !important;
}
[data-testid="stMetricLabel"] { font-size: 0.74rem !important; }
[data-testid="stMetricValue"] { font-size: 0.98rem !important; }

/* 데이터 편집기 컨테이너 모바일 최적화 */
[data-testid="stDataFrame"] { overflow-x: auto; }

/* 등락 컬러 커스텀 클래스 */
.positive-red { color: #ff4d4f !important; font-weight: 850; }
.negative-blue { color: #4dabf7 !important; font-weight: 850; }
</style>
""",
    unsafe_allow_html=True,
)

# ====================================================================
# 📊 데이터 로직 및 초기화 (세션 상태 유지)
# ====================================================================
if "manual_portfolio_df" not in st.session_state:
    # 기본 예시 데이터셋 구성
    st.session_state["manual_portfolio_df"] = pd.DataFrame(
        [
            {"종목코드": "005930", "종목명": "삼성전자", "시장구분": "국장", "보유수량": 15.0, "매입단가": 74000.0, "현재가": 77500.0},
            {"종목코드": "AAPL", "종목명": "Apple Inc.", "시장구분": "미장", "보유수량": 8.0, "매입단가": 182.0, "현재가": 210.5},
            {"종목코드": "NVDA", "종목명": "NVIDIA", "시장구분": "미장", "보유수량": 5.0, "매입단가": 115.0, "현재가": 124.8},
        ]
    )

# ====================================================================
# 🛠️ 1. 유연한 자산 추가 및 편집 인터페이스 (st.data_editor 활용)
# ====================================================================
st.subheader("📝 내 포트폴리오 실시간 편집")
st.caption("아래 표에서 수량, 매입단가, 현재가를 더블클릭하여 바로 수정할 수 있습니다. 행 추가/삭제도 지원합니다.")

# 동적 편집 활성화
edited_df = st.data_editor(
    st.session_state["manual_portfolio_df"],
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "시장구분": st.column_config.SelectboxColumn("시장구분", options=["국장", "미장", "기타"], required=True),
        "보유수량": st.column_config.NumberColumn("보유수량", min_value=0, format="%.2f"),
        "매입단가": st.column_config.NumberColumn("매입단가", min_value=0, format="%d"),
        "현재가": st.column_config.NumberColumn("현재가", min_value=0, format="%d"),
    }
)
st.session_state["manual_portfolio_df"] = edited_df

# ====================================================================
# 🧮 2. 포트폴리오 평가금액 계산 로직
# ====================================================================
df = edited_df.copy()

if not df.empty and "보유수량" in df.columns and "매입단가" in df.columns:
    # 안전하게 수치 데이터 변환 및 연산
    df["보유수량"] = pd.to_numeric(df["보유수량"]).fillna(0)
    df["매입단가"] = pd.to_numeric(df["매입단가"]).fillna(0)
    df["현재가"] = pd.to_numeric(df["현재가"]).fillna(0)
    
    df["총 매수금액"] = df["보유수량"] * df["매입단가"]
    df["총 평가금액"] = df["보유수량"] * df["현재가"]
    df["평가손익"] = df["총 평가금액"] - df["총 매수금액"]
    df["수익률(%)"] = df.apply(
        lambda r: round((r["평가손익"] / r["총 매수금액"] * 100), 2) if r["총 매수금액"] > 0 else 0.0, 
        axis=1
    )

    # ====================================================================
    # 📌 3. 실시간 총 요약 대시보드 (Metrics 카드)
    # ====================================================================
    total_buy = df["총 매수금액"].sum()
    total_eval = df["총 평가금액"].sum()
    total_pnl = total_eval - total_buy
    total_ratio = (total_pnl / total_buy * 100) if total_buy > 0 else 0.0

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 매수금액", f"{total_buy:,.0f} 원")
    col2.metric("총 평가금액", f"{total_eval:,.0f} 원")
    col3.metric(
        "총 평가손익 (수익률)", 
        f"{total_pnl:,.0f} 원", 
        delta=f"{total_ratio:.2f}%"
    )
    st.markdown("---")

    # ====================================================================
    # 📈 4. 시각화 및 자산 현황 테이블 출력
    # ====================================================================
    col_chart, col_table = st.columns([1, 1.2])

    with col_chart:
        st.subheader("🍕 자산 배분 비중")
        fig = px.pie(
            df, 
            values="총 평가금액", 
            names="종목명", 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("📋 자산 요약 현황")
        # 보기 깔끔하게 포맷팅된 테이블 출력용 DF 정제
        display_df = df[["종목코드", "종목명", "시장구분", "보유수량", "총 매수금액", "총 평가금액", "평가손익", "수익률(%)"]].copy()
        st.dataframe(
            display_df.style.format({
                "보유수량": "{:,.1f}",
                "총 매수금액": "{:,.0f}원",
                "총 평가금액": "{:,.0f}원",
                "평가손익": "{:,.0f}원",
                "수익률(%)": "{:+.2f}%"
            }),
            use_container_width=True
        )

else:
    st.info("💡 위의 편집기 표에 종목 정보를 채워 넣으면 대시보드가 자동으로 구성됩니다.")