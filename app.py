import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

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
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
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

def signed_class(value: float) -> str:
    try:
        value = float(value)
    except Exception:
        return "mobile-value"
    if value > 0:
        return "mobile-positive"
    if value < 0:
        return "mobile-negative"
    return "mobile-value"


# 일부 session_state 값은 아래 초기화 블록보다 먼저 참조될 수 있어
# 앱 시작 직후 안전하게 기본값을 보장합니다.
st.session_state.setdefault("investor_days", 3)
st.session_state.setdefault("last_refresh_time", "")


# =========================
# 공통 유틸
# =========================

def get_secret(key: str, default: Any = None) -> Any:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    import os
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
            {"symbol": "005930", "name": "삼성전자", "market_label": "국장", "currency": "KRW", "quantity": 1, "avg_price": 80000.0, "current_price": 83000.0},
            {"symbol": "AAPL", "name": "Apple Inc.", "market_label": "미장", "currency": "USD", "quantity": 1, "avg_price": 190.0, "current_price": 212.3},
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


def batch_get_default_prices(symbols: List[str]) -> Dict[str, Optional[float]]:
    """
    검색 결과 리스트 표시용 현재가 일괄 조회.
    숨겨진 API 키 또는 화면 입력 API 키가 있으면 토스 현재가 API를 사용합니다.
    없거나 실패하면 None을 반환해 화면에 '-'로 표시합니다.
    """
    symbols = [normalize_symbol(s) for s in symbols if str(s).strip()]
    result = {symbol: None for symbol in symbols}

    client = get_effective_client()
    if client is not None and symbols:
        try:
            price_map = client.get_prices(symbols)
            for symbol in symbols:
                price = safe_float(price_map.get(symbol), None)
                if price is not None and price > 0:
                    result[symbol] = float(price)
        except Exception:
            pass

    return result



