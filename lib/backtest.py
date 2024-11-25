import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


class ETFBacktest:
    def __init__(self, etf_symbols, start_date, end_date):
        self.etf_symbols = etf_symbols
        self.start_date = start_date
        self.end_date = end_date
        self.risk_free_rate = 0.02  # 연간 무위험 수익률 (예: 2%)

    def fetch_data(self):
        """ETF 데이터 가져오기"""
        self.data = pd.DataFrame()
        
        for symbol in self.etf_symbols:
            df = yf.download(symbol, start=self.start_date, end=self.end_date)['Adj Close']
            self.data[symbol] = df

        self.nasdaq = yf.download("^IXIC", start=self.start_date, end=self.end_date)['Adj Close']
        self.nasdaq = self.nasdaq.pct_change()
        self.nasdaq = (1 + self.nasdaq).cumprod()
                    
        return self.data
    
    def calculate_returns(self):
        """일간 수익률과 누적 수익률 계산"""
        self.daily_returns = self.data.pct_change()
        self.cumulative_returns = (1 + self.daily_returns).cumprod()
        
        # 연간화된 수익률 계산
        self.annual_returns = (self.cumulative_returns.iloc[-1] ** (252/len(self.cumulative_returns)) - 1)
        
        return self.daily_returns, self.cumulative_returns
    
    def calculate_metrics(self):
        """주요 성과 지표 계산"""
        metrics = {}
        
        # 연간화된 변동성
        annual_vol = self.daily_returns.std() * np.sqrt(252)
        
        # Sharpe Ratio
        excess_returns = self.annual_returns - self.risk_free_rate
        sharpe_ratio = excess_returns / annual_vol
        
        # Sortino Ratio
        negative_returns = self.daily_returns.copy()
        negative_returns[negative_returns > 0] = 0
        downside_vol = negative_returns.std() * np.sqrt(252)
        sortino_ratio = excess_returns / downside_vol
        
        # Maximum Drawdown
        rolling_max = self.cumulative_returns.expanding().max()
        drawdowns = self.cumulative_returns / rolling_max - 1
        max_drawdown = drawdowns.min()
        
        # Average Drawdown
        avg_drawdown = drawdowns.mean()
        
        for symbol in self.etf_symbols:
            metrics[symbol] = {
                'Annual Return': f"{self.annual_returns[symbol]:.4f}",
                'Sharpe Ratio': f"{sharpe_ratio[symbol]:.2f}",
                'Sortino Ratio': f"{sortino_ratio[symbol]:.2f}",
                'Max Drawdown': f"{max_drawdown[symbol]:.4f}",
                'Avg Drawdown': f"{avg_drawdown[symbol]:.4f}"
            }

        metrics = pd.DataFrame(metrics)
        metrics = metrics.astype(float)
        metrics['ETF Portfolio'] = metrics.mean(1)

        metrics = metrics.T
        metrics["Annual Return"] = metrics["Annual Return"].apply(lambda x: "{:.2f}%".format(x*100))
        metrics["Max Drawdown"] = metrics["Max Drawdown"].apply(lambda x: "{:.2f}%".format(x*100))
        metrics["Avg Drawdown"] = metrics["Avg Drawdown"].apply(lambda x: "{:.2f}%".format(x*100))
        
        return metrics
    
    def plot_performance(self):
        """포트폴리오 성과 시각화"""
        plt.figure(figsize=(15, 6))
        
        # 수익률 차트
        # self.cumulative_returns.mean(axis=1).plot()
        # self.nasdaq.plot()
        plt.plot(self.cumulative_returns.mean(axis=1), label='ETF Portfolio')
        plt.plot(self.nasdaq, label='Nasdaq')
        plt.title('ETF Portfolio Cumulative Returns')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Return')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig('ETF_Portfolio_Cumulative_Returns.png', dpi=300, bbox_inches='tight')


    def run_backtest(self):
        """백테스트 실행"""
        
        # 데이터 가져오기
        data = self.fetch_data()
        
        # 수익률 계산
        self.calculate_returns()
        
        # 성과 지표 계산
        metrics = self.calculate_metrics()
        
        # 결과 시각화
        self.plot_performance()
        
        return metrics
