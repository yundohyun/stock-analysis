<h1 align="center">주식 & 코인 분석 Streamlit</h1>

![Header](https://capsule-render.vercel.app/api?type=waving&height=300&color=gradient&text=Stock%20Analysis&animation=fadeIn&&customColorList=1)

<p align="center">주식과 코인에 대해서 여러 분석을 제공해주는 프로젝트</p>

## 🙋‍♂️ 팀원

|                        <span style="font-size: 20px">윤도현 (팀장)</span>                         |                           <span style="font-size: 20px">정진우</span>                            |
| :-----------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------: |
| [![Profile](https://avatars.githubusercontent.com/u/160732611?v=4)](https://github.com/yundohyun) | [![Profile](https://avatars.githubusercontent.com/u/202902928?v=4)](https://github.com/jinpiter) |
|                            [@yundohyun](https://github.com/yundohyun)                             |                             [@jinpiter](https://github.com/jinpiter)                             |
|                                           기획 및 개발                                            |                                        기획 및 개발 보조                                         |

## 💻 기술 스택

- Python 3.13.5
- streamlit
- plotly
- yfinance

## 📚 기획 의도

- 본 프로젝트는 개인 투자자로서 주식 시장에 깊은 관심을 가진 개발자가, 자신의 투자 경험 속에서 느낀 불편함을 직접 해결하고자 시작한 프로젝트입니다
- 매매 기록을 일일이 엑셀에 입력하고, 여러 앱을 오가며 주가 정보와 재무제표를 확인해야 하는 번거로움을 겪으면서, "개발자로서 이런 작업을 자동화할 수 있지 않을까"라는 생각에서 착안하게 되었습니다.
- 종가를 기준으로 정확한 매수 가격을 자동 조회하고, 실시간 수익률을 계산하며, 한 곳에서 모든 투자 정보를 관리할 수 있는 통합 대시보드를 개발함으로써, 같은 고민을 하는 많은 개인 투자자들에게 실질적인 도움을 주고자 합니다.

## ⚙️ 구현 기능

### 기능 요약
해당 프로젝트는 야후 파이낸스를 이용하여 금융데이터를 가져온 후, 이를 바탕으로 데이터를 분석하여 사용자에게 유용한 정보를 제공합니다.

### 주가 차트
사용자가 기간을 직접 선택하여, 원하는 기간으로 검색 종목의 주가 그래프를 분석할 수 있는 경험을 제공합니다.

### 배당 분석
검색 종목의 배당 내역을 표로 확인 할 수 있고,  이를 바탕으로 한 배당금 추이 및 배당금 합계를 막대 그래프로 확인할 수 있습니다.

### 재무 제표
손익계산서, 대차대조표, 현금흐름표를 선택하여 분기별 또는 연간으로 조회하여 표로 정리된 재무 제표를 빠르고 간편하게 살펴볼 수 있습니다.

### 포트폴리오
사용자의 투자 수익률을 계산하는 페이지입니다.  종목과 날짜를 지정하고, 가격을 입력하면 그 당시의 매수 금액과 현재 평가 금액을 기반으로 종목별 수익률 및 매수액, 현재가치를 비교한 내용을 막대 그래프로 확인할 수 있습니다.

## 📒 사용 방법

1. [`stock_analysis.py`](https://github.com/yundohyun/stock-analysis/raw/refs/heads/main/stock_analysis.py) 파일을 다운로드합니다.
2. 다운로드 받은 파일의 디렉토리에서 `pip install yfinance plotly streamlit numpy` 명령어를 실행합니다.
3. `streamlit run ./stock_analysis.py` 명령어를 실행하여 streamlit 서버를 실행합니다.
4. [`http://localhost:8501`](http://localhost:8501) 주소로 들어가서 사용하시면 됩니다.

## 🎥 시연 영상

[![Video Label](http://img.youtube.com/vi/xfOvBO3Tjv8/0.jpg)](https://youtu.be/xfOvBO3Tjv8)

## 💬 느낀점

### 윤도현

주식 및 코인 분석 사이트를 streamlit으로 제작하면서 생각보다 구현 자유도가 높아서 놀라웠고 인공지능을 참고하여 개발을 진행하였는데 아쉬운 부분이 많지만 인공지능이 많이 발전했다는 생각이 들어 흥미로웠습니다.

### 정진우

스스로 분석을 할 때에는 streamlit 디자인 부분이나 분석 아이디어 부분이나 한계가 많았었는데, 인공지능을 이용해서 만들어진 결과물을 보니 구현하는 창의성도 신기했고, 결과물도 구현이 잘 됐었던 점이 놀라웠습니다.
