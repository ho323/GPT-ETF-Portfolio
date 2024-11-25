import pandas as pd
import numpy as np
import yfinance as yf
from tqdm import tqdm
from datetime import datetime, timedelta


def preprocess_div():
    dividend=pd.read_csv("data/raw/NH_CONTEST_DATA_HISTORICAL_DIVIDEND.csv", encoding='cp949',na_values='-')

    dividend=dividend.dropna()

    # ediv_dt를 기준으로 최신 값만 가져오기 (etf_tck_cd 별로)
    latest_rows = dividend.sort_values(['etf_tck_cd', 'ediv_dt'], ascending=[True, False]).drop_duplicates(subset=['etf_tck_cd'], keep='first')

    #배당 기준 통일 : 연배당으로
    def annualize_dividend(row):
        if row['ddn_pym_fcy_cd'] == 'Quarterly':
            return row['ddn_amt'] * 4
        elif row['ddn_pym_fcy_cd'] == 'SemiAnnual':
            return row['ddn_amt'] * 2
        elif row['ddn_pym_fcy_cd'] == 'Annual':
            return row['ddn_amt'] * 1
        elif row['ddn_pym_fcy_cd'] == 'Monthly':
            return row['ddn_amt'] * 12

    def is_leap_year(year):
        """윤년 여부를 확인하는 함수"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def fix_invalid_date(date):
        """주어진 날짜가 유효하지 않으면 유효한 날짜로 변경"""
        try:
            # 날짜를 먼저 시도
            valid_date = pd.to_datetime(date, format='%Y%m%d')
        except ValueError:
            # 유효하지 않은 경우
            year = date // 10000
            month = (date // 100) % 100
            day = date % 100
            
            # 월이 1~12 범위 내인지 확인
            if month < 1 or month > 12:
                return None  # 잘못된 월
            
            # 해당 월의 마지막 날 찾기
            if month == 2:  # 2월인 경우 윤년 고려
                last_day_of_month = 29 if is_leap_year(year) else 28
            else:
                # 30일인 달
                if month in [4, 6, 9, 11]:
                    last_day_of_month = 30
                else:
                    last_day_of_month = 31

            # 유효한 날짜로 조정
            if day < 1:
                day = 1
            elif day > last_day_of_month:
                day = last_day_of_month
                
            valid_date = datetime(year, month, day)
        
        return valid_date

    # 연간 배당으로 환산
    latest_rows['annualized_dividend'] = latest_rows.apply(annualize_dividend, axis=1)

    price = []
    for i in range(len(latest_rows['ediv_dt'])):
        date=latest_rows['ediv_dt'].iloc[i]
        if pd.isna(date):  # 날짜가 NaN인 경우 건너뛰기
            price.append("NaN")
            continue
        
        # 유효하지 않은 날짜 수정
        fixed_date = fix_invalid_date(date)
        if fixed_date is None:
            print(f"Invalid month for date: {date}. Skipping...")
            price.append("NaN")
            continue

        # 날짜 찾아서 수정종가 출력
        try:
            startday = fixed_date - timedelta(days=1)
            endday = fixed_date + timedelta(days=3)
            
            # 정수형 날짜를 pandas Timestamp로 변환 후 문자열 포맷팅
            startday_str = startday.strftime('%Y-%m-%d')
            endday_str = endday.strftime('%Y-%m-%d')
            
            name=latest_rows['etf_tck_cd'].iloc[i]

            result = yf.download(name, start=startday_str, end=endday_str)
            if not result.empty:  # 데이터가 있는지 확인
                price.append(result['Adj Close'][0])  # 첫 번째 값을 추가
            else:
                price.append("NaN")  # 데이터가 없으면 None 추가
        except Exception as e:  # 예외 처리
            print(f"Error downloading data for {startday_str} to {endday_str}: {e}")
            price.append("NaN")
            continue  # 에러 발생 시 None 추가"""

    latest_rows['price'] = price

    #결측치 제거
    latest_rows=latest_rows.dropna()
    latest_rows['price']=latest_rows['price'].astype(float)

    #(1주당 배당금 / 주가) × 100
    latest_rows['dividend_yield']=latest_rows['annualized_dividend']/latest_rows['price']*100
    completed_dividend=latest_rows.copy()

    ##AAPB 만 데이터가 잘못되어서 이거 바꿔줄게요. 즉 aapb 데이터 바꾼 버전 이 completed_dividend 이고 안바꾼 버젼이 latest_rows
    completed_dividend['dividend_yield'].iloc[4]=completed_dividend['dividend_yield'].iloc[4]/12
    completed_dividend=completed_dividend.dropna()

    dividends_data=[]
    count=0#불러오기 진행도 체크용

    for ticker in tqdm(completed_dividend['etf_tck_cd']):
        stock = yf.Ticker(ticker) 
        # 배당 성향(Payout Ratio) 가져오기
        payout_ratio = stock.info.get("payoutRatio")
        
        # 배당 성장률 계산을 위한 배당금 히스토리 가져오기
        dividends = stock.dividends
        # 날짜 정보가 'Date' 열에 있다면, 이를 DatetimeIndex로 설정
        dividends.index = pd.to_datetime(dividends.index)
        # 연간 배당금 총합 구하기
        annual_dividends = dividends.resample('Y').sum()
        if len(annual_dividends) >= 2:
            initial_dividend = annual_dividends.iloc[0]
            final_dividend = annual_dividends.iloc[-1]
            years = len(annual_dividends) - 1
            dividend_growth_rate = (final_dividend / initial_dividend) ** (1 / years) - 1
            
        else:
            dividend_growth_rate = np.nan


        dividends_data.append({'etf_tck_cd':ticker,
                            "Payout Ratio": payout_ratio,
                            "연평균 배당 성장률 (CAGR)": dividend_growth_rate})
        
    dividends_data = pd.DataFrame(dividends_data)
    dividend_final=pd.merge(completed_dividend, dividends_data, on='etf_tck_cd')
    
    dividend_final.to_csv('dividend_final.csv', index=False, encoding='utf-8-sig')


