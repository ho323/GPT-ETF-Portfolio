import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


class Tagging:
    def __init__(self, df):
        self.df = df
        self.tags = []
        
        self._benchmark_etf()
        self.etf_info=pd.read_csv("data/raw/NH_CONTEST_ETF_SOR_IFO.csv", encoding='cp949')
        self.stk_info=pd.read_csv("data/raw/NH_CONTEST_NW_FC_STK_IEM_IFO.csv", encoding='cp949')
        self.etf_hold=pd.read_csv("data/raw/NH_CONTEST_DATA_ETF_HOLDINGS.csv", encoding='cp949')
        self.etf_stk = pd.merge(self.etf_hold, self.stk_info, on='tck_iem_cd', how='left')
        self.div = pd.read_csv("data/dividend_final.csv")
        self.vog = pd.read_csv("data/value_or_growth.csv")

    def _benchmark_etf(self):
        # 1. 벤치마크 지수 선택
        etf = yf.Ticker('SPY')

        # 2. 3개월 전 날짜 계산
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=90)  # 약 3개월 전 날짜

        # 3. 3개월 간 주가 데이터 불러오기 (종가 기준)
        price_data = etf.history(start=start_date, end=end_date)

        # 4. 총수익률 계산
        # 시작일 종가와 종료일 종가를 이용하여 수익률을 계산
        start_price = price_data['Close'].iloc[0]
        end_price = price_data['Close'].iloc[-1]
        
        self.benchmark_return = (end_price - start_price) / start_price * 100  # 퍼센트로 계산

    def classify_momentum(self, pft):        
        if pft is None:
            return 'Unknown'
        elif pft >= self.benchmark_return:
            return '모멘텀'
        else:
            return None
        
    def classify_lowvol(self, v_zsor):
        if v_zsor is None:
            return 'Unknown'
        elif v_zsor <= self.etf_info['vty_z_sor'].quantile(0.25):
            return '로우볼'
        else:
            return None

    def classify_stk(self, row):
        # 시총 합계에 따라 대형주/중형주/소형주로 구분
        if row >= 10000:
            return '대형주'
        elif row >= 2000:
            return '중형주'
        elif row < 2000:
            return '소형주'
        
        else: #시총 값이 없을때
            return 'NaN'
        
    def classify_etf_dividend(self, dividend_yield):
        if dividend_yield is None:
            return None
        elif dividend_yield >= 3:  # 3% 이상
            return '고배당'
        else:  
            return None
        
    def classify_etf_growth(self, row):
        if row is None:
            return None
        elif row == '가치주':
            return '가치주'
        elif row == '성장주':
            return '성장주'
        else:
            return None
        
    def _get_etf_info(self, row):
        etf = yf.Ticker(row['etf_iem_cd'])
        info = etf.info
        description = info.get("longBusinessSummary", "").lower()

        return description

    def find_tag_keywards(self, row):
        description = row['deescription']
        if "value" in description or "undervalued" in description:
            row["가치주"] = "가치주"
        if "growth" in description or "innovative" in description:
            row["성장주"] = "성장주"
        if "quality" in description or "high-quality" in description:
            row["퀄리티"] = "퀄리티"
        if "momentum" in description:
            row["모멘텀"] = "모멘텀"
        if "low volatility" in description or "low risk" in description:
            row["로우볼"] = "로우볼"


    def tagging(self):
        # self.stk_info['description'] = self.etf_info.apply(self._get_etf_info, axis=1)

        self.df['모멘텀'] = self.etf_info['mm3_tot_pft_rt'].apply(self.classify_momentum)
        self.df['로우볼'] = self.etf_info['vty_z_sor'].apply(self.classify_lowvol)
        self.df['사이즈'] = self.etf_stk['mkt_pr_tot_amt'].apply(self.classify_stk)
        self.df['고배당'] = self.div['dividend_yield'].apply(self.classify_etf_dividend)
        self.df['가치주'] = self.vog['value_or_growth'].apply(self.classify_etf_growth)
        self.df['성장주'] = self.vog['value_or_growth'].apply(self.classify_etf_growth)

        # self.df = self.df.apply(self.find_tag_keywards)

        self.df = self.df[['tck_iem_cd', '모멘텀', '로우볼', '사이즈', '고배당', '가치주', '성장주']]
        self.df.to_csv("data/tagging.csv", index=False)

def generate_response_tagging(query):
    # 태그 데이터 불러오기
    tag_data = pd.read_csv("data/tagging.csv")
    tag_data = tag_data.fillna(value='')

    tag_data = json.dumps(tag_data.to_dict(orient='records'))

    load_dotenv()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 투자 전략 전문가입니다. 주어진 태그 데이터를 참조하여 추천할 ETF 5개를 아주 간결하게 티커만 제시해주세요. 예시: ['DIVO', 'QQQ', 'IWM', 'EFA', 'EEM']"},
            {"role": "user", "content": f"태그 데이터: {tag_data}"},
            {"role": "user", "content": f"추천할 전략: {query}\n\n추천 ETF 5개 \n\nAnswer: "},
        ],
    )
    return response.choices[0].message.content