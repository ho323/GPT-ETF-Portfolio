import os
from openai import OpenAI
from dotenv import load_dotenv


# 사용자 정보 입력 받기
def get_user_information():
    user_information = dict()

    # 기존 유저 정보 활용
    user_information["name"] = "김철수"
    user_information["age"] = "20"
    user_information["gender"] = "남자"
    user_information["occupation"] = "대학생"
    user_information["income"] = "0"
    user_information["investment"] = "7"    # 투자 년수
    user_information["investment_amount"] = "100000000"

    # 투자 정보 입력 이상형 월드컵
    user_information["size"] = input("다음 세 개 중 하나만 골라야 한다면 내 선택은? \n1. 대형주 투자 2. 중형주 투자 3. 소형주 투자")
    user_information["strategy"] = input("나는 어떤 ETF 투자 전략이 잘 맞을까? \n1. 가치주 투자 2. 성장주 투자")
    user_information["prefer"] = input("내가 더 선호하는 주식은? \n 1. 배당주 2. 성장주")
    user_information["period"] = input("주식을 한 번 사면 주로 언제까지 들고 있지? \n 1. 한달 2. 6개월 3. 1년 4. 3년 5. 5년 6. 10년 이상")
    user_information["volatility"] = input("나는 어느 정도의 변동성까지 버틸 수 있을까? \n1. 최상 2. 상 3. 중 4. 하 5. 최하")

    return user_information


# 프롬프트 생성 함수
def generate_prompt(user_information):
    prompt = f"""아래는 투자자의 정보입니다. 
    해당 정보를 바탕으로 투자 성향을 분석하고, 추천하는 투자 전략의 순위를 제시해주세요.
    
    # 투자자 정보
    - 이름: {user_information['name']}
    - 나이: {user_information['age']}
    - 성별: {user_information['gender']}
    - 직업: {user_information['occupation']}
    - 연소득: {user_information['income']}원
    - 투자경력: {user_information['investment']}년
    - 투자자금: {user_information['investment_amount']}원
    - 주식 규모 선호: {user_information['size']}
    - 투자 전략 선호: {user_information['strategy']}
    - 선호 주식 유형: {user_information['prefer']}
    - 보유 기간: {user_information['period']}
    - 감내할 수 있는 변동성: {user_information['volatility']}
    
    # 추천할 수 있는 투자 전략 목록 
    - 가치주 투자
    - 성장주 투자
    - 고배당 투자
    - 퀄리티 투자
    - 모멘텀 투자
    - 로우볼 투자
    - 대형주 투자
    - 중형주 투자
    - 소형주 투자

    # 출력 예시
    김철수 님의 정보를 바탕으로 분석해보면, 24세의 대학생으로 상대적으로 젊은 나이에 상당한 투자 경험(7년)을 가지고 있습니다. 연소득이 0원인 상황에서도 1억 원의 투자자금을 보유하고 있어 금전적 여유가 있는 투자자로 판단됩니다. 중형주와 성장주에 대한 선호도가 높고, 감내할 수 있는 변동성이 상으로 설정되어 있어 대체로 위험을 감수할 준비가 되어 있습니다.

    이 정보를 바탕으로 분석한 투자 성향은 다음과 같습니다:

    1. **위험 수용 능력**: 젊은 투자자이고 높은 변동성을 감내할 수 있으므로 공격적인 투자 전략을 선호할 가능성이 높습니다.
    2. **선호하는 주식 유형**: 성장주와 중형주 개발에 집중하고 있어 빠른 성장이 예상되는 기업에 대한 관심이 두드러집니다.
    3. **투자 시간**: 1년의 보유 기간을 고려했을 때, 단기적인 성과보다는 적어도 중기적인 성과를 목표로 할 수 있습니다.

    위의 분석에 기반하여 김호성에게 추천하는 투자 전략의 순서는 아래와 같습니다:

    1. **성장주 투자**: 그의 주식 유형 및 투자 전략에 완벽히 부합하며, 중형주로도 많은 성장 가능성이 있는 기업에 투자할 수 있습니다.
    2. **모멘텀 투자**: 주가 상승 추세에 있는 주식을 선택하여 단기적인 수익을 추구하는 전략입니다. 김호성의 선호에 잘 맞습니다.
    3. **중형주 투자**: 선호 주식 규모와 일치하며, 중형주는 대형주보다 높은 성장 잠재력을 지닌 경우가 많습니다.
    4. **퀄리티 투자**: 안정적인 성장성을 가진 고품질 주식에 투자하여 리스크를 적절히 관리하면서도 높은 성과를 기대할 수 있습니다.
    5. **소형주 투자**: 상대적으로 위험이 크지만 높은 성장 가능성을 가진 소형주에 대한 투자를 고려해봐도 좋습니다.
    6. **로우볼 투자**: 가격 하락 이후 회복 가능성이 있는 주식에 대한 투자는 추가적인 수익성을 높일 수 있습니다.
    7. **고배당 투자**: 안정적인 현금 흐름을 원할 때 고려할 수 있지만, 현재 성장 투자 성향에는 부합하지 않을 수 있습니다.
    8. **가치주 투자**: 당장의 성장 잠재력보다 저평가된 주식에 투자하는 전략으로, 김호성의 성향과는 거리가 있습니다.
    9. **대형주 투자**: 전반적으로 안정적이지만, 김호성의 공격적인 성장 투자 성향과는 잘 맞지 않을 것으로 보입니다.

    상위 추천 전략
    1. 성장주 투자
    2. 모멘텀 투자
    3. 중형주 투자
    4. 퀄리티 투자
    5. 소형주 투자
    """

    return prompt


# GPT-4 모델을 사용한 응답 생성 함수
def generate_response_recommendation(prompt):    
    load_dotenv()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 투자 전략 전문가입니다. 주어진 유저 정보를 바탕으로 투자 성향을 분석하고, 추천하는 투자 전략의 순위를 제시해주세요."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content

