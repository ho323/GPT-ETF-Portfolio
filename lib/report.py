import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv


# 파일 읽기 함수
def get_instructions(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            instructions = file.read()
        return instructions
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print("An error occurred while reading the file:", e)
    

# RAG를 위한 데이터 검색 함수
def retrieve_data(query, data_list):
    # 키워드 매칭
    results = [data for data in data_list if query.lower() in data.lower()]
    return results


# 데이터 파일 읽기 및 전처리 함수
def read_and_preprocess_data(file_path):
    df1 = pd.read_excel('./data/azure_upload/ETF배당내역.xlsx')
    df2 = pd.read_excel('./data/azure_upload/ETF점수정보.xlsx')
    df3 = pd.read_excel('./data/azure_upload/해외종목정보.xlsx')

    df = pd.merge(df1, df2, on='ticker', how='left').merge(df3, on='ticker', how='left')
    df = df.astype(str)
    df.set_index('ticker', inplace=True)
    df.fillna('-', inplace=True)
    df.drop(['date_y'], axis=1, inplace=True)

    df.to_csv(file_path, index=False)

    with open(file_path, 'r', encoding='utf-8-sig') as file:
        data = file.read()

    return data


# GPT-4 모델을 사용한 응답 생성 함수
def generate_response_report(query, data_list):
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    instructions = get_instructions('./instructions.md')
    retrieved_data = retrieve_data(query, data_list)
    context = " ".join(retrieved_data)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"},
        ],
    )
    return response.choices[0].message.content