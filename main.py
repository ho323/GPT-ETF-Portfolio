import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from lib.preprocessing import preprocess_div, preprocess_growth
from lib.recommendation import get_user_information, generate_prompt, generate_response_recommendation
from lib.tagging import Tagging, generate_response_tagging
from lib.report import read_and_preprocess_data, generate_response_report
from lib.backtest import ETFBacktest

if __name__ == '__main__':
    # 데이터 전처리
    preprocess_div()    # 배당 정보 전처리
    preprocess_growth()

    # 사용자 정보 받기
    user_information = get_user_information()
    prompt = generate_prompt(user_information)

    # 추천 전략 생성
    result = generate_response_recommendation(prompt)
    print(result)
    with open('user_recommendation.txt', 'w') as f:
        f.write(result)

    # 상위 5개 추천 전략 추출
    top_st = result.split('\n')[-5:]
    top_st = [st[3:] for st in top_st]
    
    # 전략별 추천 ETF 생성
    df = pd.read_csv("data/raw/NH_CONTEST_NW_FC_STK_IEM_IFO.csv", encoding='cp949')
    df = df[df['stk_etf_dit_cd'] == 'ETF']

    tg = Tagging(df)
    tg.tagging()

    recommended_etfs = [] # 2차원 배열 
    for st in top_st:
        etfs = eval(generate_response_tagging(st)) # ['DIVO', 'QQQ', 'IWM', 'EFA', 'EEM']
        recommended_etfs.append(etfs)
        print(f"{st} 전략 추천 ETF: {etfs}")


    # ETF 분석 보고서 작성
    recommended_etfs = sum(recommended_etfs, [])
    data_list = [read_and_preprocess_data('data/rag_data.csv')]
    for query in recommended_etfs:
        result = generate_response_report(query, data_list)
        print(result)

        with open(f'{query}_report.txt', 'w') as f:
            data = f.write(result)

    # 백테스트 실행
    etf_basket = recommended_etfs
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    bt = ETFBacktest(
        etf_symbols=etf_basket,
        start_date=start_date,
        end_date=end_date,
    )
    metrics = bt.run_backtest()
    print("\nPerformance Metrics: \n", metrics)
    metrics.to_csv('metrics.csv')