def preprocess_growth():
    # 1. 필요한 데이터 읽기
    stock_daily = pd.read_csv("data/raw/NH_CONTEST_STK_DT_QUT.csv", encoding='cp949', na_values='-')
    stock_info = pd.read_csv("data/raw/NH_CONTEST_NW_FC_STK_IEM_IFO.csv", encoding='cp949', na_values='-')
    
    # 2. 필요한 컬럼 선택 및 필터링
    stock_daily_data = stock_daily[['bse_dt', 'tck_iem_cd', 'iem_end_pr']]
    stock_info_data = stock_info[['tck_iem_cd', 'fc_sec_krl_nm', 'fc_sec_eng_nm', 'stk_etf_dit_cd', 
                                  'ltg_tot_stk_qty', 'ser_cfc_nm', 'ids_nm', 'mkt_pr_tot_amt']]
    
    # 주식만 선택
    only_stock_info = stock_info_data[stock_info_data['stk_etf_dit_cd'] == '주식']

    # 3. `yfinance`를 통해 PER, PBR, ROE, 부채 비율 가져오기
    tickers = only_stock_info['tck_iem_cd'].unique()
    financial_data = []

    for ticker in tqdm(tickers, desc="Fetching financial data"):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 필요한 데이터 수집
            per = info.get('trailingPE', np.nan)
            pbr = info.get('priceToBook', np.nan)
            roe = info.get('returnOnEquity', np.nan)
            debt_to_equity = info.get('debtToEquity', np.nan)
            
            financial_data.append({
                'tck_iem_cd': ticker,
                'PER': per,
                'PBR': pbr,
                'ROE': roe,
                '부채 비율': debt_to_equity
            })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            financial_data.append({
                'tck_iem_cd': ticker,
                'PER': np.nan,
                'PBR': np.nan,
                'ROE': np.nan,
                '부채 비율': np.nan
            })

    # 데이터프레임 변환
    financial_df = pd.DataFrame(financial_data)

    # 4. 결측치 처리 및 계산
    # PER, PBR, ROE
    financial_df['PER'] = financial_df['PER'].astype(float)
    financial_df['PBR'] = financial_df['PBR'].astype(float)
    financial_df['ROE'] = financial_df['ROE'].astype(float)
    financial_df['부채 비율'] = financial_df['부채 비율'].astype(float)

    # PER, PBR, ROE 값 계산
    financial_df['PER'] = financial_df.apply(
        lambda x: x['PBR'] / x['ROE'] if pd.isna(x['PER']) and pd.notna(x['PBR']) and pd.notna(x['ROE']) else x['PER'], 
        axis=1
    )
    financial_df['PBR'] = financial_df.apply(
        lambda x: x['PER'] * x['ROE'] if pd.isna(x['PBR']) and pd.notna(x['PER']) and pd.notna(x['ROE']) else x['PBR'], 
        axis=1
    )
    financial_df['ROE'] = financial_df.apply(
        lambda x: x['PBR'] / x['PER'] if pd.isna(x['ROE']) and pd.notna(x['PER']) and pd.notna(x['PBR']) else x['ROE'], 
        axis=1
    )

    # 5. 섹터별 평균 값 계산
    merged_df = pd.merge(only_stock_info, financial_df, on='tck_iem_cd', how='inner')

    def calculate_sector_mean(group):
        return {
            'PER_mean': group['PER'].mean(),
            'PBR_mean': group['PBR'].mean(),
            'ROE_mean': group['ROE'].mean(),
            '부채 비율_mean': group['부채 비율'].mean()
        }

    sector_means = merged_df.groupby('ser_cfc_nm').apply(calculate_sector_mean).apply(pd.Series).reset_index()

    # 6. 성장주와 가치주 태그 생성
    def categorize_stock(row, sector_means):
        sector_data = sector_means[sector_means['ser_cfc_nm'] == row['ser_cfc_nm']]
        if sector_data.empty:
            return np.nan

        per_mean = sector_data['PER_mean'].values[0]
        pbr_mean = sector_data['PBR_mean'].values[0]

        if pd.isna(row['PER']) or pd.isna(row['PBR']):
            return np.nan

        if row['PER'] >= per_mean and row['PBR'] >= pbr_mean:
            return '성장주'
        elif row['PER'] < per_mean and row['PBR'] < pbr_mean:
            return '가치주'
        else:
            return np.nan

    merged_df['value_or_growth'] = merged_df.apply(lambda x: categorize_stock(x, sector_means), axis=1)

    # 7. 결과 저장
    merged_df.to_csv("data/value_or_growth.csv", index=False, encoding="utf-8-sig")

