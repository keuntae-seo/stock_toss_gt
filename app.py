import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import os
import re

try:
    from st_keyup import st_keyup
except Exception:
    st_keyup = None


APP_TITLE = "토스증권 Open API 포트폴리오 대시보드"


# =========================
# Streamlit 설정
# =========================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📈",
    layout="wide",
)

# =========================
# 모바일 친화 UI
# =========================

st.markdown(
    """
<style>
/* 전체 여백 축소 */
.block-container {
    padding-top: 1.0rem;
    padding-left: 1.0rem;
    padding-right: 1.0rem;
    padding-bottom: 2rem;
}

/* 제목 크기 조정 */
h1 {
    font-size: 1.55rem !important;
    line-height: 1.25 !important;
}
h2 {
    font-size: 1.28rem !important;
}
h3 {
    font-size: 1.12rem !important;
}

/* 모바일에서 탭/버튼 터치 영역 확보 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    overflow-x: auto;
    white-space: nowrap;
}
.stTabs [data-baseweb="tab"] {
    min-height: 42px;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
}

.stButton > button {
    min-height: 38px;
    border-radius: 12px;
    font-weight: 700;
}

/* metric 카드 모바일 가독성 */
[data-testid="stMetric"] {
    background: rgba(250, 250, 250, 0.75);
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 14px;
    padding: 0.65rem 0.75rem;
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.05rem;
}

/* dataframe 가로 스크롤 */
[data-testid="stDataFrame"] {
    overflow-x: auto;
}

/* 수기 포트폴리오 카드 */
.mobile-card {
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 16px;
    padding: 0.85rem;
    margin-bottom: 0.75rem;
    background: rgba(250, 250, 250, 0.75);
}
.mobile-card-title {
    font-weight: 800;
    font-size: 1.02rem;
    margin-bottom: 0.15rem;
}
.mobile-card-sub {
    color: rgba(49, 51, 63, 0.68);
    font-size: 0.82rem;
    margin-bottom: 0.55rem;
}
.mobile-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.35rem 0.6rem;
    font-size: 0.88rem;
}
.mobile-label {
    color: rgba(49, 51, 63, 0.62);
    font-size: 0.78rem;
}
.mobile-value {
    font-weight: 700;
}
.mobile-positive {
    color: #e03131;
    font-weight: 800;
}
.mobile-negative {
    color: #1971c2;
    font-weight: 800;
}

/* 작은 화면에서는 사이드바 대신 본문 설정이 더 읽기 쉬움 */
@media (max-width: 760px) {
    .block-container {
        padding-left: 0.65rem;
        padding-right: 0.65rem;
        padding-top: 0.75rem;
    }
    h1 {
        font-size: 1.35rem !important;
    }
    /* column 강제 세로 배치는 검색 결과 한 줄 표시를 깨서 제거 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.45rem;
    }
    .stButton > button {
        width: 100%;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def is_mobile_mode() -> bool:
    return bool(st.session_state.get("mobile_mode", True))



st.markdown(
    """
<style>
/* =========================
   모바일 compact override
   ========================= */
@media (max-width: 760px) {
    .block-container {
        padding-left: 0.45rem !important;
        padding-right: 0.45rem !important;
        padding-top: 0.35rem !important;
        padding-bottom: 1.2rem !important;
    }

    h1, h2, h3 {
        margin-top: 0.25rem !important;
        margin-bottom: 0.35rem !important;
    }

    p {
        margin-bottom: 0.35rem !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 0.35rem !important;
    }

    .stButton > button {
        min-height: 34px !important;
        height: 34px !important;
        padding: 0.15rem 0.45rem !important;
        border-radius: 10px !important;
        font-size: 0.92rem !important;
    }

    [data-testid="stMetric"] {
        padding: 0.45rem 0.55rem !important;
        border-radius: 12px !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.74rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 0.98rem !important;
    }

    .mobile-card {
        padding: 0.62rem 0.7rem !important;
        margin-bottom: 0.45rem !important;
        border-radius: 13px !important;
    }

    .mobile-card-title {
        font-size: 0.98rem !important;
        margin-bottom: 0.05rem !important;
    }

    .mobile-card-sub {
        font-size: 0.76rem !important;
        margin-bottom: 0.25rem !important;
    }

    .mobile-card-grid {
        gap: 0.2rem 0.45rem !important;
        font-size: 0.8rem !important;
    }

    .mobile-label {
        font-size: 0.70rem !important;
    }

    .stNumberInput label {
        font-size: 0.78rem !important;
        margin-bottom: 0.1rem !important;
    }

    .stNumberInput input {
        min-height: 34px !important;
        height: 34px !important;
        padding: 0.15rem 0.45rem !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stExpander"] details summary {
        padding-top: 0.35rem !important;
        padding-bottom: 0.35rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
@media (max-width: 760px) {
    div[data-testid="column"] .stButton > button {
        margin-top: 0.06rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
@media (max-width: 760px) {
    hr {
        margin-top: 0.12rem !important;
        margin-bottom: 0.12rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
@media (max-width: 760px) {
    /* 검색 결과 행을 최대한 촘촘하게 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.25rem !important;
    }

    /* 검색 결과 행은 최대한 낮게 */
    .mobile-search-name {
        padding: 0.22rem 0 0.05rem 0;
        font-weight: 800;
        font-size: 0.92rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .mobile-search-price {
        padding: 0.22rem 0 0.05rem 0;
        font-size: 0.78rem;
        color: #777;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-align: right;
    }

    .mobile-search-divider {
        margin-top: 0.06rem;
        margin-bottom: 0.06rem;
        border-top: 1px solid rgba(49, 51, 63, 0.10);
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
@media (max-width: 760px) {
    .manual-list-row {
        display: grid;
        grid-template-columns: 34px 1fr auto 34px;
        align-items: center;
        gap: 0.45rem;
        padding: 0.48rem 0.1rem;
        border-bottom: 1px solid rgba(49, 51, 63, 0.12);
    }
    .manual-list-name {
        font-weight: 800;
        font-size: 0.95rem;
        line-height: 1.15;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .manual-list-sub {
        color: #8b8f98;
        font-size: 0.72rem;
        margin-top: 0.12rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .manual-list-right {
        text-align: right;
        min-width: 104px;
    }
    .manual-list-amount {
        font-weight: 800;
        font-size: 0.9rem;
        line-height: 1.15;
        white-space: nowrap;
    }
    .manual-list-pnl {
        font-size: 0.72rem;
        margin-top: 0.12rem;
        white-space: nowrap;
    }
    .manual-list-btn .stButton > button {
        min-height: 30px !important;
        height: 30px !important;
        width: 30px !important;
        padding: 0 !important;
        border-radius: 50% !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
    }
    .manual-price-edit {
        margin-left: 2.4rem;
        margin-right: 2.4rem;
        padding-bottom: 0.35rem;
    }
    .manual-price-edit .stNumberInput input {
        height: 30px !important;
        min-height: 30px !important;
        font-size: 0.82rem !important;
    }
    .manual-price-edit .stNumberInput label {
        font-size: 0.72rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
@media (max-width: 760px) {
    /* 수기 포트폴리오 목록의 종목명 버튼을 리스트 텍스트처럼 보이게 */
    button[kind="secondary"] {
        text-align: left !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
@media (max-width: 760px) {
    .block-container {
        padding-left: 0.65rem !important;
        padding-right: 0.65rem !important;
        padding-top: 0.45rem !important;
        max-width: 100% !important;
    }

    h1 {
        font-size: 1.35rem !important;
        margin-bottom: 0.35rem !important;
    }

    h2, h3 {
        font-size: 1.08rem !important;
        margin-top: 0.55rem !important;
        margin-bottom: 0.35rem !important;
    }

    .stButton > button {
        min-height: 34px !important;
        border-radius: 12px !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
    }

    /* 종목 검색 결과 한 줄 */
    .search-row {
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr) 64px;
        align-items: center;
        gap: 0.4rem;
        padding: 0.42rem 0.1rem;
        border-bottom: 1px solid rgba(140, 140, 160, 0.22);
    }
    .search-name {
        font-size: 0.92rem;
        font-weight: 800;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }
    .search-price {
        font-size: 0.78rem;
        color: #8b8f98;
        text-align: right;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }

    /* 수기 포트폴리오 목록 */
    .portfolio-row {
        display: grid;
        grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
        align-items: center;
        padding: 0.55rem 0.05rem;
        border-bottom: 1px solid rgba(140, 140, 160, 0.22);
    }
    .portfolio-name {
        font-size: 0.96rem;
        font-weight: 850;
        line-height: 1.2;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }
    .portfolio-sub {
        font-size: 0.73rem;
        color: #8b8f98;
        margin-top: 0.12rem;
    }
    .portfolio-value {
        text-align: right;
        font-size: 0.93rem;
        font-weight: 850;
        line-height: 1.2;
    }
    .portfolio-pnl {
        text-align: right;
        font-size: 0.73rem;
        margin-top: 0.12rem;
    }

    .detail-card {
        border: 1px solid rgba(140, 140, 160, 0.22);
        border-radius: 16px;
        padding: 0.8rem;
        margin: 0.45rem 0;
        background: rgba(250, 250, 250, 0.06);
    }
    .detail-title {
        font-size: 1.05rem;
        font-weight: 900;
    }
    .detail-sub {
        font-size: 0.76rem;
        color: #8b8f98;
        margin-top: 0.1rem;
    }
    .detail-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem 0.7rem;
        margin-top: 0.65rem;
    }
    .detail-label {
        font-size: 0.72rem;
        color: #8b8f98;
    }
    .detail-value {
        font-size: 0.95rem;
        font-weight: 850;
    }
    .positive-red {
        color: #ff4d4f !important;
        font-weight: 850;
    }
    .negative-blue {
        color: #4dabf7 !important;
        font-weight: 850;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
/* 투자자별 순매수 거래일 number_input UI */
div[data-testid="stNumberInput"] {
    max-width: 100%;
}

@media (max-width: 760px) {
    div[data-testid="stNumberInput"] input {
        height: 38px !important;
        min-height: 38px !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
.investor-inline-title {
    font-size: 1.18rem;
    font-weight: 850;
    line-height: 38px;
    white-space: nowrap;
}

@media (max-width: 760px) {
    .investor-inline-title {
        font-size: 0.94rem !important;
        line-height: 38px !important;
        white-space: nowrap;
    }

    /* 해당 number input이 제목 안에 들어간 것처럼 보이도록 compact */
    div[data-testid="stNumberInput"] input {
        height: 38px !important;
        min-height: 38px !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        text-align: center !important;
        padding-left: 0.35rem !important;
        padding-right: 0.35rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
.portfolio-row-button button {
    min-height: 64px !important;
    height: auto !important;
    padding: 0.55rem 0.8rem !important;
    text-align: left !important;
    border-radius: 14px !important;
    white-space: normal !important;
}

.portfolio-row-html {
    display: grid;
    grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
    align-items: center;
    gap: 0.7rem;
    width: 100%;
}

.portfolio-row-left-title {
    font-size: 1rem;
    font-weight: 900;
    line-height: 1.2;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.portfolio-row-left-sub {
    font-size: 0.78rem;
    color: #8b8f98;
    margin-top: 0.15rem;
}

.portfolio-row-right {
    text-align: right;
}

.portfolio-row-right-main {
    font-size: 0.98rem;
    font-weight: 900;
    line-height: 1.2;
}

.portfolio-row-right-sub {
    font-size: 0.78rem;
    margin-top: 0.15rem;
}

@media (max-width: 760px) {
    .portfolio-row-button button {
        min-height: 58px !important;
        padding: 0.48rem 0.65rem !important;
    }
    .portfolio-row-left-title {
        font-size: 0.94rem !important;
    }
    .portfolio-row-left-sub,
    .portfolio-row-right-sub {
        font-size: 0.72rem !important;
    }
    .portfolio-row-right-main {
        font-size: 0.9rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<style>
.portfolio-card-link {
    display: block;
    text-decoration: none !important;
    color: inherit !important;
    border: 1px solid rgba(140, 140, 160, 0.32);
    border-radius: 16px;
    padding: 0.72rem 0.9rem;
    margin: 0.45rem 0;
    background: rgba(255, 255, 255, 0.035);
    transition: all 0.12s ease-in-out;
}

.portfolio-card-link:hover {
    border-color: rgba(255, 75, 75, 0.75);
    background: rgba(255, 75, 75, 0.055);
}

.portfolio-card-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
    gap: 0.6rem;
    align-items: center;
}

.portfolio-card-name {
    font-size: 1.02rem;
    font-weight: 900;
    line-height: 1.2;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.portfolio-card-qty {
    margin-top: 0.32rem;
    font-size: 0.82rem;
    color: #a0a4ad;
    font-weight: 700;
}

.portfolio-card-value {
    text-align: right;
    font-size: 1rem;
    font-weight: 900;
    line-height: 1.2;
}

.portfolio-card-profit {
    text-align: right;
    margin-top: 0.32rem;
    font-size: 0.82rem;
    font-weight: 850;
}

@media (max-width: 760px) {
    .portfolio-card-link {
        padding: 0.62rem 0.7rem;
        margin: 0.36rem 0;
        border-radius: 14px;
    }
    .portfolio-card-name {
        font-size: 0.95rem;
    }
    .portfolio-card-qty,
    .portfolio-card-profit {
        font-size: 0.74rem;
    }
    .portfolio-card-value {
        font-size: 0.92rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

def signed_class(value: float) -> str:
    try:
        value = float(value)
    except Exception:
        return "detail-value"
    if value > 0:
        return "positive-red"
    if value < 0:
        return "negative-blue"
    return "detail-value"

def get_secret(key: str, default: str = "") -> str:
    """
    Streamlit secrets 우선, 없으면 환경변수 사용.
    secrets.toml이 없거나 key가 없어도 앱이 죽지 않게 처리합니다.
    """
    try:
        value = st.secrets.get(key, None)
        if value is not None:
            return str(value)
    except Exception:
        pass

    return os.getenv(key, default)

def safe_float(x: Any, default: Optional[float] = 0.0) -> Optional[float]:
    try:
        if x is None or x == "":
            return default
        return float(str(x).replace(",", ""))
    except Exception:
        return default


def normalize_symbol(symbol: str) -> str:
    return str(symbol).strip().upper()




def is_kr_symbol(symbol: str) -> bool:
    """
    국장 종목코드 여부 판단.
    예: 005930, 000660, 402340
    """
    symbol = normalize_symbol(symbol)
    return bool(re.fullmatch(r"\d{6}", symbol))


def parse_json_path(obj: Any, path: str, default: Any = None) -> Any:
    if not path:
        return obj

    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except Exception:
                return default
        else:
            return default

        if cur is None:
            return default

    return cur


def format_money_by_currency(amount: Any, currency: str = "KRW") -> str:
    amount = safe_float(amount, None)
    if amount is None:
        return "-"

    currency = str(currency or "KRW").upper()

    if currency == "KRW":
        return f"{amount:,.0f}원"
    if currency == "USD":
        return f"${amount:,.2f}"

    return f"{amount:,.2f} {currency}"


def format_rate_percent(rate: Any) -> str:
    value = safe_float(rate, None)
    if value is None:
        return "-"
    return f"{value:,.2f}%"


def market_label(market_country: Any = None, currency: Any = None, symbol: Any = None) -> str:
    mc = str(market_country or "").upper()
    cur = str(currency or "").upper()
    sym = str(symbol or "").upper()

    if mc == "KR" or cur == "KRW" or sym.isdigit():
        return "국장"
    if mc == "US" or cur == "USD":
        return "미장"
    return "기타"


def today_yyyymmdd() -> str:
    return datetime.now().strftime("%Y%m%d")


def days_ago_yyyymmdd(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")


def clamp_int(value: Any, default: int, min_value: int, max_value: int) -> int:
    try:
        value = int(value)
    except Exception:
        value = default
    return max(min_value, min(max_value, value))



def live_search_input(label: str, placeholder: str, key: str, help: str = "") -> str:
    """
    Streamlit 기본 st.text_input은 Enter/blur 후 rerun되는 경우가 있어
    검색 후보가 타이핑 중 즉시 갱신되지 않을 수 있습니다.

    streamlit-keyup이 설치되어 있으면 keyup마다 값을 Python으로 전달합니다.
    설치되어 있지 않으면 text_input으로 fallback합니다.
    """
    if st_keyup is not None:
        return st_keyup(
            label,
            placeholder=placeholder,
            key=key,
            debounce=250,
        ) or ""

    st.caption("실시간 검색을 쓰려면 `pip install streamlit-keyup`이 필요합니다. 현재는 Enter 후 검색됩니다.")
    return st.text_input(
        label,
        placeholder=placeholder,
        key=key,
        help=help,
    )


# =========================
# 데모 데이터
# =========================

def demo_holdings() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "005930", "name": "삼성전자", "market_country": "KR", "currency": "KRW", "quantity": 20, "avg_price": 72000, "current_price": 83000, "source": "데모"},
            {"symbol": "000660", "name": "SK하이닉스", "market_country": "KR", "currency": "KRW", "quantity": 5, "avg_price": 185000, "current_price": 298000, "source": "데모"},
            {"symbol": "105560", "name": "KB금융", "market_country": "KR", "currency": "KRW", "quantity": 8, "avg_price": 79000, "current_price": 94000, "source": "데모"},
            {"symbol": "AAPL", "name": "Apple Inc.", "market_country": "US", "currency": "USD", "quantity": 4, "avg_price": 180.5, "current_price": 212.3, "source": "데모"},
            {"symbol": "NVDA", "name": "NVIDIA", "market_country": "US", "currency": "USD", "quantity": 3, "avg_price": 121.2, "current_price": 154.8, "source": "데모"},
        ]
    )


def initial_manual_portfolio() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "005930", "name": "삼성전자", "market_label": "국장", "currency": "KRW", "quantity": 0, "avg_price": 80000.0, "current_price": 83000.0},
            {"symbol": "AAPL", "name": "Apple Inc.", "market_label": "미장", "currency": "USD", "quantity": 0, "avg_price": 190.0, "current_price": 212.3},
        ]
    )


def demo_exchange_rate() -> Dict[str, Any]:
    return {
        "baseCurrency": "USD",
        "quoteCurrency": "KRW",
        "rate": "1380.5",
        "midRate": "1375",
        "basisPoint": "40",
        "rateChangeType": "UP",
        "validFrom": datetime.now().isoformat(timespec="seconds"),
    }


def demo_investor_trends(symbols: List[str], days: int = 3) -> pd.DataFrame:
    rows = []
    days = clamp_int(days, 1, 60, 3)
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=days)
    for symbol in symbols:
        for i, d in enumerate(dates):
            rows.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "symbol": symbol,
                    "개인": [1200000000, -850000000, 310000000, 560000000, -210000000][i % 5],
                    "외국인": [-400000000, 1500000000, -220000000, -330000000, 740000000][i % 5],
                    "기관합계": [-800000000, -650000000, -90000000, 120000000, -530000000][i % 5],
                }
            )
    return pd.DataFrame(rows)


def demo_daily_candles(symbols: List[str], days: int) -> pd.DataFrame:
    rows = []
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=max(1, days))
    for idx, symbol in enumerate(symbols):
        base_price = 70000 + idx * 20000 if symbol.isdigit() else 150 + idx * 20
        for i, d in enumerate(dates):
            close = base_price * (1 + 0.006 * i + 0.02 * ((i % 5) - 2))
            rows.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "symbol": symbol,
                    "close": round(close, 2),
                    "currency": "KRW" if symbol.isdigit() else "USD",
                }
            )
    return pd.DataFrame(rows)


# =========================
# 토스증권 Open API Client
# =========================

class TossInvestClient:
    """
    토스증권 OpenAPI 연동.

    사용 API:
    - 토큰: POST /oauth2/token
    - 계좌 목록: GET /api/v1/accounts
    - 보유 주식: GET /api/v1/holdings
    - 보유 주식 조회 시 X-Tossinvest-Account 헤더
    - 현재가 다건 조회: GET /api/v1/prices?symbols=...
    - 원달러 환율: GET /api/v1/exchange-rate?baseCurrency=USD&quoteCurrency=KRW
    - 일봉 캔들: GET /api/v1/candles?symbol=...&interval=1d&count=...
    """

    def __init__(
        self,
        api_key: str = "",
        secret_key: str = "",
        account_seq: str = "",
    ):
        self.base_url = str(get_secret("TOSS_BASE_URL", "https://openapi.tossinvest.com")).rstrip("/")

        self.api_key = api_key.strip()
        self.secret_key = secret_key.strip()
        self.account_seq = str(account_seq or "").strip()

        self.token_path = str(get_secret("TOSS_TOKEN_PATH", "/oauth2/token"))
        self.accounts_path = str(get_secret("TOSS_ACCOUNTS_PATH", "/api/v1/accounts"))
        self.holdings_path = str(get_secret("TOSS_HOLDINGS_PATH", "/api/v1/holdings"))
        self.prices_path = str(get_secret("TOSS_PRICES_PATH", "/api/v1/prices"))
        self.exchange_rate_path = str(get_secret("TOSS_EXCHANGE_RATE_PATH", "/api/v1/exchange-rate"))
        self.candles_path = str(get_secret("TOSS_CANDLES_PATH", "/api/v1/candles"))

        self.accounts_items_path = str(get_secret("TOSS_ACCOUNTS_ITEMS_PATH", "result"))
        self.holdings_items_path = str(get_secret("TOSS_HOLDINGS_ITEMS_PATH", "result.items"))
        self.prices_items_path = str(get_secret("TOSS_PRICES_ITEMS_PATH", "result"))
        self.exchange_rate_result_path = str(get_secret("TOSS_EXCHANGE_RATE_RESULT_PATH", "result"))
        self.candles_items_path = str(get_secret("TOSS_CANDLES_ITEMS_PATH", "result.candles"))

        self.token_access_path = str(get_secret("TOSS_TOKEN_ACCESS_PATH", "access_token"))
        self.token_expires_path = str(get_secret("TOSS_TOKEN_EXPIRES_PATH", "expires_in"))

        self.timeout = int(get_secret("TOSS_TIMEOUT", 10))

        self._access_token = None
        self._expires_at = 0.0
        self.session = requests.Session()

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.secret_key)

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get_access_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 60:
            return self._access_token

        if not self.configured:
            raise RuntimeError("API Key와 Secret Key를 입력하지 않았습니다.")

        url = self._url(self.token_path)

        attempts = [
            {
                "data": {
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.secret_key,
                },
                "auth": None,
            },
            {
                "data": {"grant_type": "client_credentials"},
                "auth": (self.api_key, self.secret_key),
            },
        ]

        last_error = None

        for attempt in attempts:
            try:
                response = self.session.post(
                    url,
                    data=attempt["data"],
                    auth=attempt["auth"],
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                    timeout=self.timeout,
                )

                if response.status_code >= 400:
                    last_error = f"{response.status_code}: {response.text[:1000]}"
                    continue

                data = response.json()
                token = parse_json_path(data, self.token_access_path)
                expires_in = safe_float(parse_json_path(data, self.token_expires_path), 86400)

                if not token:
                    last_error = f"토큰 응답에서 access token을 찾지 못했습니다: {data}"
                    continue

                self._access_token = str(token)
                self._expires_at = time.time() + float(expires_in or 86400)
                return self._access_token

            except Exception as e:
                last_error = str(e)

        raise RuntimeError(f"토큰 발급 실패: {last_error}")

    def _headers(self, include_account: bool = False) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if include_account:
            account_seq = self.resolve_account_seq()
            headers["X-Tossinvest-Account"] = str(account_seq)

        return headers

    def request_json(
        self,
        method: str,
        path: str,
        include_account: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        response = self.session.request(
            method=method.upper(),
            url=self._url(path),
            headers=self._headers(include_account=include_account),
            timeout=self.timeout,
            **kwargs,
        )

        if response.status_code >= 400:
            raise RuntimeError(f"API 오류 {response.status_code}: {response.text[:1200]}")

        try:
            return response.json()
        except Exception:
            raise RuntimeError(f"JSON 응답이 아닙니다: {response.text[:1200]}")

    def get_accounts(self) -> List[Dict[str, Any]]:
        data = self.request_json("GET", self.accounts_path, include_account=False)
        items = parse_json_path(data, self.accounts_items_path, [])
        if isinstance(items, dict):
            return [items]
        if isinstance(items, list):
            return items
        return []

    def resolve_account_seq(self) -> str:
        if self.account_seq and self.account_seq.lower() not in {"auto", "자동"}:
            return self.account_seq

        accounts = self.get_accounts()
        if not accounts:
            raise RuntimeError("조회 가능한 계좌가 없습니다. /api/v1/accounts 응답이 빈 배열입니다.")

        account_seq = accounts[0].get("accountSeq")
        if account_seq is None:
            raise RuntimeError(f"계좌 목록 응답에서 accountSeq를 찾지 못했습니다: {accounts}")

        self.account_seq = str(account_seq)
        return self.account_seq

    def get_holdings_raw(self) -> List[Dict[str, Any]]:
        data = self.request_json("GET", self.holdings_path, include_account=True)
        items = parse_json_path(data, self.holdings_items_path, [])
        if isinstance(items, dict):
            return [items]
        if isinstance(items, list):
            return items
        return []

    def get_exchange_rate(self) -> Dict[str, Any]:
        data = self.request_json(
            "GET",
            self.exchange_rate_path,
            include_account=False,
            params={"baseCurrency": "USD", "quoteCurrency": "KRW"},
        )
        result = parse_json_path(data, self.exchange_rate_result_path, {})
        return result if isinstance(result, dict) else {}

    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        symbols = [normalize_symbol(s) for s in symbols if str(s).strip()]
        if not symbols:
            return {}

        chunks = [symbols[i:i + 200] for i in range(0, len(symbols), 200)]
        result = {}

        for chunk in chunks:
            data = self.request_json(
                "GET",
                self.prices_path,
                include_account=False,
                params={"symbols": ",".join(chunk)},
            )
            items = parse_json_path(data, self.prices_items_path, [])
            if isinstance(items, dict):
                items = [items]

            for item in items or []:
                symbol = normalize_symbol(item.get("symbol", ""))
                price = safe_float(item.get("lastPrice"), None)
                if symbol and price is not None:
                    result[symbol] = price

        return result

    def get_daily_candles_page(
        self,
        symbol: str,
        count: int = 200,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            "symbol": normalize_symbol(symbol),
            "interval": "1d",
            "count": min(max(1, int(count)), 200),
            "adjusted": "true",
        }
        if before:
            params["before"] = before

        return self.request_json(
            "GET",
            self.candles_path,
            include_account=False,
            params=params,
        )

    def get_daily_candles(
        self,
        symbol: str,
        days: int = 20,
        page_size: int = 200,
        max_pages: int = 5,
        sleep_sec: float = 0.15,
    ) -> List[Dict[str, Any]]:
        days = clamp_int(days, 1, 2000, 20)
        needed = days
        before = None
        rows = []

        for _ in range(max_pages):
            data = self.get_daily_candles_page(
                symbol=symbol,
                count=min(page_size, max(1, needed - len(rows))),
                before=before,
            )
            result = parse_json_path(data, "result", {}) or {}
            candles = result.get("candles") or []
            next_before = result.get("nextBefore")

            if not candles:
                break

            rows.extend(candles)

            if len(rows) >= needed:
                break

            if not next_before:
                break

            before = next_before
            time.sleep(sleep_sec)

        return rows[:days]

    def holdings_to_df(self, rows: List[Dict[str, Any]]) -> pd.DataFrame:
        out = []

        for row in rows:
            symbol = normalize_symbol(row.get("symbol", ""))
            name = row.get("name") or symbol
            currency = row.get("currency") or "KRW"
            market_country = row.get("marketCountry") or ""

            quantity = safe_float(row.get("quantity"), 0)
            avg_price = safe_float(row.get("averagePurchasePrice"), 0)
            current_price = safe_float(row.get("lastPrice"), 0)

            market_value = row.get("marketValue") or {}
            profit_loss = row.get("profitLoss") or {}
            daily_profit_loss = row.get("dailyProfitLoss") or {}

            buy_amount = safe_float(market_value.get("purchaseAmount"), None)
            eval_amount = safe_float(market_value.get("amount"), None)
            pl_amount = safe_float(profit_loss.get("amount"), None)
            pl_rate = safe_float(profit_loss.get("rate"), None)
            daily_pl_amount = safe_float(daily_profit_loss.get("amount"), None)
            daily_pl_rate = safe_float(daily_profit_loss.get("rate"), None)

            out.append(
                {
                    "symbol": symbol,
                    "name": str(name),
                    "market_country": market_country,
                    "currency": currency,
                    "quantity": quantity,
                    "avg_price": avg_price,
                    "current_price": current_price,
                    "buy_amount": buy_amount,
                    "eval_amount": eval_amount,
                    "profit_loss": pl_amount,
                    "profit_rate_ratio": pl_rate,
                    "daily_profit_loss": daily_pl_amount,
                    "daily_profit_rate_ratio": daily_pl_rate,
                    "source": "API",
                }
            )

        return pd.DataFrame(out)


# =========================
# 데이터 조회 / 계산
# =========================

def normalize_manual_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(
            columns=["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
        )

    df = df.copy()

    for col in ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]:
        if col not in df.columns:
            df[col] = "" if col in ["symbol", "name", "market_label", "currency"] else 0

    df["symbol"] = df["symbol"].astype(str).map(normalize_symbol)
    df = df[df["symbol"] != ""].copy()
    df["name"] = df["name"].astype(str)
    df["market_label"] = df["market_label"].astype(str).replace("", None)
    df["currency"] = df["currency"].astype(str).replace("", None)

    for idx, row in df.iterrows():
        if pd.isna(row["market_label"]):
            df.at[idx, "market_label"] = market_label(symbol=row["symbol"], currency=row["currency"])
        if pd.isna(row["currency"]):
            df.at[idx, "currency"] = "KRW" if df.at[idx, "market_label"] == "국장" else "USD"

    for col in ["quantity", "avg_price", "current_price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["market_country"] = df["market_label"].map({"국장": "KR", "미장": "US"}).fillna("")
    df["source"] = "수기"

    return df[["symbol", "name", "market_label", "market_country", "currency", "quantity", "avg_price", "current_price", "source"]]


def enrich_holdings(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    required = [
        "symbol",
        "name",
        "market_country",
        "currency",
        "quantity",
        "avg_price",
        "current_price",
        "buy_amount",
        "eval_amount",
        "profit_loss",
        "profit_rate_ratio",
        "daily_profit_loss",
        "daily_profit_rate_ratio",
        "source",
    ]

    for col in required:
        if col not in df.columns:
            if col in ["symbol", "name", "market_country", "currency", "source"]:
                df[col] = ""
            else:
                df[col] = None

    df["symbol"] = df["symbol"].astype(str).map(normalize_symbol)
    df["name"] = df["name"].astype(str)
    df["currency"] = df["currency"].replace("", "KRW").fillna("KRW").astype(str)
    df["market_label"] = df.apply(lambda r: market_label(r.get("market_country"), r.get("currency"), r.get("symbol")), axis=1)

    for col in ["quantity", "avg_price", "current_price", "buy_amount", "eval_amount", "profit_loss", "profit_rate_ratio", "daily_profit_loss", "daily_profit_rate_ratio"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["buy_amount"] = df["buy_amount"].fillna(df["quantity"].fillna(0) * df["avg_price"].fillna(0))
    df["eval_amount"] = df["eval_amount"].fillna(df["quantity"].fillna(0) * df["current_price"].fillna(0))
    df["profit_loss"] = df["profit_loss"].fillna(df["eval_amount"].fillna(0) - df["buy_amount"].fillna(0))

    df["profit_rate"] = df["profit_rate_ratio"] * 100
    missing_rate = df["profit_rate"].isna()
    df.loc[missing_rate, "profit_rate"] = df.loc[missing_rate].apply(
        lambda r: (r["profit_loss"] / r["buy_amount"] * 100) if r["buy_amount"] else 0,
        axis=1,
    )

    df["daily_profit_rate"] = df["daily_profit_rate_ratio"] * 100

    df["weight_in_market"] = 0.0
    for m in df["market_label"].unique():
        mask = df["market_label"] == m
        total = df.loc[mask, "eval_amount"].sum()
        if total:
            df.loc[mask, "weight_in_market"] = df.loc[mask, "eval_amount"] / total * 100

    return df.sort_values(["market_label", "eval_amount"], ascending=[True, False]).reset_index(drop=True)


def merge_portfolios(api_df: pd.DataFrame, manual_df: pd.DataFrame, include_manual: bool) -> pd.DataFrame:
    frames = []

    if api_df is not None and not api_df.empty:
        frames.append(api_df)

    if include_manual:
        manual_norm = normalize_manual_portfolio(manual_df)
        if not manual_norm.empty:
            frames.append(manual_norm)

    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)

    # 같은 source 안에서 같은 종목이 중복되면 마지막 입력 사용
    merged = merged.drop_duplicates(["source", "symbol"], keep="last").reset_index(drop=True)

    return merged


def get_api_holdings(client: TossInvestClient, demo_mode: bool) -> Tuple[pd.DataFrame, Optional[str]]:
    if demo_mode:
        return demo_holdings(), None

    try:
        rows = client.get_holdings_raw()
        df = client.holdings_to_df(rows)

        if not df.empty:
            need_prices = (
                "current_price" not in df.columns
                or df["current_price"].isna().any()
                or (pd.to_numeric(df["current_price"], errors="coerce").fillna(0) == 0).any()
            )

            if need_prices:
                price_map = client.get_prices(df["symbol"].tolist())
                df["current_price"] = df.apply(
                    lambda r: price_map.get(r["symbol"], r.get("current_price")),
                    axis=1,
                )

        return df, None

    except Exception as e:
        return pd.DataFrame(), str(e)


def update_manual_prices_with_api(client: TossInvestClient, manual_df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    manual_norm = normalize_manual_portfolio(manual_df)
    if manual_norm.empty:
        return manual_norm, None

    try:
        price_map = client.get_prices(manual_norm["symbol"].tolist())
        if price_map:
            manual_norm["current_price"] = manual_norm.apply(
                lambda r: price_map.get(r["symbol"], r["current_price"]),
                axis=1,
            )
        return manual_norm, None
    except Exception as e:
        return manual_norm, str(e)


def refresh_manual_current_prices() -> Tuple[pd.DataFrame, Optional[str]]:
    """
    숨겨진 API 키 또는 화면 입력 API 키로 수기 포트폴리오의 현재가를 갱신합니다.
    버튼을 누를 때마다 토스 API를 다시 호출합니다.
    매입가는 사용자의 실제 매입단가이므로 자동 갱신하지 않습니다.
    원달러 환율도 함께 새로 조회해 session_state에 반영합니다.
    """
    client = get_effective_client()
    manual_norm = normalize_manual_portfolio(st.session_state["manual_portfolio"])

    if client is None:
        return manual_norm, "API 키가 없어 실제 현재가/환율을 조회할 수 없습니다."

    updated, err = update_manual_prices_with_api(client, manual_norm)
    st.session_state["manual_portfolio"] = updated[
        ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
    ].copy()

    try:
        fx, fx_err = get_exchange_rate_data(client, demo_mode=False)
        st.session_state["last_exchange_rate"] = fx
        st.session_state["last_exchange_error"] = fx_err
    except Exception as e:
        fx_err = str(e)
        st.session_state["last_exchange_error"] = fx_err

    st.session_state["last_refresh_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if err and st.session_state.get("last_exchange_error"):
        return updated, f"현재가 갱신 오류: {err}\\n환율 갱신 오류: {st.session_state['last_exchange_error']}"
    if err:
        return updated, f"현재가 갱신 오류: {err}"
    if st.session_state.get("last_exchange_error"):
        return updated, f"환율 갱신 오류: {st.session_state['last_exchange_error']}"

    return updated, None


def get_exchange_rate_data(client: Optional[TossInvestClient], demo_mode: bool) -> Tuple[Dict[str, Any], Optional[str]]:
    if demo_mode or client is None:
        return demo_exchange_rate(), None

    try:
        return client.get_exchange_rate(), None
    except Exception as e:
        return {}, str(e)


def get_daily_candles_df(
    client: Optional[TossInvestClient],
    holdings: pd.DataFrame,
    demo_mode: bool,
    chart_days: int,
    max_chart_symbols: int,
    sleep_sec: float = 0.15,
) -> Tuple[pd.DataFrame, Optional[str]]:
    if holdings.empty:
        return pd.DataFrame(), None

    chart_days = clamp_int(chart_days, 1, 2000, 20)
    max_chart_symbols = clamp_int(max_chart_symbols, 1, 50, 10)

    symbols = holdings["symbol"].dropna().astype(str).map(normalize_symbol).unique().tolist()
    symbols = symbols[:max_chart_symbols]

    if demo_mode or client is None:
        return demo_daily_candles(symbols, chart_days), None

    rows = []
    errors = []

    max_pages = (chart_days + 199) // 200 + 1

    for symbol in symbols:
        try:
            candles = client.get_daily_candles(
                symbol=symbol,
                days=chart_days,
                page_size=200,
                max_pages=max_pages,
                sleep_sec=sleep_sec,
            )
            currency = holdings.loc[holdings["symbol"] == symbol, "currency"].iloc[0]

            for c in candles:
                ts = c.get("timestamp")
                rows.append(
                    {
                        "date": str(ts)[:10],
                        "symbol": symbol,
                        "close": safe_float(c.get("closePrice"), None),
                        "currency": c.get("currency") or currency,
                    }
                )

            time.sleep(sleep_sec)

        except Exception as e:
            err = str(e)
            if "rate-limit-exceeded" in err or "429" in err:
                errors.append(f"{symbol}: 요청 한도 초과. 조회 종목 수/기간을 줄이거나 잠시 후 다시 시도하세요.")
            else:
                errors.append(f"{symbol}: {e}")

    df = pd.DataFrame(rows)
    if df.empty:
        return df, "\n".join(errors) if errors else None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values(["symbol", "date"])
    df = df.drop_duplicates(["symbol", "date"], keep="last").reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df, "\n".join(errors) if errors else None


def get_investor_trends_df(holdings: pd.DataFrame, demo_mode: bool, investor_days: int = 3) -> Tuple[pd.DataFrame, Optional[str]]:
    if holdings.empty:
        return pd.DataFrame(), None

    kr_symbols = (
        holdings.loc[holdings["market_label"] == "국장", "symbol"]
        .dropna()
        .astype(str)
        .map(normalize_symbol)
        .unique()
        .tolist()
    )

    if not kr_symbols:
        return pd.DataFrame(), "국장 보유 종목이 없어 투자자별 순매수 데이터를 표시하지 않습니다."

    investor_days = clamp_int(investor_days, 1, 60, 3)

    if demo_mode:
        return demo_investor_trends(kr_symbols, investor_days), None

    try:
        from pykrx import stock
    except Exception:
        return pd.DataFrame(), "pykrx가 설치되어 있지 않습니다. `pip install pykrx` 후 다시 실행하세요."

    # 거래일 기준 n일을 확보하기 위해 달력일은 넉넉히 조회
    start = days_ago_yyyymmdd(max(14, investor_days * 4))
    end = today_yyyymmdd()

    result_frames = []
    errors = []

    for symbol in kr_symbols:
        try:
            df = stock.get_market_trading_value_by_date(start, end, symbol, detail=True)
            if df is None or df.empty:
                continue

            df = df.tail(investor_days).reset_index()
            date_col = df.columns[0]
            df = df.rename(columns={date_col: "date"})
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            df["symbol"] = symbol

            keep_cols = ["date", "symbol"]
            for col in ["개인", "외국인", "기관합계", "금융투자", "보험", "투신", "사모", "은행", "기타금융", "연기금"]:
                if col in df.columns:
                    keep_cols.append(col)

            result_frames.append(df[keep_cols])

        except Exception as e:
            errors.append(f"{symbol}: {e}")

    if not result_frames:
        return pd.DataFrame(), "\n".join(errors) if errors else "투자자별 순매수 데이터가 없습니다."

    out = pd.concat(result_frames, ignore_index=True)
    return out, "\n".join(errors) if errors else None



# =========================
# 종목 검색
# =========================

US_STOCK_MASTER = [
    {"symbol": "AAPL", "name": "Apple Inc.", "market_label": "미장", "currency": "USD"},
    {"symbol": "MSFT", "name": "Microsoft", "market_label": "미장", "currency": "USD"},
    {"symbol": "NVDA", "name": "NVIDIA", "market_label": "미장", "currency": "USD"},
    {"symbol": "GOOGL", "name": "Alphabet Class A", "market_label": "미장", "currency": "USD"},
    {"symbol": "GOOG", "name": "Alphabet Class C", "market_label": "미장", "currency": "USD"},
    {"symbol": "AMZN", "name": "Amazon", "market_label": "미장", "currency": "USD"},
    {"symbol": "META", "name": "Meta Platforms", "market_label": "미장", "currency": "USD"},
    {"symbol": "TSLA", "name": "Tesla", "market_label": "미장", "currency": "USD"},
    {"symbol": "AVGO", "name": "Broadcom", "market_label": "미장", "currency": "USD"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "market_label": "미장", "currency": "USD"},
    {"symbol": "MU", "name": "Micron Technology", "market_label": "미장", "currency": "USD"},
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "market_label": "미장", "currency": "USD"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "market_label": "미장", "currency": "USD"},
    {"symbol": "SOXX", "name": "iShares Semiconductor ETF", "market_label": "미장", "currency": "USD"},
    {"symbol": "SPCX", "name": "SPAC and New Issue ETF", "market_label": "미장", "currency": "USD"},
]


@st.cache_data(ttl=60 * 60 * 24)
def get_kr_stock_master() -> pd.DataFrame:
    """
    pykrx로 국장 종목 마스터를 가져옵니다.
    네트워크/소스 이슈가 있으면 최소 예시 목록으로 fallback합니다.
    """
    try:
        from pykrx import stock

        tickers = stock.get_market_ticker_list(market="ALL")
        rows = []
        for ticker in tickers:
            rows.append(
                {
                    "symbol": ticker,
                    "name": stock.get_market_ticker_name(ticker),
                    "market_label": "국장",
                    "currency": "KRW",
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            return df

    except Exception:
        pass

    return pd.DataFrame(
        [
            {"symbol": "005930", "name": "삼성전자", "market_label": "국장", "currency": "KRW"},
            {"symbol": "005935", "name": "삼성전자우", "market_label": "국장", "currency": "KRW"},
            {"symbol": "009150", "name": "삼성전기", "market_label": "국장", "currency": "KRW"},
            {"symbol": "000810", "name": "삼성화재", "market_label": "국장", "currency": "KRW"},
            {"symbol": "028260", "name": "삼성물산", "market_label": "국장", "currency": "KRW"},
            {"symbol": "032830", "name": "삼성생명", "market_label": "국장", "currency": "KRW"},
            {"symbol": "018260", "name": "삼성에스디에스", "market_label": "국장", "currency": "KRW"},
            {"symbol": "006400", "name": "삼성SDI", "market_label": "국장", "currency": "KRW"},
            {"symbol": "000660", "name": "SK하이닉스", "market_label": "국장", "currency": "KRW"},
            {"symbol": "402340", "name": "SK스퀘어", "market_label": "국장", "currency": "KRW"},
            {"symbol": "034730", "name": "SK", "market_label": "국장", "currency": "KRW"},
            {"symbol": "096770", "name": "SK이노베이션", "market_label": "국장", "currency": "KRW"},
            {"symbol": "011790", "name": "SKC", "market_label": "국장", "currency": "KRW"},
            {"symbol": "017670", "name": "SK텔레콤", "market_label": "국장", "currency": "KRW"},
            {"symbol": "361610", "name": "SK아이이테크놀로지", "market_label": "국장", "currency": "KRW"},
            {"symbol": "285130", "name": "SK케미칼", "market_label": "국장", "currency": "KRW"},
            {"symbol": "003570", "name": "SNT다이내믹스", "market_label": "국장", "currency": "KRW"},
            {"symbol": "035420", "name": "NAVER", "market_label": "국장", "currency": "KRW"},
            {"symbol": "035720", "name": "카카오", "market_label": "국장", "currency": "KRW"},
            {"symbol": "105560", "name": "KB금융", "market_label": "국장", "currency": "KRW"},
            {"symbol": "055550", "name": "신한지주", "market_label": "국장", "currency": "KRW"},
            {"symbol": "086790", "name": "하나금융지주", "market_label": "국장", "currency": "KRW"},
            {"symbol": "316140", "name": "우리금융지주", "market_label": "국장", "currency": "KRW"},
        ]
    )


def search_stock_master(keyword: str, market_scope: str = "전체", limit: int = 30) -> pd.DataFrame:
    keyword = str(keyword or "").strip().upper()
    if not keyword:
        return pd.DataFrame(columns=["symbol", "name", "market_label", "currency"])

    frames = []

    if market_scope in ["전체", "국장"]:
        frames.append(get_kr_stock_master())

    if market_scope in ["전체", "미장"]:
        frames.append(pd.DataFrame(US_STOCK_MASTER))

    if not frames:
        return pd.DataFrame(columns=["symbol", "name", "market_label", "currency"])

    df = pd.concat(frames, ignore_index=True)
    df["symbol"] = df["symbol"].astype(str).map(normalize_symbol)
    df["name"] = df["name"].astype(str)

    keyword_no_space = keyword.replace(" ", "")
    symbol_text = df["symbol"].str.upper()
    name_text = df["name"].str.upper()
    name_no_space = name_text.str.replace(" ", "", regex=False)

    mask = (
        symbol_text.str.contains(keyword, na=False)
        | name_text.str.contains(keyword, na=False)
        | name_no_space.str.contains(keyword_no_space, na=False)
    )

    result = df[mask].copy()

    # 검색 결과 우선순위:
    # 1. 종목코드가 검색어로 시작
    # 2. 종목명이 검색어로 시작
    # 3. 공백 제거 종목명이 검색어로 시작
    # 4. 그 외 포함 검색
    result["rank"] = 9
    result.loc[symbol_text[mask].str.startswith(keyword, na=False), "rank"] = 1
    result.loc[name_text[mask].str.startswith(keyword, na=False), "rank"] = 2
    result.loc[name_no_space[mask].str.startswith(keyword_no_space, na=False), "rank"] = 3
    result["label"] = result["name"] + " (" + result["symbol"] + ", " + result["market_label"] + ")"

    return (
        result.drop_duplicates("symbol")
        .sort_values(["rank", "market_label", "name", "symbol"])
        .head(limit)
        .reset_index(drop=True)
    )



def get_demo_current_price(symbol: str) -> float:
    symbol = normalize_symbol(symbol)
    demo = demo_holdings()
    matched = demo[demo["symbol"].astype(str).map(normalize_symbol) == symbol]
    if not matched.empty:
        return float(matched.iloc[0]["current_price"])

    # 데모 모드 fallback. 실제 가격이 아니라 화면 확인용 기본값입니다.
    if symbol.isdigit():
        return 50000.0
    return 100.0



def get_effective_api_credentials() -> Tuple[str, str, str]:
    """
    우선순위:
    1. .streamlit/secrets.toml 또는 환경변수의 숨겨진 키
    2. 화면에서 직접 입력한 키

    화면에는 숨겨진 키 값을 표시하지 않습니다.
    """
    hidden_api_key = str(get_secret("TOSS_DEFAULT_API_KEY", "") or "").strip()
    hidden_secret_key = str(get_secret("TOSS_DEFAULT_SECRET_KEY", "") or "").strip()

    input_api_key = str(st.session_state.get("input_api_key", "") or "").strip()
    input_secret_key = str(st.session_state.get("input_secret_key", "") or "").strip()
    account_seq = str(st.session_state.get("input_account_seq", "auto") or "auto").strip()

    api_key = hidden_api_key or input_api_key
    secret_key = hidden_secret_key or input_secret_key
    return api_key, secret_key, account_seq


def has_hidden_api_credentials() -> bool:
    return bool(
        str(get_secret("TOSS_DEFAULT_API_KEY", "") or "").strip()
        and str(get_secret("TOSS_DEFAULT_SECRET_KEY", "") or "").strip()
    )


def get_effective_client() -> Optional[TossInvestClient]:
    api_key, secret_key, account_seq = get_effective_api_credentials()
    if not api_key or not secret_key:
        return None
    return TossInvestClient(api_key=api_key, secret_key=secret_key, account_seq=account_seq)



def get_kr_latest_close_prices(symbols: List[str]) -> Dict[str, Optional[float]]:
    """
    토스 API 현재가 조회가 안 될 때, 국장 종목은 pykrx 최근 종가로 보완합니다.
    실시간 현재가는 아니지만 모바일 검색 결과에서 '-'만 뜨는 것을 방지하기 위한 fallback입니다.
    """
    result = {normalize_symbol(s): None for s in symbols}
    kr_symbols = [normalize_symbol(s) for s in symbols if is_kr_symbol(normalize_symbol(s))]

    if not kr_symbols:
        return result

    try:
        from pykrx import stock
    except Exception:
        return result

    # 오늘 포함 최근 14일 중 데이터가 있는 마지막 거래일 종가 사용
    for d in pd.date_range(end=pd.Timestamp.today(), periods=14, freq="D")[::-1]:
        date_str = d.strftime("%Y%m%d")
        try:
            ohlcv = stock.get_market_ohlcv_by_ticker(date_str, market="ALL")
            if ohlcv is None or ohlcv.empty or "종가" not in ohlcv.columns:
                continue

            for symbol in kr_symbols:
                if symbol in ohlcv.index:
                    price = safe_float(ohlcv.loc[symbol, "종가"], None)
                    if price is not None and price > 0:
                        result[symbol] = float(price)

            if any(result.get(s) is not None for s in kr_symbols):
                break

        except Exception:
            continue

    return result



def get_us_latest_prices(symbols: List[str]) -> Dict[str, Optional[float]]:
    """
    Toss API 현재가 조회가 안 될 때, 미장 종목/ETF는 yfinance로 최근 가격을 보완합니다.
    완전한 실시간 시세는 아니며 거래소 정책상 지연 시세일 수 있습니다.
    """
    result = {normalize_symbol(s): None for s in symbols}
    us_symbols = [normalize_symbol(s) for s in symbols if not is_kr_symbol(normalize_symbol(s))]

    if not us_symbols:
        return result

    try:
        import yfinance as yf
    except Exception:
        return result

    for symbol in us_symbols:
        try:
            ticker = yf.Ticker(symbol)
            price = None

            try:
                fast_info = ticker.fast_info
                price = fast_info.get("last_price", None)
            except Exception:
                price = None

            if price is None or safe_float(price, None) is None:
                try:
                    hist = ticker.history(period="1d", interval="1m")
                    if hist is not None and not hist.empty and "Close" in hist.columns:
                        price = hist["Close"].dropna().iloc[-1]
                except Exception:
                    price = None

            if price is None or safe_float(price, None) is None:
                try:
                    hist = ticker.history(period="5d", interval="1d")
                    if hist is not None and not hist.empty and "Close" in hist.columns:
                        price = hist["Close"].dropna().iloc[-1]
                except Exception:
                    price = None

            price = safe_float(price, None)
            if price is not None and price > 0:
                result[symbol] = float(price)

        except Exception:
            continue

    return result


def batch_get_default_prices(symbols: List[str]) -> Dict[str, Optional[float]]:
    """
    검색 결과/수기 추가 시 사용할 기본 현재가 조회.

    1순위: Toss OpenAPI /api/v1/prices
    2순위: 국장 pykrx 최근 종가
    3순위: 미장 yfinance 최근 가격

    Toss API 키가 있으면 Toss 가격이 우선입니다.
    키가 없거나 조회 실패해도 앱이 죽지 않고 fallback 또는 '-'로 표시합니다.
    """
    symbols = [normalize_symbol(s) for s in symbols]
    result: Dict[str, Optional[float]] = {s: None for s in symbols}

    try:
        client = get_effective_client()
        if client is not None and symbols:
            price_map = client.get_prices(symbols)
            for symbol in symbols:
                price = safe_float(price_map.get(symbol), None)
                if price is not None and price > 0:
                    result[symbol] = float(price)
    except Exception:
        pass

    try:
        missing_kr = [s for s, v in result.items() if v is None and is_kr_symbol(s)]
        if missing_kr:
            fallback_kr = get_kr_latest_close_prices(missing_kr)
            for symbol, price in fallback_kr.items():
                if result.get(symbol) is None and price is not None and price > 0:
                    result[symbol] = float(price)
    except Exception:
        pass

    try:
        missing_us = [s for s, v in result.items() if v is None and not is_kr_symbol(s)]
        if missing_us:
            fallback_us = get_us_latest_prices(missing_us)
            for symbol, price in fallback_us.items():
                if result.get(symbol) is None and price is not None and price > 0:
                    result[symbol] = float(price)
    except Exception:
        pass

    return result

def get_default_price_for_manual_stock(symbol: str):
    """
    수기 종목 추가 시 기본 현재가.
    Toss API가 있으면 Toss 현재가를 우선 사용하고,
    실패 시 국장은 pykrx, 미장은 yfinance fallback을 사용합니다.
    """
    symbol = normalize_symbol(symbol)
    try:
        price_map = batch_get_default_prices([symbol])
        price = safe_float(price_map.get(symbol), None)
        if price is not None and price > 0:
            return float(price)
    except Exception:
        pass
    return None

def add_manual_stock_row(stock_row: pd.Series):
    symbol = normalize_symbol(stock_row.get("symbol", ""))
    real_price = get_default_price_for_manual_stock(symbol)
    default_price = float(real_price) if real_price is not None else 0.0

    new_row = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "name": str(stock_row.get("name", "")),
                "market_label": str(stock_row.get("market_label", market_label(symbol=symbol))),
                "currency": str(stock_row.get("currency", "KRW" if symbol.isdigit() else "USD")),
                "quantity": 0.0,
                # 매입가는 최초 기본값만 현재가와 동일하게 넣습니다.
                # 이후 수량을 바꿔도 단가는 바뀌지 않고, 매입금액/평가금액만 바뀌는 게 정상입니다.
                "avg_price": default_price,
                "current_price": default_price,
            }
        ]
    )

    current = normalize_manual_portfolio(st.session_state["manual_portfolio"])[
        ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
    ]

    st.session_state["manual_portfolio"] = (
        pd.concat([current, new_row], ignore_index=True)
        .drop_duplicates("symbol", keep="last")
        .reset_index(drop=True)
    )


# =========================
# 화면 렌더링
# =========================

def render_exchange_rate(exchange_rate: Dict[str, Any], error_message: Optional[str]):
    rate = safe_float(exchange_rate.get("rate"), None)
    mid_rate = safe_float(exchange_rate.get("midRate"), None)
    bp = safe_float(exchange_rate.get("basisPoint"), None)
    change_type = str(exchange_rate.get("rateChangeType", "") or "")
    valid_from = exchange_rate.get("validFrom", "")

    if rate is None:
        st.metric("원달러 환율", "-")
    else:
        delta = None
        if bp is not None:
            delta = f"{bp:,.2f}bp"
            if change_type == "DOWN":
                delta = f"-{abs(bp):,.2f}bp"
            elif change_type == "UP":
                delta = f"+{abs(bp):,.2f}bp"

        st.metric("원달러 환율 USD/KRW", f"{rate:,.2f}원", delta=delta)

    caption_parts = []
    if mid_rate is not None:
        caption_parts.append(f"중간환율 {mid_rate:,.2f}")
    if valid_from:
        caption_parts.append(f"기준시각 {valid_from}")
    if st.session_state.get("last_refresh_time"):
        caption_parts.append(f"마지막 갱신 {st.session_state['last_refresh_time']}")
    if caption_parts:
        st.caption(" · ".join(caption_parts))

    if error_message:
        st.warning(f"환율 조회 실패: {error_message}")


def render_holdings_table(df: pd.DataFrame, title: str):
    st.subheader(title)

    if df is None or df.empty:
        st.info("보유 종목이 없습니다.")
        return

    for i, r in df.reset_index(drop=True).iterrows():
        currency = r.get("currency", "KRW")
        qty = safe_float(r.get("quantity"), 0)
        eval_amount = safe_float(r.get("eval_amount"), 0)
        profit_loss = safe_float(r.get("profit_loss"), 0)
        profit_rate = safe_float(r.get("profit_rate"), 0)
        name = str(r.get("name", ""))
        symbol = str(r.get("symbol", ""))

        portfolio_card_link(
            href=f"?holding_symbol={symbol}",
            name=name,
            value_text=format_money_by_currency(eval_amount, currency),
            qty_text=f"{qty:g}주",
            profit_text=f"{format_money_by_currency(profit_loss, currency)} ({profit_rate:+.1f}%)",
            profit_value=profit_loss,
        )



def render_allocation_charts(df: pd.DataFrame, title_prefix: str):
    st.subheader(f"{title_prefix} 보유 비중")

    if df.empty:
        st.info("보유 종목이 없습니다.")
        return

    chart_df = df[df["eval_amount"] > 0].copy()
    if chart_df.empty:
        st.info("평가금액이 없어 보유 비중 차트를 표시할 수 없습니다.")
        return

    chart_df["종목"] = chart_df["name"] + " (" + chart_df["symbol"] + ")"

    chart_left, chart_right = st.columns([1.2, 1])

    with chart_left:
        # 원파이보다 상호작용이 좋은 treemap
        path_cols = ["market_label", "종목"] if "종합" in title_prefix else ["종목"]
        fig_tree = px.treemap(
            chart_df,
            path=path_cols,
            values="eval_amount",
            color="profit_rate",
            hover_data={
                "symbol": True,
                "currency": True,
                "eval_amount": ":,.2f",
                "profit_rate": ":.2f",
            },
            title=f"{title_prefix} 인터랙티브 트리맵",
        )
        fig_tree.update_traces(textinfo="label+percent parent+value")
        st.plotly_chart(fig_tree, use_container_width=True)

    with chart_right:
        fig_bar = px.bar(
            chart_df.sort_values("eval_amount", ascending=True),
            x="eval_amount",
            y="종목",
            orientation="h",
            color="profit_rate",
            title=f"{title_prefix} 평가금액 순위",
            labels={"eval_amount": "평가금액", "종목": "종목", "profit_rate": "수익률(%)"},
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def render_market_section(holdings: pd.DataFrame, market_name: str):
    market_df = holdings[holdings["market_label"] == market_name].copy()

    st.markdown(f"### {market_name}")

    if market_df.empty:
        st.info(f"{market_name} 보유 종목이 없습니다.")
        return

    currency = market_df["currency"].iloc[0]
    total_eval = market_df["eval_amount"].sum()
    total_pl = market_df["profit_loss"].sum()
    total_buy = market_df["buy_amount"].sum()
    total_rate = total_pl / total_buy * 100 if total_buy else 0

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{market_name} 평가금액", format_money_by_currency(total_eval, currency))
    c2.metric(f"{market_name} 평가손익", format_money_by_currency(total_pl, currency), delta=format_money_by_currency(total_pl, currency))
    c3.metric(f"{market_name} 수익률", format_rate_percent(total_rate), delta=format_rate_percent(total_rate))

    render_holdings_table(market_df, f"{market_name} 보유 종목")
    render_allocation_charts(market_df, market_name)








def get_query_param_value(key: str) -> Optional[str]:
    try:
        value = st.query_params.get(key, None)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        return None


def clear_query_params_safe():
    try:
        st.query_params.clear()
    except Exception:
        pass


def portfolio_card_link(
    href: str,
    name: str,
    value_text: str,
    qty_text: str,
    profit_text: str,
    profit_value: float = 0.0,
):
    profit_cls = signed_class(profit_value)
    st.markdown(
        f"""
<a class="portfolio-card-link" href="{href}">
  <div class="portfolio-card-grid">
    <div>
      <div class="portfolio-card-name">{name}</div>
      <div class="portfolio-card-qty">{qty_text}</div>
    </div>
    <div>
      <div class="portfolio-card-value">{value_text}</div>
      <div class="portfolio-card-profit {profit_cls}">{profit_text}</div>
    </div>
  </div>
</a>
""",
        unsafe_allow_html=True,
    )


def price_step_by_currency(currency: str) -> float:
    """단가 조정 단위. 국장/KRW는 100원, 미장/USD는 1달러 단위."""
    return 100.0 if str(currency or "KRW").upper() == "KRW" else 1.0


def sync_manual_df(df: pd.DataFrame):
    st.session_state["manual_portfolio"] = normalize_manual_portfolio(df)[
        ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
    ].copy()


def render_manual_detail_page(quick_df: pd.DataFrame, selected_symbol: str, section_key: str):
    """카드 클릭 후 보이는 상세 화면. 수량/평균 매매가/현재가를 여기서만 수정합니다."""
    selected_symbol = normalize_symbol(selected_symbol)
    match = quick_df[quick_df["symbol"].astype(str).map(normalize_symbol) == selected_symbol]

    if match.empty:
        st.session_state["selected_manual_symbol"] = None
        clear_query_params_safe()
        st.warning("선택한 종목을 찾을 수 없습니다.")
        st.rerun()

    i = match.index[0]
    row = quick_df.loc[i]

    symbol = str(row["symbol"])
    name = str(row["name"])
    currency = str(row["currency"])
    market = str(row.get("market_label", market_label(symbol=symbol, currency=currency)))
    qty = safe_float(row.get("quantity"), 0)
    avg_price = safe_float(row.get("avg_price"), 0)
    current_price = safe_float(row.get("current_price"), 0)
    buy_amount = qty * avg_price
    eval_amount = qty * current_price
    profit = eval_amount - buy_amount
    profit_rate = (profit / buy_amount * 100) if buy_amount else 0
    step_price = price_step_by_currency(currency)

    back_col, title_col = st.columns([0.55, 3.45], gap="small")
    with back_col:
        if st.button("‹", key=f"{section_key}_manual_back_{symbol}", use_container_width=True):
            st.session_state["selected_manual_symbol"] = None
            clear_query_params_safe()
            st.rerun()
    with title_col:
        st.markdown(f"### {name}")
        st.caption(f"{market} · {symbol}")

    st.markdown(
        f"""
<div class="detail-card">
  <div class="detail-title">{name}</div>
  <div class="detail-sub">{qty:g}주 · {symbol}</div>
  <div class="detail-grid">
    <div>
      <div class="detail-label">평가금액</div>
      <div class="detail-value">{format_money_by_currency(eval_amount, currency)}</div>
    </div>
    <div>
      <div class="detail-label">평가손익</div>
      <div class="detail-value {signed_class(profit)}">{format_money_by_currency(profit, currency)} ({profit_rate:+.1f}%)</div>
    </div>
    <div>
      <div class="detail-label">평균 매매가</div>
      <div class="detail-value">{format_money_by_currency(avg_price, currency)}</div>
    </div>
    <div>
      <div class="detail-label">현재가</div>
      <div class="detail-value">{format_money_by_currency(current_price, currency)}</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.caption("수량은 +/-로 조정하고, 평균 매매가와 현재가는 아래 입력칸에서 수정합니다.")

    minus_col, qty_col, plus_col = st.columns([0.8, 2.4, 0.8], gap="small")
    with minus_col:
        if st.button("－", key=f"{section_key}_detail_qty_minus_{symbol}", use_container_width=True):
            quick_df.loc[i, "quantity"] = max(0, qty - 1)
            sync_manual_df(quick_df)
            st.rerun()
    with qty_col:
        st.markdown(
            f"""
<div style="text-align:center;font-weight:900;padding-top:0.45rem;">
  보유 수량 {qty:g}주
</div>
""",
            unsafe_allow_html=True,
        )
    with plus_col:
        if st.button("＋", key=f"{section_key}_detail_qty_plus_{symbol}", use_container_width=True):
            quick_df.loc[i, "quantity"] = qty + 1
            sync_manual_df(quick_df)
            st.rerun()

    p1, p2 = st.columns(2, gap="small")
    new_avg = p1.number_input(
        "평균 매매가",
        min_value=0.0,
        value=float(avg_price),
        step=float(step_price),
        key=f"{section_key}_detail_avg_price_{symbol}",
    )
    new_current = p2.number_input(
        "현재가",
        min_value=0.0,
        value=float(current_price),
        step=float(step_price),
        key=f"{section_key}_detail_current_price_{symbol}",
    )

    if new_avg != avg_price or new_current != current_price:
        quick_df.loc[i, "avg_price"] = new_avg
        quick_df.loc[i, "current_price"] = new_current
        sync_manual_df(quick_df)
        st.rerun()


def render_manual_portfolio_controls(section_key: str = "total"):
    """
    수기 포트폴리오 관리 UI.
    목록은 보유 종목 카드 형태로 표시하고, 카드를 누르면 상세 화면에서 수량/단가를 수정합니다.
    """
    st.subheader("수기 포트폴리오")

    try:
        quick_df = normalize_manual_portfolio(st.session_state.get("manual_portfolio", pd.DataFrame()))[
            ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
        ].reset_index(drop=True)
    except Exception:
        quick_df = pd.DataFrame(columns=["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"])

    selected_symbol = get_query_param_value("manual_symbol") or st.session_state.get("selected_manual_symbol")
    if selected_symbol:
        st.session_state["selected_manual_symbol"] = normalize_symbol(selected_symbol)
        render_manual_detail_page(quick_df, selected_symbol, section_key)
    else:
        st.caption("카드를 누르면 상세페이지에서 수량, 평균 매매가, 현재가를 조정할 수 있습니다.")

        if quick_df.empty:
            st.info("수기 포트폴리오에 등록된 종목이 없습니다. 종목을 검색해서 추가하세요.")
        else:
            for i, row in quick_df.iterrows():
                symbol = str(row["symbol"])
                currency = str(row["currency"])
                qty = safe_float(row["quantity"], 0)
                avg_price = safe_float(row["avg_price"], 0)
                current_price = safe_float(row["current_price"], 0)

                buy_amount = qty * avg_price
                eval_amount = qty * current_price
                profit = eval_amount - buy_amount
                profit_rate = (profit / buy_amount * 100) if buy_amount else 0

                portfolio_card_link(
                    href=f"?manual_symbol={symbol}",
                    name=str(row["name"]),
                    value_text=format_money_by_currency(eval_amount, currency),
                    qty_text=f"{qty:g}주",
                    profit_text=f"{format_money_by_currency(profit, currency)} ({profit_rate:+.1f}%)",
                    profit_value=profit,
                )

    col_refresh, col_save, col_reset = st.columns([1.4, 0.9, 1.6])
    with col_refresh:
        if st.button("현재가/환율 실제값 갱신", key=f"{section_key}_refresh_manual", use_container_width=True):
            updated_manual, refresh_error = refresh_manual_current_prices()
            if refresh_error:
                st.warning(refresh_error)
            else:
                st.success("현재가와 원달러 환율 갱신 완료")
            st.rerun()

    with col_save:
        if st.button("수기 저장", key=f"{section_key}_save_manual", use_container_width=True):
            try:
                sync_manual_df(st.session_state["manual_portfolio"])
            except Exception:
                pass
            st.success("수기 포트폴리오 저장 완료")
            st.rerun()

    with col_reset:
        if st.button("수기 포트폴리오 초기화", key=f"{section_key}_reset_manual", use_container_width=True):
            st.session_state["manual_portfolio"] = initial_manual_portfolio()
            st.session_state["selected_manual_symbol"] = None
            clear_query_params_safe()
            st.success("초기화 완료")
            st.rerun()


def render_manual_portfolio_in_total_tab(exchange_rate):
    """
    종합 탭의 기존 '종합 보유 종목' 자리에
    수기 포트폴리오 목록을 표시합니다.
    """
    render_manual_portfolio_controls(section_key="total_tab")

def normalize_exchange_rate_value(exchange_rate, default: float = 1350.0) -> float:
    """
    exchange_rate가 float/int 또는 dict 형태로 들어와도 숫자 환율만 뽑아냅니다.
    예:
    - 1350.5
    - {"rate": 1350.5}
    - {"exchange_rate": 1350.5}
    - {"result": {"rate": 1350.5}}
    """
    if isinstance(exchange_rate, dict):
        candidate_keys = [
            "rate",
            "exchange_rate",
            "exchangeRate",
            "basePrice",
            "price",
            "value",
            "usd_krw",
            "USDKRW",
        ]

        for key in candidate_keys:
            value = exchange_rate.get(key)
            parsed = safe_float(value, None)
            if parsed is not None and parsed > 0:
                return float(parsed)

        result = exchange_rate.get("result")
        if isinstance(result, dict):
            for key in candidate_keys:
                value = result.get(key)
                parsed = safe_float(value, None)
                if parsed is not None and parsed > 0:
                    return float(parsed)

    parsed = safe_float(exchange_rate, None)
    if parsed is not None and parsed > 0:
        return float(parsed)

    return float(default)


def render_total_section(holdings: pd.DataFrame, exchange_rate):
    """
    종합 탭.
    상단의 총 평가금액 요약은 유지하고,
    기존 '종합 보유 종목' 영역은 수기 포트폴리오 내용으로 대체합니다.
    """
    st.subheader("종합")

    fx_rate = normalize_exchange_rate_value(exchange_rate)

    if holdings is None or holdings.empty:
        st.info("보유 종목 데이터가 없습니다.")
        render_manual_portfolio_in_total_tab(fx_rate)
        return

    df = holdings.copy()

    if "eval_amount" not in df.columns:
        df["eval_amount"] = 0

    if "currency" not in df.columns:
        df["currency"] = "KRW"

    if "market_label" not in df.columns:
        df["market_label"] = df["currency"].map(lambda x: "미장" if x == "USD" else "국장")

    df["eval_amount"] = pd.to_numeric(df["eval_amount"], errors="coerce").fillna(0)

    if "eval_amount_krw" not in df.columns:
        df["eval_amount_krw"] = df.apply(
            lambda r: safe_float(r.get("eval_amount"), 0) * (fx_rate if r.get("currency") == "USD" else 1),
            axis=1,
        )
    else:
        df["eval_amount_krw"] = pd.to_numeric(df["eval_amount_krw"], errors="coerce").fillna(0)

    kr_total = safe_float(df.loc[df["market_label"] == "국장", "eval_amount"].sum(), 0)
    us_total = safe_float(df.loc[df["market_label"] == "미장", "eval_amount"].sum(), 0)
    total_krw = safe_float(df["eval_amount_krw"].sum(), 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("국장 평가금액", format_money_by_currency(kr_total, "KRW"))
    c2.metric("미장 평가금액", format_money_by_currency(us_total, "USD"))
    c3.metric("종합 원화환산", format_money_by_currency(total_krw, "KRW"))

    # 기존 '종합 보유 종목' 자리를 수기 포트폴리오 내용으로 완전 대체
    render_manual_portfolio_in_total_tab(fx_rate)



def render_daily_candles(candles_df: pd.DataFrame, holdings: pd.DataFrame, chart_days: int, error_message: Optional[str]):
    st.divider()
    st.subheader(f"최근 {chart_days}일 일자별 종가 선 그래프")

    if error_message:
        st.warning(f"일부 종목 일봉 조회 실패:\n{error_message}")

    if candles_df.empty:
        st.info("일자별 종가 차트 데이터가 없습니다.")
        return

    st.caption(f"현재 차트 포인트 수: {len(candles_df):,}개")

    name_map = holdings.set_index("symbol")["name"].to_dict()
    market_map = holdings.set_index("symbol")["market_label"].to_dict()
    candles_df = candles_df.copy()
    candles_df["name"] = candles_df["symbol"].map(name_map).fillna(candles_df["symbol"])
    candles_df["market_label"] = candles_df["symbol"].map(market_map).fillna("기타")
    candles_df["종목"] = candles_df["name"] + " (" + candles_df["symbol"] + ")"

    kr_df = candles_df[candles_df["market_label"] == "국장"].copy()
    us_df = candles_df[candles_df["market_label"] == "미장"].copy()

    tab_kr, tab_us = st.tabs(["국장 일봉", "미장 일봉"])

    with tab_kr:
        if kr_df.empty:
            st.info("국장 일봉 데이터가 없습니다.")
        else:
            fig = px.line(
                kr_df,
                x="date",
                y="close",
                color="종목",
                markers=True,
                title=f"국장 보유 종목 최근 {chart_days}일 종가",
                labels={"date": "날짜", "close": "종가"},
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab_us:
        if us_df.empty:
            st.info("미장 일봉 데이터가 없습니다.")
        else:
            fig = px.line(
                us_df,
                x="date",
                y="close",
                color="종목",
                markers=True,
                title=f"미장 보유 종목 최근 {chart_days}일 종가",
                labels={"date": "날짜", "close": "종가"},
            )
            st.plotly_chart(fig, use_container_width=True)






def get_investor_days_value(default: int = 3) -> int:
    value = st.session_state.get("investor_days", default)
    value = clamp_int(value, 1, 60, default)
    st.session_state["investor_days"] = value
    return value


def set_investor_days_value(value: int):
    value = clamp_int(value, 1, 60, 3)
    st.session_state["investor_days"] = value
    # 기간 변경 시 상세 화면은 목록으로 돌려 혼동 방지
    st.session_state["selected_investor_symbol"] = None


def force_last_n_rows_by_symbol(df: pd.DataFrame, n_days: int) -> pd.DataFrame:
    """
    화면 표시 직전 최종 안전장치.
    df에 종목별 60행/수개월치가 있어도 symbol별 최근 n_days개만 반환합니다.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    n_days = int(max(1, min(60, int(n_days))))
    out = df.copy()

    if "symbol" not in out.columns or "date" not in out.columns:
        return out.head(n_days)

    out["_date_sort"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["_date_sort"])

    if out.empty:
        return out.drop(columns=["_date_sort"], errors="ignore")

    out = out.sort_values(["symbol", "_date_sort"])
    out = out.groupby("symbol", group_keys=False).tail(n_days)
    out = out.sort_values(["symbol", "_date_sort"]).reset_index(drop=True)
    out["date"] = out["_date_sort"].dt.strftime("%Y-%m-%d")
    return out.drop(columns=["_date_sort"], errors="ignore")


def filter_investor_df_last_n_trading_days(investor_df: pd.DataFrame, n_days: int) -> pd.DataFrame:
    return force_last_n_rows_by_symbol(investor_df, n_days)

def render_investor_trends(investor_df: pd.DataFrame, error_message: Optional[str], holdings: Optional[pd.DataFrame] = None, investor_days: int = 3):
    if "investor_days" not in st.session_state:
        st.session_state["investor_days"] = 3

    st.divider()

    # 숫자 입력을 session_state와 직접 연결
    current_days = int(max(1, min(60, int(st.session_state.get("investor_days", 3)))))

    # 제목과 거래일 입력을 한 줄로 표시
    title_left, days_input_col, title_right = st.columns([1.35, 0.9, 1.65], gap="small")

    with title_left:
        st.markdown(
            """
<div class="investor-inline-title">국장 보유 종목 최근</div>
""",
            unsafe_allow_html=True,
        )

    with days_input_col:
        if "investor_days_input_hard" not in st.session_state:
            st.session_state["investor_days_input_hard"] = current_days

        input_days = st.number_input(
            "조회 거래일 수",
            min_value=1,
            max_value=60,
            step=1,
            key="investor_days_input_hard",
            label_visibility="collapsed",
        )

    with title_right:
        st.markdown(
            """
<div class="investor-inline-title">거래일 투자자별 순매수</div>
""",
            unsafe_allow_html=True,
        )

    if int(input_days) != int(st.session_state.get("investor_days", 3)):
        st.session_state["investor_days"] = int(input_days)
        st.session_state["selected_investor_symbol"] = None
        st.rerun()

    effective_days = int(st.session_state["investor_days"])

    st.caption(f"현재 설정: 최근 {effective_days}거래일만 표시")

    if error_message:
        st.warning(error_message)

    # 원본이 60일이어도 display source를 여기서 강제로 N개로 자름
    df = force_last_n_rows_by_symbol(investor_df, effective_days)

    if df.empty:
        st.info("투자자별 순매수 데이터가 없습니다.")
        return

    name_map = {}
    if holdings is not None and not holdings.empty:
        name_map = holdings.drop_duplicates("symbol").set_index("symbol")["name"].to_dict()

    df = df.copy()
    df["종목명"] = df["symbol"].map(name_map).fillna(df["symbol"])
    df = force_last_n_rows_by_symbol(df, effective_days)

    value_cols = [c for c in df.columns if c not in ["date", "symbol", "종목명"]]

    def color_signed(value):
        try:
            numeric = float(value)
        except Exception:
            return ""
        if numeric > 0:
            return "color: #ff4b4b; font-weight: 800;"
        if numeric < 0:
            return "color: #4b8bff; font-weight: 800;"
        return ""

    def fmt_money(value):
        try:
            return f"{float(value):,.0f}"
        except Exception:
            return value

    selected_symbol = st.session_state.get("selected_investor_symbol")

    # 상세 화면
    if selected_symbol:
        detail_df = df[df["symbol"] == selected_symbol].copy()
        detail_df = force_last_n_rows_by_symbol(detail_df, effective_days)

        if detail_df.empty:
            st.session_state["selected_investor_symbol"] = None
            st.rerun()

        stock_name = detail_df["종목명"].iloc[0]

        back_col, title_col = st.columns([0.65, 3.35], gap="small")
        with back_col:
            if st.button("‹", key=f"investor_back_{selected_symbol}", use_container_width=True):
                st.session_state["selected_investor_symbol"] = None
                st.rerun()
        with title_col:
            st.markdown(f"### {stock_name}")
            st.caption(f"{selected_symbol} · 최근 {effective_days}거래일 상세")

        display = detail_df[["date"] + value_cols].copy()
        display = display.rename(columns={"date": "날짜"})

        styled = (
            display.style
            .format({col: fmt_money for col in value_cols})
            .map(color_signed, subset=value_cols)
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        chart_cols = [c for c in ["개인", "외국인", "기관합계"] if c in detail_df.columns]
        if chart_cols:
            melted = detail_df.melt(
                id_vars=["date"],
                value_vars=chart_cols,
                var_name="투자자",
                value_name="순매수금액",
            )
            fig = px.bar(
                melted,
                x="date",
                y="순매수금액",
                color="투자자",
                barmode="group",
                title=f"{stock_name} 최근 {effective_days}거래일 투자자별 순매수",
                labels={"date": "날짜", "순매수금액": "순매수금액(원)"},
            )
            fig.update_layout(
                height=360 if is_mobile_mode() else 460,
                margin=dict(l=10, r=10, t=55, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        if st.button("목록으로 돌아가기", key=f"investor_done_{selected_symbol}", use_container_width=True):
            st.session_state["selected_investor_symbol"] = None
            st.rerun()

        return

    # 목록 화면
    for symbol in df["symbol"].drop_duplicates().tolist():
        g = df[df["symbol"] == symbol].copy()
        g = force_last_n_rows_by_symbol(g, effective_days)

        if g.empty:
            continue

        stock_name = g["종목명"].iloc[0]

        name_col, count_col = st.columns([2.7, 1.1], gap="small")
        with name_col:
            if st.button(stock_name, key=f"open_investor_detail_{symbol}_{effective_days}", use_container_width=True):
                st.session_state["selected_investor_symbol"] = symbol
                st.rerun()
        with count_col:
            st.caption(f"{len(g)} / {effective_days}거래일")

        display = g[["date"] + value_cols].copy()
        display = display.rename(columns={"date": "날짜"})

        # 여기가 핵심: st.dataframe에는 이미 N개로 잘린 display만 들어감
        styled = (
            display.style
            .format({col: fmt_money for col in value_cols})
            .map(color_signed, subset=value_cols)
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

    st.caption("양수는 빨간색, 음수는 파란색입니다. 그래프는 종목명을 누르면 상세 화면에서 볼 수 있습니다.")




def get_manual_holdings_for_display() -> pd.DataFrame:
    """
    종합 탭에서 보여줄 수기 포트폴리오 전용 보유 종목 데이터.
    API 보유 종목과 합치지 않고, 사용자가 입력한 수기 포트폴리오만 표시합니다.
    """
    try:
        manual_df = normalize_manual_portfolio(st.session_state.get("manual_portfolio", pd.DataFrame()))
        if manual_df.empty:
            return pd.DataFrame()
        return enrich_holdings(manual_df)
    except Exception:
        return pd.DataFrame()


def render_dashboard(
    holdings: pd.DataFrame,
    exchange_rate: Dict[str, Any],
    exchange_error: Optional[str],
    daily_candles_df: pd.DataFrame,
    daily_candles_error: Optional[str],
    investor_df: pd.DataFrame,
    investor_error: Optional[str],
    chart_days: int,
    demo_mode: bool,
    error_message: Optional[str] = None,
):
    top_left, top_right = st.columns([1, 3])
    with top_left:
        render_exchange_rate(exchange_rate, exchange_error)
    with top_right:
        if demo_mode:
            st.info("현재 데모 모드입니다. API Key와 Secret Key를 입력하고 [입력한 API 키로 조회] 버튼을 누르면 본인 계좌 기준으로 조회됩니다.")

    if error_message:
        st.error("토스 API 조회 실패")
        st.code(error_message)
        st.warning("공식 문서 기준 endpoint를 반영했습니다. 그래도 실패하면 API 권한, 계좌 순번, 계좌 보유 여부를 확인하세요.")

    if holdings.empty:
        st.warning("보유 종목 데이터가 없습니다.")
    else:
        tab_total, tab_kr, tab_us = st.tabs(["종합", "국장 보유종목", "미장 보유종목"])

        with tab_total:
            render_total_section(holdings, exchange_rate)

        with tab_kr:
            render_market_section(holdings, "국장")

        with tab_us:
            render_market_section(holdings, "미장")

        st.subheader("CSV 다운로드")
        csv = holdings.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "보유종목 CSV 다운로드",
            data=csv.encode("utf-8-sig"),
            file_name="portfolio_holdings.csv",
            mime="text/csv",
            use_container_width=True,
        )

    investor_days_value = int(st.session_state.get("investor_days", 3))
    investor_df = force_last_n_rows_by_symbol(investor_df, int(st.session_state.get("investor_days", 3)))
    render_investor_trends(investor_df, investor_error, holdings=holdings, investor_days=investor_days_value)
    render_daily_candles(daily_candles_df, holdings, chart_days, daily_candles_error)


# =========================
# Session state
# =========================

if "manual_portfolio" not in st.session_state:
    st.session_state["manual_portfolio"] = initial_manual_portfolio()

if "stock_search_results" not in st.session_state:
    st.session_state["stock_search_results"] = pd.DataFrame(columns=["symbol", "name", "market_label", "currency", "label"])

if "include_manual_portfolio" not in st.session_state:
    st.session_state["include_manual_portfolio"] = True

if "mobile_mode" not in st.session_state:
    st.session_state["mobile_mode"] = True

if "selected_manual_symbol" not in st.session_state:
    st.session_state["selected_manual_symbol"] = None

if "selected_investor_symbol" not in st.session_state:
    st.session_state["selected_investor_symbol"] = None

if "input_api_key" not in st.session_state:
    st.session_state["input_api_key"] = str(get_secret("TOSS_DEFAULT_API_KEY", ""))

if "input_secret_key" not in st.session_state:
    st.session_state["input_secret_key"] = str(get_secret("TOSS_DEFAULT_SECRET_KEY", ""))

if "input_account_seq" not in st.session_state:
    st.session_state["input_account_seq"] = "auto"

if "has_clicked_query" not in st.session_state:
    st.session_state["has_clicked_query"] = False

if "chart_days" not in st.session_state:
    st.session_state["chart_days"] = 20

if "max_chart_symbols" not in st.session_state:
    st.session_state["max_chart_symbols"] = 10

if "last_holdings" not in st.session_state:
    st.session_state["last_holdings"] = enrich_holdings(demo_holdings())

if "last_api_holdings" not in st.session_state:
    st.session_state["last_api_holdings"] = pd.DataFrame()

if "last_demo_mode" not in st.session_state:
    st.session_state["last_demo_mode"] = True

if "last_error_message" not in st.session_state:
    st.session_state["last_error_message"] = None

if "last_exchange_rate" not in st.session_state:
    st.session_state["last_exchange_rate"] = demo_exchange_rate()

if "last_exchange_error" not in st.session_state:
    st.session_state["last_exchange_error"] = None

if "last_daily_candles_df" not in st.session_state:
    st.session_state["last_daily_candles_df"] = demo_daily_candles(st.session_state["last_holdings"]["symbol"].tolist(), 20)

if "last_daily_candles_error" not in st.session_state:
    st.session_state["last_daily_candles_error"] = None

if "last_investor_df" not in st.session_state:
    st.session_state["last_investor_df"] = demo_investor_trends(
        st.session_state["last_holdings"].loc[st.session_state["last_holdings"]["market_label"] == "국장", "symbol"].tolist(),
        st.session_state.get("investor_days", 3),
    )

if "last_investor_error" not in st.session_state:
    st.session_state["last_investor_error"] = None

if "investor_days_initialized" not in st.session_state:
    st.session_state["investor_days"] = 3
    st.session_state["investor_days_initialized"] = True
elif "investor_days" not in st.session_state:
    st.session_state["investor_days"] = 3

if "last_refresh_time" not in st.session_state:
    st.session_state["last_refresh_time"] = ""


# =========================
# Sidebar
# =========================

st.title("📱 내 포트폴리오")

with st.sidebar:
    st.header("화면 설정")
    st.session_state["mobile_mode"] = st.toggle(
        "모바일 보기",
        value=bool(st.session_state.get("mobile_mode", True)),
        help="모바일에서는 표보다 카드형 화면을 우선 표시합니다.",
    )
    st.divider()

    st.header("API 설정")

    hidden_ready = has_hidden_api_credentials()

    if hidden_ready:
        st.success("숨겨진 Toss API 키 사용 중")
        st.caption("`.streamlit/secrets.toml`의 키를 사용합니다. 화면에는 키가 표시되지 않습니다.")
    else:
        st.info("숨겨진 API 키가 없습니다. 필요하면 아래 고급 설정에서 직접 입력하세요.")

    with st.expander("고급: 직접 API 키 입력", expanded=False):
        input_api_key = st.text_input(
            "Toss API Key / Client ID",
            type="password",
            value=st.session_state["input_api_key"],
            placeholder="본인 Client ID 입력",
            help="입력값은 파일/DB에 저장하지 않고 현재 브라우저 세션에서만 사용합니다.",
        )

        input_secret_key = st.text_input(
            "Toss Secret Key / Client Secret",
            type="password",
            value=st.session_state["input_secret_key"],
            placeholder="본인 Client Secret 입력",
            help="입력값은 파일/DB에 저장하지 않고 현재 브라우저 세션에서만 사용합니다.",
        )

        input_account_seq = st.text_input(
            "계좌 순번",
            value=st.session_state["input_account_seq"],
            help="auto로 두면 /api/v1/accounts의 첫 번째 accountSeq를 자동 사용합니다.",
        )

        st.session_state["input_api_key"] = input_api_key
        st.session_state["input_secret_key"] = input_secret_key
        st.session_state["input_account_seq"] = input_account_seq

    effective_api_key, effective_secret_key, _ = get_effective_api_credentials()
    api_ready = bool(effective_api_key and effective_secret_key)

    if api_ready:
        st.success("실제 현재가/환율/API 조회 가능")
    else:
        st.info("API 키가 없어도 수기 포트폴리오나 데모 데이터로 조회할 수 있습니다.")

    st.divider()

    st.subheader("차트 설정")
    chart_days = st.number_input(
        "일봉 차트 조회 일수",
        min_value=1,
        max_value=2000,
        value=int(st.session_state["chart_days"]),
        step=1,
        help="예: 20, 120 등 원하는 일수를 입력하세요.",
    )

    max_chart_symbols = st.number_input(
        "차트 조회 종목 수 제한",
        min_value=1,
        max_value=50,
        value=int(st.session_state["max_chart_symbols"]),
        step=1,
        help="보유 종목이 많으면 차트가 무거워질 수 있어 제한합니다.",
    )

    st.session_state["chart_days"] = int(chart_days)
    st.session_state["max_chart_symbols"] = int(max_chart_symbols)

    # 투자자별 순매수 거래일 수는 해당 섹션 안의 +/- 버튼으로만 조정합니다.



    include_manual = st.toggle(
        "수기 포트폴리오 포함",
        value=bool(st.session_state["include_manual_portfolio"]),
        help="직접 입력한 종목/수량/매입가를 함께 포트폴리오에 반영합니다.",
    )
    st.session_state["include_manual_portfolio"] = include_manual

    auto_update_manual_price = st.toggle(
        "수기 종목 현재가 API로 보완",
        value=False,
        disabled=not api_ready,
        help="API 키가 있을 때 직접 입력한 종목의 현재가를 토스 현재가 API로 덮어씁니다.",
    )

    st.divider()

    col_query, col_manual, col_demo = st.columns(3)

    with col_query:
        query_clicked = st.button(
            "API 조회",
            use_container_width=True,
            disabled=not api_ready,
        )

    with col_manual:
        manual_clicked = st.button(
            "수기만 보기",
            use_container_width=True,
        )

    with col_demo:
        demo_clicked = st.button(
            "데모 보기",
            use_container_width=True,
        )

    if query_clicked:
        st.session_state["has_clicked_query"] = True

        effective_api_key, effective_secret_key, effective_account_seq = get_effective_api_credentials()
        client = TossInvestClient(
            api_key=effective_api_key,
            secret_key=effective_secret_key,
            account_seq=effective_account_seq,
        )

        with st.spinner("토스 API로 계좌/환율/차트 정보를 조회하는 중입니다..."):
            api_holdings_raw, error_message = get_api_holdings(client, demo_mode=False)
            st.session_state["last_api_holdings"] = api_holdings_raw

            manual_df = st.session_state["manual_portfolio"]
            manual_error = None
            if include_manual and auto_update_manual_price:
                manual_df, manual_error = update_manual_prices_with_api(client, manual_df)
                st.session_state["manual_portfolio"] = manual_df[["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]].copy()

            combined_raw = merge_portfolios(api_holdings_raw, st.session_state["manual_portfolio"], include_manual)
            holdings = enrich_holdings(combined_raw)

            exchange_rate, exchange_error = get_exchange_rate_data(client, demo_mode=False)
            daily_df, daily_error = get_daily_candles_df(
                client,
                holdings,
                demo_mode=False,
                chart_days=st.session_state["chart_days"],
                max_chart_symbols=st.session_state["max_chart_symbols"],
                sleep_sec=0.15,
            )
            investor_df, investor_error = get_investor_trends_df(
                holdings,
                demo_mode=False,
                investor_days=st.session_state.get("investor_days", 3),
            )

            if manual_error:
                if daily_error:
                    daily_error += f"\n수기 종목 현재가 보완 실패: {manual_error}"
                else:
                    daily_error = f"수기 종목 현재가 보완 실패: {manual_error}"

            st.session_state["last_holdings"] = holdings
            st.session_state["last_demo_mode"] = False
            st.session_state["last_error_message"] = error_message
            st.session_state["last_exchange_rate"] = exchange_rate
            st.session_state["last_exchange_error"] = exchange_error
            st.session_state["last_daily_candles_df"] = daily_df
            st.session_state["last_daily_candles_error"] = daily_error
            st.session_state["last_investor_df"] = investor_df
            st.session_state["last_investor_error"] = investor_error

    if manual_clicked:
        st.session_state["has_clicked_query"] = True

        manual_raw = normalize_manual_portfolio(st.session_state["manual_portfolio"])
        holdings = enrich_holdings(manual_raw)

        st.session_state["last_api_holdings"] = pd.DataFrame()
        st.session_state["last_holdings"] = holdings
        st.session_state["last_demo_mode"] = True
        st.session_state["last_error_message"] = None
        st.session_state["last_exchange_rate"] = demo_exchange_rate()
        st.session_state["last_exchange_error"] = None
        st.session_state["last_daily_candles_df"] = demo_daily_candles(holdings["symbol"].tolist(), st.session_state["chart_days"])
        st.session_state["last_daily_candles_error"] = "수기만 보기에서는 실제 일봉 API를 호출하지 않고 데모 차트를 표시합니다. 실제 차트가 필요하면 API 키로 조회하세요."
        st.session_state["last_investor_df"] = demo_investor_trends(
            holdings.loc[holdings["market_label"] == "국장", "symbol"].tolist(),
            st.session_state.get("investor_days", 3),
        )
        st.session_state["last_investor_error"] = None

    if demo_clicked:
        st.session_state["has_clicked_query"] = True
        holdings = enrich_holdings(demo_holdings())

        st.session_state["last_api_holdings"] = pd.DataFrame()
        st.session_state["last_holdings"] = holdings
        st.session_state["last_demo_mode"] = True
        st.session_state["last_error_message"] = None
        st.session_state["last_exchange_rate"] = demo_exchange_rate()
        st.session_state["last_exchange_error"] = None
        st.session_state["last_daily_candles_df"] = demo_daily_candles(holdings["symbol"].tolist(), st.session_state["chart_days"])
        st.session_state["last_daily_candles_error"] = None
        st.session_state["last_investor_df"] = demo_investor_trends(
            holdings.loc[holdings["market_label"] == "국장", "symbol"].tolist(),
            st.session_state.get("investor_days", 3),
        )
        st.session_state["last_investor_error"] = None

    if not st.session_state["has_clicked_query"]:
        st.caption("키 입력/수기 입력 후 버튼을 눌러야 조회가 실행됩니다.")
    elif st.session_state["last_demo_mode"]:
        st.info("현재 결과는 데모 또는 수기 기반 데이터입니다.")
    else:
        st.success("마지막 조회 결과: 입력한 API 키 기준")


# =========================
# 수기 포트폴리오 입력
# =========================

st.subheader("수기 포트폴리오 입력")

st.caption("종목 검색으로 추가한 뒤 아래 수량 +/- 표에서 수량을 조정합니다. 현재가/환율은 버튼으로 실제값 갱신할 수 있습니다.")

with st.expander("종목명/종목코드 검색해서 추가", expanded=True):
    # [추가] 버튼을 누른 뒤에는 검색창을 빈 값으로 초기화합니다.
    # 위젯 생성 이후 session_state 값을 직접 바꾸면 Streamlit 오류가 날 수 있어
    # 버튼 클릭 시 플래그만 세우고, 다음 rerun에서 위젯 생성 전에 초기화합니다.
    if st.session_state.pop("clear_stock_search_keyword_live", False):
        st.session_state["stock_search_keyword_live"] = ""

    stock_keyword = live_search_input(
        "검색어",
        placeholder="예: 삼, 삼성, S, SK, SK스, AAPL",
        key="stock_search_keyword_live",
        help="입력하는 도중에 아래 후보 종목 리스트가 갱신됩니다.",
    )

    # 시장 선택 탭/필터 제거: 전체 시장에서 자동 검색
    search_results = search_stock_master(
        stock_keyword,
        "전체",
        limit=30,
    )

    st.session_state["stock_search_results"] = search_results

    if not stock_keyword.strip():
        st.info("검색어를 입력하는 도중에 후보 종목이 아래 리스트로 표시됩니다. 예: `삼` → 삼성전자/삼성전기/삼성화재, `SK스` → SK스퀘어.")
    elif search_results.empty:
        st.warning("검색 결과가 없습니다. 종목명 또는 종목코드를 다시 입력해보세요.")
    else:
        st.caption(f"검색 결과 {len(search_results):,}개 · 원하는 종목의 [추가] 버튼을 누르세요.")

        price_map = batch_get_default_prices(search_results["symbol"].tolist())

        if is_mobile_mode():
            for i, row in search_results.iterrows():
                symbol = row["symbol"]
                name = row["name"]
                currency = row["currency"]
                default_price = price_map.get(symbol)

                c1, c2 = st.columns([3.4, 0.75], gap="small")
                with c1:
                    st.markdown(
                        f"""
<div class="search-row" style="border-bottom:0;">
  <div class="search-name">{name}</div>
  <div class="search-price">현재가 {format_money_by_currency(default_price, currency)}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                with c2:
                    if st.button("추가", key=f"add_stock_mobile_{symbol}_{i}", use_container_width=True):
                        add_manual_stock_row(row)
                        st.session_state["clear_stock_search_keyword_live"] = True
                        st.success(f"{name} 추가 완료")
                        st.rerun()
                st.markdown('<div style="border-bottom:1px solid rgba(140,140,160,0.22); margin:0.08rem 0;"></div>', unsafe_allow_html=True)
        else:
            header_cols = st.columns([1.1, 2.5, 0.8, 1.2, 0.8])
            header_cols[0].markdown("**종목코드**")
            header_cols[1].markdown("**종목명**")
            header_cols[2].markdown("**통화**")
            header_cols[3].markdown("**현재가/기본가**")
            header_cols[4].markdown("**추가**")

            for i, row in search_results.iterrows():
                symbol = row["symbol"]
                name = row["name"]
                currency = row["currency"]
                default_price = price_map.get(symbol)

                row_cols = st.columns([1.1, 2.5, 0.8, 1.2, 0.8])
                row_cols[0].write(symbol)
                row_cols[1].write(name)
                row_cols[2].write(currency)
                row_cols[3].write(format_money_by_currency(default_price, currency))

                if row_cols[4].button("추가", key=f"add_stock_{symbol}_{i}", use_container_width=True):
                    add_manual_stock_row(row)
                    st.session_state["clear_stock_search_keyword_live"] = True
                    st.success(f"{name} ({symbol}) 추가 완료")
                    st.rerun()

        st.caption("추가 시 API 키가 있으면 실제 현재가가 현재가/매입가 기본값으로 들어갑니다. API 키가 없거나 조회 실패 시 0으로 들어가며 직접 수정할 수 있습니다.")

# 수기 포트폴리오는 종합 탭 안에서만 표시/수정합니다.
# 여기서는 데이터 정규화와 데모/수기 화면의 계산값 동기화만 수행합니다.
normalized_manual_editor = normalize_manual_portfolio(st.session_state["manual_portfolio"])[
    ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
]
st.session_state["manual_portfolio"] = normalized_manual_editor.copy()

# 현재 화면이 수기/데모 기반이면, 아래 대시보드 계산값이 즉시 바뀌게 반영
if st.session_state.get("last_demo_mode", True):
    manual_holdings_live = enrich_holdings(normalized_manual_editor)
    if not manual_holdings_live.empty:
        st.session_state["last_holdings"] = manual_holdings_live

# =========================
# 메인 화면
# =========================

if not st.session_state["has_clicked_query"]:
    st.info("왼쪽 사이드바에서 API 조회, 수기만 보기, 데모 보기 중 하나를 선택하세요.")

render_dashboard(
    holdings=st.session_state["last_holdings"],
    exchange_rate=st.session_state["last_exchange_rate"],
    exchange_error=st.session_state["last_exchange_error"],
    daily_candles_df=st.session_state["last_daily_candles_df"],
    daily_candles_error=st.session_state["last_daily_candles_error"],
    investor_df=st.session_state["last_investor_df"],
    investor_error=st.session_state["last_investor_error"],
    chart_days=st.session_state["chart_days"],
    demo_mode=st.session_state["last_demo_mode"],
    error_message=st.session_state["last_error_message"],
)


# =========================
# 배포/설정 안내
# =========================

with st.expander("배포용 설정 안내"):
    st.markdown(
        """
### 이 버전의 구조

- API 계좌 조회와 수기 포트폴리오 입력을 모두 지원합니다.
- API 키가 없어도 수량/매입가/현재가를 직접 입력해 포트폴리오를 구성할 수 있습니다.
- 일봉 차트 조회 일수는 사용자가 직접 입력합니다. 예: 20일, 120일.
- PER 낮은 순 TOP 5는 제거했습니다.
- 입력값은 파일이나 DB에 저장하지 않고 현재 브라우저 세션에서만 사용합니다.

### 토스증권 OpenAPI 공식 경로

```toml
TOSS_BASE_URL = "https://openapi.tossinvest.com"
TOSS_TOKEN_PATH = "/oauth2/token"
TOSS_ACCOUNTS_PATH = "/api/v1/accounts"
TOSS_HOLDINGS_PATH = "/api/v1/holdings"
TOSS_PRICES_PATH = "/api/v1/prices"
TOSS_EXCHANGE_RATE_PATH = "/api/v1/exchange-rate"
TOSS_CANDLES_PATH = "/api/v1/candles"

TOSS_ACCOUNTS_ITEMS_PATH = "result"
TOSS_HOLDINGS_ITEMS_PATH = "result.items"
TOSS_PRICES_ITEMS_PATH = "result"
TOSS_EXCHANGE_RATE_RESULT_PATH = "result"
TOSS_CANDLES_ITEMS_PATH = "result.candles"

TOSS_TOKEN_ACCESS_PATH = "access_token"
TOSS_TOKEN_EXPIRES_PATH = "expires_in"
TOSS_TIMEOUT = 10
```

### 로컬 개발용 기본 API Key

```toml
TOSS_DEFAULT_API_KEY = "새로_재발급받은_API_KEY"
TOSS_DEFAULT_SECRET_KEY = "새로_재발급받은_SECRET_KEY"
```
        """
    )