def get_default_price_for_manual_stock(symbol: str):
    """
    토스 현재가 API에서 실제 현재가를 가져옵니다.
    숨겨진 API 키 또는 화면 입력 API 키가 없거나 조회 실패하면 None을 반환합니다.
    """
    symbol = normalize_symbol(symbol)
    client = get_effective_client()

    if client is None:
        return None

    try:
        price_map = client.get_prices([symbol])
        price = safe_float(price_map.get(symbol), None)

        if price is not None and price > 0:
            return float(price)

    except Exception:
        return None

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

    if df.empty:
        st.info("보유 종목이 없습니다.")
        return

    if is_mobile_mode():
        for _, r in df.iterrows():
            currency = r.get("currency", "KRW")
            profit_loss = safe_float(r.get("profit_loss"), 0)
            profit_rate = safe_float(r.get("profit_rate"), 0)

            st.markdown(
                f"""
<div class="mobile-card">
  <div class="mobile-card-title">{r.get('name', '')}</div>
  <div class="mobile-card-sub">{r.get('symbol', '')} · {safe_float(r.get('quantity'), 0):g}주 · {currency}</div>
  <div class="mobile-card-grid">
    <div><div class="mobile-label">현재가</div><div class="mobile-value">{format_money_by_currency(r.get('current_price'), currency)}</div></div>
    <div><div class="mobile-label">평가금액</div><div class="mobile-value">{format_money_by_currency(r.get('eval_amount'), currency)}</div></div>
    <div><div class="mobile-label">평가손익</div><div class="{signed_class(profit_loss)}">{format_money_by_currency(profit_loss, currency)}</div></div>
    <div><div class="mobile-label">수익률</div><div class="{signed_class(profit_rate)}">{format_rate_percent(profit_rate)}</div></div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        return

        return

    display = df.copy()
    display["평균단가"] = display.apply(lambda r: format_money_by_currency(r["avg_price"], r["currency"]), axis=1)
    display["현재가"] = display.apply(lambda r: format_money_by_currency(r["current_price"], r["currency"]), axis=1)
    display["매입금액"] = display.apply(lambda r: format_money_by_currency(r["buy_amount"], r["currency"]), axis=1)
    display["평가금액"] = display.apply(lambda r: format_money_by_currency(r["eval_amount"], r["currency"]), axis=1)
    display["평가손익"] = display.apply(lambda r: format_money_by_currency(r["profit_loss"], r["currency"]), axis=1)
    display["수익률"] = display["profit_rate"].map(lambda x: format_rate_percent(x))
    display["당일손익"] = display.apply(lambda r: format_money_by_currency(r["daily_profit_loss"], r["currency"]), axis=1)
    display["당일수익률"] = display["daily_profit_rate"].map(lambda x: format_rate_percent(x))
    display["비중"] = display["weight_in_market"].map(lambda x: format_rate_percent(x))

    st.dataframe(
        display[
            [
                "source",
                "symbol",
                "name",
                "currency",
                "quantity",
                "평균단가",
                "현재가",
                "매입금액",
                "평가금액",
                "평가손익",
                "수익률",
                "당일손익",
                "당일수익률",
                "비중",
            ]
        ].rename(
            columns={
                "source": "구분",
                "symbol": "종목코드",
                "name": "종목명",
                "currency": "통화",
                "quantity": "수량",
            }
        ),
        use_container_width=True,
        hide_index=True,
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


def render_total_section(holdings: pd.DataFrame, exchange_rate: Dict[str, Any]):
    st.markdown("### 종합")

    if holdings.empty:
        st.info("보유 종목이 없습니다.")
        return

    usdkrw = safe_float(exchange_rate.get("rate"), None)
    total_df = holdings.copy()

    # 종합 탭은 원화 환산 평가금액도 함께 계산
    def to_krw(row):
        amount = safe_float(row.get("eval_amount"), 0)
        currency = str(row.get("currency", "KRW")).upper()
        if currency == "USD" and usdkrw:
            return amount * usdkrw
        return amount

    total_df["eval_amount_krw"] = total_df.apply(to_krw, axis=1)

    kr_eval = total_df.loc[total_df["currency"].str.upper() == "KRW", "eval_amount"].sum()
    usd_eval = total_df.loc[total_df["currency"].str.upper() == "USD", "eval_amount"].sum()
    total_krw = total_df["eval_amount_krw"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("국장 평가금액", format_money_by_currency(kr_eval, "KRW"))
    c2.metric("미장 평가금액", format_money_by_currency(usd_eval, "USD"))
    c3.metric("종합 원화환산", format_money_by_currency(total_krw, "KRW"))

    render_holdings_table(total_df, "종합 보유 종목")

    # 종합 차트는 원화환산 평가금액 기준으로 시각화
    chart_df = total_df.copy()
    chart_df["eval_amount"] = chart_df["eval_amount_krw"]
    chart_df["currency"] = "KRW"
    render_allocation_charts(chart_df, "종합 원화환산")


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


def render_investor_trends(investor_df: pd.DataFrame, error_message: Optional[str], holdings: Optional[pd.DataFrame] = None, investor_days: int = 3):
    st.divider()
    st.subheader(f"국장 보유 종목 최근 {investor_days}거래일 투자자별 순매수")

    st.caption("개인/외국인/기관 순매수는 토스증권 OpenAPI에 현재 제공되지 않아, 국장 종목만 pykrx로 조회합니다. 단위는 원화 거래대금 순매수입니다.")

    if error_message:
        st.warning(error_message)

    if investor_df.empty:
        st.info("투자자별 순매수 데이터가 없습니다.")
        return

    name_map = {}
    if holdings is not None and not holdings.empty:
        name_map = holdings.drop_duplicates("symbol").set_index("symbol")["name"].to_dict()

    df = investor_df.copy()
    df["종목명"] = df["symbol"].map(name_map).fillna(df["symbol"])

    value_cols = [c for c in df.columns if c not in ["date", "symbol", "종목명"]]

    def color_signed(value):
        try:
            numeric = float(value)
        except Exception:
            return ""
        if numeric > 0:
            return "color: #ff4b4b; font-weight: 700;"
        if numeric < 0:
            return "color: #4b8bff; font-weight: 700;"
        return ""

    def fmt_money(value):
        try:
            return f"{float(value):,.0f}"
        except Exception:
            return value

    for stock_name, g in df.groupby("종목명", sort=False):
        symbol_text = g["symbol"].iloc[0]
        st.markdown(f"#### {stock_name}")

        display = g[["date"] + value_cols].copy()
        display = display.rename(columns={"date": "날짜"})

        styled = (
            display.style
            .format({col: fmt_money for col in value_cols})
            .map(color_signed, subset=value_cols)
        )

        st.dataframe(styled, use_container_width=True, hide_index=True)

        chart_cols = [c for c in ["개인", "외국인", "기관합계"] if c in g.columns]
        if chart_cols:
            melted = g.melt(
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
                title=f"{stock_name} 투자자별 순매수",
                labels={"date": "날짜", "순매수금액": "순매수금액(원)"},
            )
            st.plotly_chart(fig, use_container_width=True)

    st.caption("색상 기준: 양수는 빨간색, 음수는 파란색으로 표시합니다.")


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

    render_investor_trends(investor_df, investor_error, holdings=holdings, investor_days=chart_days if False else st.session_state.get("investor_days", 3))
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

if "investor_days" not in st.session_state:
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

    st.subheader("투자자별 순매수 설정")
    inv_minus, inv_value, inv_plus = st.columns([1, 2, 1])
    with inv_minus:
        if st.button("－", key="investor_days_minus", use_container_width=True):
            st.session_state["investor_days"] = max(1, int(st.session_state.get("investor_days", 3)) - 1)
            st.rerun()
    with inv_value:
        investor_days_input = st.number_input(
            "거래일",
            min_value=1,
            max_value=60,
            value=int(st.session_state.get("investor_days", 3)),
            step=1,
            label_visibility="collapsed",
        )
    with inv_plus:
        if st.button("＋", key="investor_days_plus", use_container_width=True):
            st.session_state["investor_days"] = min(60, int(st.session_state.get("investor_days", 3)) + 1)
            st.rerun()
    st.session_state["investor_days"] = int(investor_days_input)
    st.caption(f"현재 설정: 최근 {st.session_state['investor_days']}거래일")

    st.divider()

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

                c1, c2, c3 = st.columns([1.65, 1.35, 0.75], gap="small")
                with c1:
                    st.markdown(
                        f"""
<div style="padding:0.35rem 0 0.1rem 0; font-weight:800; font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
{name}
</div>
""",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"""
<div style="padding:0.35rem 0 0.1rem 0; font-size:0.82rem; color:#777; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
현재가 {format_money_by_currency(default_price, currency)}
</div>
""",
                        unsafe_allow_html=True,
                    )
                with c3:
                    if st.button("추가", key=f"add_stock_mobile_{symbol}_{i}", use_container_width=True):
                        add_manual_stock_row(row)
                        st.success(f"{name} 추가 완료")
                        st.rerun()
                st.divider()
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
                    st.success(f"{name} ({symbol}) 추가 완료")
                    st.rerun()

        st.caption("추가 시 API 키가 있으면 실제 현재가가 현재가/매입가 기본값으로 들어갑니다. API 키가 없거나 조회 실패 시 0으로 들어가며 직접 수정할 수 있습니다.")

# 상단의 큰 편집 표는 제거하고, 아래 수량 +/- 표 하나만 사용합니다.
normalized_manual_editor = normalize_manual_portfolio(st.session_state["manual_portfolio"])[
    ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
]
st.session_state["manual_portfolio"] = normalized_manual_editor.copy()

# 현재 화면이 수기/데모 기반이면, 아래 대시보드 계산값이 즉시 바뀌게 반영
if st.session_state.get("last_demo_mode", True):
    manual_holdings_live = enrich_holdings(normalized_manual_editor)
    if not manual_holdings_live.empty:
        st.session_state["last_holdings"] = manual_holdings_live

st.markdown("#### 수기 포트폴리오")
st.caption("수량/단가 변경 시 총액이 바로 계산됩니다.")

quick_df = normalize_manual_portfolio(st.session_state["manual_portfolio"])[
    ["symbol", "name", "market_label", "currency", "quantity", "avg_price", "current_price"]
].reset_index(drop=True)

if quick_df.empty:
    st.info("수량 조정할 수기 종목이 없습니다.")
else:
    if is_mobile_mode():
        for i, row in quick_df.iterrows():
            symbol = row["symbol"]
            currency = row["currency"]
            qty = safe_float(row["quantity"], 0)
            avg_price = safe_float(row["avg_price"], 0)
            current_price = safe_float(row["current_price"], 0)

            st.markdown(
                f"""
<div class="mobile-card">
  <div class="mobile-card-title">{row["name"]}</div>
  <div class="mobile-card-sub">{symbol} · {currency}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            q1, q2, q3 = st.columns([0.75, 1.2, 0.75])
            if q1.button("－", key=f"m_qty_minus_{symbol}_{i}", use_container_width=True):
                quick_df.loc[i, "quantity"] = max(0, qty - 1)
                st.session_state["manual_portfolio"] = quick_df.copy()
                st.rerun()

            q2.markdown(
                f"""
<div style="text-align:center; padding-top:0.15rem;">
  <div style="font-size:0.72rem; color:#777;">수량</div>
  <div style="font-size:1.15rem; font-weight:800;">{qty:g}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            if q3.button("＋", key=f"m_qty_plus_{symbol}_{i}", use_container_width=True):
                quick_df.loc[i, "quantity"] = qty + 1
                st.session_state["manual_portfolio"] = quick_df.copy()
                st.rerun()

            p1, p2 = st.columns(2)
            new_avg = p1.number_input(
                "평균 매입가",
                min_value=0.0,
                value=float(avg_price),
                step=1.0,
                key=f"m_avg_{symbol}_{i}",
            )
            new_current = p2.number_input(
                "현재가",
                min_value=0.0,
                value=float(current_price),
                step=1.0,
                key=f"m_current_{symbol}_{i}",
            )

            if new_avg != avg_price or new_current != current_price:
                quick_df.loc[i, "avg_price"] = new_avg
                quick_df.loc[i, "current_price"] = new_current
                st.session_state["manual_portfolio"] = quick_df.copy()
                st.rerun()

            buy_amount = qty * new_avg
            eval_amount = qty * new_current
            profit = eval_amount - buy_amount

            st.markdown(
                f"""
<div class="mobile-card" style="margin-top:-0.15rem;">
  <div class="mobile-card-grid">
    <div><div class="mobile-label">총 매입</div><div class="mobile-value">{format_money_by_currency(buy_amount, currency)}</div></div>
    <div><div class="mobile-label">총 평가</div><div class="mobile-value">{format_money_by_currency(eval_amount, currency)}</div></div>
    <div><div class="mobile-label">평가손익</div><div class="{signed_class(profit)}">{format_money_by_currency(profit, currency)}</div></div>
    <div><div class="mobile-label">수익률</div><div class="{signed_class(profit)}">{format_rate_percent((profit / buy_amount * 100) if buy_amount else 0)}</div></div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

    else:
        header = st.columns([1.0, 1.8, 0.45, 0.7, 0.45, 1.1, 1.1, 1.1, 1.1])
        header[0].markdown("**종목코드**")
        header[1].markdown("**종목명**")
        header[2].markdown("")
        header[3].markdown("**수량**")
        header[4].markdown("")
        header[5].markdown("**평균 매입가**")
        header[6].markdown("**현재가**")
        header[7].markdown("**총 매입금액**")
        header[8].markdown("**총 평가금액**")

        for i, row in quick_df.iterrows():
            symbol = row["symbol"]
            currency = row["currency"]
            qty = safe_float(row["quantity"], 0)
            avg_price = safe_float(row["avg_price"], 0)
            current_price = safe_float(row["current_price"], 0)
            buy_amount = qty * avg_price
            eval_amount = qty * current_price

            cols = st.columns([1.0, 1.8, 0.45, 0.7, 0.45, 1.1, 1.1, 1.1, 1.1])
            cols[0].write(symbol)
            cols[1].write(row["name"])

            if cols[2].button("－", key=f"qty_minus_{symbol}_{i}", use_container_width=True):
                quick_df.loc[i, "quantity"] = max(0, qty - 1)
                st.session_state["manual_portfolio"] = quick_df.copy()
                st.rerun()

            cols[3].write(f"**{qty:g}**")

            if cols[4].button("＋", key=f"qty_plus_{symbol}_{i}", use_container_width=True):
                quick_df.loc[i, "quantity"] = qty + 1
                st.session_state["manual_portfolio"] = quick_df.copy()
                st.rerun()

            new_avg = cols[5].number_input(
                "평균 매입가",
                min_value=0.0,
                value=float(avg_price),
                step=1.0,
                key=f"avg_price_inline_{symbol}_{i}",
                label_visibility="collapsed",
            )
            new_current = cols[6].number_input(
                "현재가",
                min_value=0.0,
                value=float(current_price),
                step=1.0,
                key=f"current_price_inline_{symbol}_{i}",
                label_visibility="collapsed",
            )

            if new_avg != avg_price or new_current != current_price:
                quick_df.loc[i, "avg_price"] = new_avg
                quick_df.loc[i, "current_price"] = new_current
                st.session_state["manual_portfolio"] = quick_df.copy()
                st.rerun()

            buy_amount = qty * new_avg
            eval_amount = qty * new_current
            cols[7].write(format_money_by_currency(buy_amount, currency))
            cols[8].write(format_money_by_currency(eval_amount, currency))
col_refresh, col_save, col_reset = st.columns([1.6, 1, 2.7])
with col_refresh:
    if st.button("현재가/환율 실제값 갱신", use_container_width=True):
        updated_manual, refresh_error = refresh_manual_current_prices()
        if refresh_error:
            st.warning(refresh_error)
        else:
            st.success("현재가와 원달러 환율 갱신 완료")
        st.rerun()

with col_save:
    if st.button("수기 저장", use_container_width=True):
        st.session_state["manual_portfolio"] = normalized_manual_editor.copy()
        st.success("수기 포트폴리오 저장 완료")
        st.rerun()

with col_reset:
    if st.button("수기 포트폴리오 초기화", use_container_width=True):
        st.session_state["manual_portfolio"] = initial_manual_portfolio()
        st.success("초기화 완료")
        st.rerun()

if st.session_state.get("last_refresh_time"):
    st.caption(f"마지막 실제값 갱신: {st.session_state['last_refresh_time']}")


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
