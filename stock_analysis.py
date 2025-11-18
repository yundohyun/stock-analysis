import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta, date
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="주식 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 통합 주식 데이터 분석 대시보드")

# 세션 상태 초기화 (최상단에서 수행)
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = []

if 'closing_price' not in st.session_state:
    st.session_state.closing_price = 0.0

if 'closing_price_found' not in st.session_state:
    st.session_state.closing_price_found = False

# 사이드바 - 종목 선택
with st.sidebar:
    st.title("⚙️ 설정")
    ticker = st.text_input(
        '종목 티커 입력',
        value='AAPL',
        placeholder='예: AAPL, 005930.KS (삼성전자)'
    )
    
    if ticker:
        try:
            info = yf.Ticker(ticker)
            st.sidebar.success(f"✅ {ticker} 로드 완료")
        except Exception as e:
            st.sidebar.error(f"❌ 종목을 찾을 수 없습니다")

# 헬퍼 함수: 안전한 데이터 다운로드
def safe_download(ticker, start_date=None, end_date=None, period=None):
    """안전하게 주가 데이터 다운로드 - 데이터 프레임 정규화"""
    errors = []
    
    # 방법 1: 날짜 범위 지정
    if start_date and end_date:
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
            data = normalize_dataframe(data, ticker)
            if data is not None and not data.empty:
                return data, None
        except Exception as e:
            errors.append(f"방법1 실패: {str(e)}")
        
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            data = normalize_dataframe(data, ticker)
            if data is not None and not data.empty:
                return data, None
        except Exception as e:
            errors.append(f"방법1-2 실패: {str(e)}")
    
    # 방법 2: period 지정
    if period:
        try:
            data = yf.download(ticker, period=period, progress=False, auto_adjust=False)
            data = normalize_dataframe(data, ticker)
            if data is not None and not data.empty:
                return data, None
        except Exception as e:
            errors.append(f"방법2 실패: {str(e)}")
        
        try:
            data = yf.download(ticker, period=period, progress=False)
            data = normalize_dataframe(data, ticker)
            if data is not None and not data.empty:
                return data, None
        except Exception as e:
            errors.append(f"방법2-2 실패: {str(e)}")
    
    # 모든 방법 실패
    error_msg = "\n".join(errors) if errors else "알 수 없는 오류"
    return None, error_msg

# 헬퍼 함수: 데이터프레임 정규화
def normalize_dataframe(data, ticker):
    """데이터프레임을 정규 형식으로 변환"""
    try:
        # 데이터가 비어있는지 확인
        if data is None or data.empty:
            return None
        
        # 멀티 인덱스인 경우 싱글 종목만 추출
        if isinstance(data.columns, pd.MultiIndex):
            # 멀티 레벨 컬럼 구조
            if ticker in data.columns.get_level_values(1):
                data = data.xs(ticker, level=1, axis=1)
            elif ticker in data.columns.get_level_values(0):
                data = data[ticker]
        
        # 필수 컬럼 확인
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # 컬럼 정리 (대소문자 통일)
        data.columns = [col if col in required_cols else col for col in data.columns]
        
        # 필수 컬럼이 모두 있는지 확인
        if not all(col in data.columns for col in required_cols):
            return None
        
        # 필요한 컬럼만 선택
        data = data[required_cols].copy()
        
        # 데이터 타입 변환
        for col in required_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # NaN이 모두인 경우 제외
        if data.isna().all().all():
            return None
        
        # 인덱스 이름 설정
        data.index.name = 'Date'
        
        return data
    
    except Exception as e:
        return None

# 헬퍼 함수: 숫자 포맷팅
def format_number(value):
    """숫자 값을 안전하게 포맷팅"""
    if value is None or pd.isna(value):
        return 'N/A'
    if isinstance(value, str):
        return value
    try:
        value = float(value)
        if abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        elif abs(value) < 1 and value != 0:
            return f"${value:.4f}"
        else:
            return f"${value:.2f}"
    except:
        return str(value)

# 헬퍼 함수: 특정 날짜의 종가 가져오기
def get_closing_price_on_date(ticker, target_date):
    """특정 날짜의 종가 가져오기"""
    try:
        # date 객체를 datetime으로 변환
        if isinstance(target_date, date) and not isinstance(target_date, datetime):
            target_date = datetime.combine(target_date, datetime.min.time())
        
        # Timestamp로 변환
        target_timestamp = pd.Timestamp(target_date)
        
        # 해당 날짜 전후 데이터 조회
        start_date = target_timestamp - timedelta(days=5)
        end_date = target_timestamp + timedelta(days=5)
        
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        
        if data is None or data.empty:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data is None or data.empty:
            return None
        
        # 멀티 인덱스인 경우 처리
        if isinstance(data.columns, pd.MultiIndex):
            if ticker in data.columns.get_level_values(1):
                data = data.xs(ticker, level=1, axis=1)
            elif ticker in data.columns.get_level_values(0):
                data = data[ticker]
        
        # 인덱스를 Timestamp로 정규화
        data.index = pd.to_datetime(data.index)
        
        # 정확한 날짜의 데이터 찾기
        if target_timestamp in data.index:
            return float(data.loc[target_timestamp, 'Close'])
        
        # 없으면 가장 가까운 거래일 찾기
        data_sorted = data.sort_index()
        idx = data_sorted.index.searchsorted(target_timestamp)
        
        if idx > 0:
            # 이전 거래일
            closest_date = data_sorted.index[idx - 1]
            return float(data_sorted.loc[closest_date, 'Close'])
        elif idx < len(data_sorted):
            # 다음 거래일
            closest_date = data_sorted.index[idx]
            return float(data_sorted.loc[closest_date, 'Close'])
        
        return None
    
    except Exception as e:
        return None

# 탭 생성
if ticker:
    try:
        info = yf.Ticker(ticker)
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["📈 홈", "📊 주가차트", "💰 배당분석", "🏢 회사정보", "📑 재무제표", "💼 포트폴리오"]
        )
        
        # ============ TAB 1: 홈 ============
        with tab1:
            st.subheader(f"{ticker} - 기본 정보")
            
            company_info = info.info
            
            # 메트릭 카드
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                current_price = company_info.get('currentPrice', None)
                if current_price and not pd.isna(current_price):
                    st.metric("현재가", f"${float(current_price):.2f}")
                else:
                    st.metric("현재가", "N/A")
            
            with col2:
                market_cap = company_info.get('marketCap', None)
                if market_cap and not pd.isna(market_cap):
                    st.metric("시가총액", format_number(float(market_cap)))
                else:
                    st.metric("시가총액", "N/A")
            
            with col3:
                week_52_high = company_info.get('fiftyTwoWeekHigh', None)
                if week_52_high and not pd.isna(week_52_high):
                    st.metric("52주 최고", f"${float(week_52_high):.2f}")
                else:
                    st.metric("52주 최고", "N/A")
            
            with col4:
                week_52_low = company_info.get('fiftyTwoWeekLow', None)
                if week_52_low and not pd.isna(week_52_low):
                    st.metric("52주 최저", f"${float(week_52_low):.2f}")
                else:
                    st.metric("52주 최저", "N/A")
            
            # 상세 정보
            st.subheader("📌 기본 정보")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**회사명**: {company_info.get('longName', 'N/A')}")
                st.write(f"**업종**: {company_info.get('industry', 'N/A')}")
                st.write(f"**섹터**: {company_info.get('sector', 'N/A')}")
                st.write(f"**국가**: {company_info.get('country', 'N/A')}")
            
            with col2:
                employees = company_info.get('fullTimeEmployees', None)
                if employees and not pd.isna(employees):
                    try:
                        st.write(f"**직원 수**: {int(employees):,}")
                    except:
                        st.write(f"**직원 수**: {employees}")
                else:
                    st.write(f"**직원 수**: N/A")
                st.write(f"**홈페이지**: {company_info.get('website', 'N/A')}")
                st.write(f"**거래소**: {company_info.get('exchange', 'N/A')}")
            
            # 회사 설명
            st.subheader("📝 회사 소개")
            summary = company_info.get('longBusinessSummary', None)
            if summary and summary != 'N/A':
                st.write(summary)
            else:
                st.info("회사 소개 정보가 없습니다.")
        
        # ============ TAB 2: 주가 차트 ============
        with tab2:
            st.subheader("📈 주가 차트 분석")
            
            # 설정 - 탭 방식으로 기간 선택
            tab_preset, tab_custom = st.tabs(["⏱️ 기간 선택", "📅 날짜 직접 선택"])
            
            with tab_preset:
                st.write("**기본 기간 선택:**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    period = st.selectbox('기간', ['1개월', '3개월', '6개월', '1년', '5년', '10년'], key='period')
                
                with col2:
                    ma_20 = st.checkbox('20일 이동평균선', value=True)
                
                with col3:
                    ma_50 = st.checkbox('50일 이동평균선', value=True)
                
                period_map = {
                    '1개월': '1mo',
                    '3개월': '3mo',
                    '6개월': '6mo',
                    '1년': '1y',
                    '5년': '5y',
                    '10년': '10y'
                }
                
                # 데이터 수집
                st.info(f"📊 {ticker} 데이터 로딩 중...")
                data, error_msg = safe_download(ticker, period=period_map[period])
                
                use_custom = False
            
            with tab_custom:
                st.write("**날짜 범위 직접 선택:**")
                col1, col2 = st.columns(2)
                
                # 기본값: 1년 전부터 오늘까지
                end_date = datetime.now().date()
                start_date = (datetime.now() - timedelta(days=365)).date()
                
                with col1:
                    start_date = st.date_input(
                        '시작 날짜',
                        value=start_date,
                        key='start_date'
                    )
                
                with col2:
                    end_date = st.date_input(
                        '종료 날짜',
                        value=end_date,
                        key='end_date'
                    )
                
                # 이동평균선 옵션
                col1, col2 = st.columns(2)
                with col1:
                    ma_20 = st.checkbox('20일 이동평균선', value=True, key='ma20_custom')
                with col2:
                    ma_50 = st.checkbox('50일 이동평균선', value=True, key='ma50_custom')
                
                # 데이터 수집
                st.info(f"📊 {ticker} 데이터 로딩 중 ({start_date} ~ {end_date})...")
                data, error_msg = safe_download(ticker, start_date=start_date, end_date=end_date)
                
                use_custom = True
            
            # 데이터 표시
            if error_msg or data is None:
                st.error(f"❌ 캔들 그래프 데이터 로드 실패")
                st.error(f"**오류 내용**: {error_msg}")
                
                with st.expander("🔧 디버깅 정보 및 해결 방법"):
                    st.write(f"**입력된 티커**: {ticker}")
                    if use_custom:
                        st.write(f"**선택된 기간**: {start_date} ~ {end_date}")
                    else:
                        st.write(f"**선택된 기간**: {period}")
                    st.write(f"**시스템 시간**: {datetime.now()}")
                    
                    st.markdown("""
                    ### 해결 방법:
                    1. **티커 확인**: 정확한 형식인지 확인
                       - 미국 종목: AAPL, MSFT, GOOGL 등
                       - 한국 종목: 005930.KS (삼성전자) 등
                       - https://finance.yahoo.com 에서 확인
                    
                    2. **기간 변경**: 1개월이 아닌 더 긴 기간 시도
                    
                    3. **네트워크 확인**: 인터넷 연결 상태 확인
                    
                    4. **캐시 초기화**: 브라우저 새로고침 (Ctrl+F5)
                    """)
            else:
                # 데이터 확인
                st.success(f"✅ 데이터 로드 완료 ({len(data)}개 거래일)")
                
                # 데이터 정보 표시
                with st.expander("📋 데이터 정보"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("데이터 행 수", len(data))
                    with col2:
                        st.metric("시작 날짜", str(data.index[0].date()))
                    with col3:
                        st.metric("종료 날짜", str(data.index[-1].date()))
                    with col4:
                        st.metric("컬럼", ', '.join(data.columns))
                
                try:
                    # 데이터 정제
                    data_clean = data.dropna(subset=['Open', 'High', 'Low', 'Close']).copy()
                    
                    if len(data_clean) == 0:
                        st.error("❌ 유효한 주가 데이터가 없습니다.")
                    else:
                        st.success(f"✅ {len(data_clean)}개의 유효한 데이터")
                        
                        # 데이터 타입 명시적 변환
                        data_clean['Open'] = pd.to_numeric(data_clean['Open'], errors='coerce')
                        data_clean['High'] = pd.to_numeric(data_clean['High'], errors='coerce')
                        data_clean['Low'] = pd.to_numeric(data_clean['Low'], errors='coerce')
                        data_clean['Close'] = pd.to_numeric(data_clean['Close'], errors='coerce')
                        
                        # 최종 NaN 제거
                        data_clean = data_clean.dropna(subset=['Open', 'High', 'Low', 'Close'])
                        
                        if len(data_clean) > 0:
                            # Plotly 캔들스틱 차트
                            fig = go.Figure(data=[go.Candlestick(
                                x=data_clean.index,
                                open=data_clean['Open'].values,
                                high=data_clean['High'].values,
                                low=data_clean['Low'].values,
                                close=data_clean['Close'].values,
                                name='주가'
                            )])
                            
                            # 이동평균선 추가
                            if ma_20 and len(data_clean) >= 20:
                                ma20 = data_clean['Close'].rolling(window=20).mean()
                                fig.add_trace(go.Scatter(
                                    x=data_clean.index, y=ma20,
                                    mode='lines', name='20일 MA',
                                    line=dict(color='orange', width=2)
                                ))
                            
                            if ma_50 and len(data_clean) >= 50:
                                ma50 = data_clean['Close'].rolling(window=50).mean()
                                fig.add_trace(go.Scatter(
                                    x=data_clean.index, y=ma50,
                                    mode='lines', name='50일 MA',
                                    line=dict(color='blue', width=2)
                                ))
                            
                            fig.update_layout(
                                title=f'{ticker} 주가 차트',
                                yaxis_title='가격 ($)',
                                xaxis_title='날짜',
                                template='plotly_white',
                                height=600,
                                hovermode='x unified',
                                xaxis_rangeslider_visible=False
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 기술 지표
                            st.subheader("📊 기술 지표")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                try:
                                    current = float(data_clean['Close'].iloc[-1])
                                    st.metric("현재가", f"${current:.2f}")
                                except:
                                    st.metric("현재가", "N/A")
                            
                            with col2:
                                try:
                                    change = float(data_clean['Close'].iloc[-1] - data_clean['Close'].iloc[0])
                                    change_pct = float((change / data_clean['Close'].iloc[0] * 100))
                                    st.metric("변화", f"${change:.2f}", f"{change_pct:.2f}%")
                                except:
                                    st.metric("변화", "N/A")
                            
                            with col3:
                                try:
                                    volume = int(data_clean['Volume'].iloc[-1])
                                    st.metric("거래량", f"{volume:,}")
                                except:
                                    st.metric("거래량", "N/A")
                            
                            with col4:
                                try:
                                    avg_price = float(data_clean['Close'].mean())
                                    st.metric("평균 가격", f"${avg_price:.2f}")
                                except:
                                    st.metric("평균 가격", "N/A")
                            
                            # 최근 데이터 테이블
                            st.subheader("📋 최근 데이터 (최근 10거래일)")
                            display_data = data_clean.tail(10).iloc[::-1].copy()
                            for col in display_data.columns:
                                if display_data[col].dtype in ['float64', 'float32']:
                                    display_data[col] = display_data[col].round(2)
                            st.dataframe(display_data, use_container_width=True)
                        else:
                            st.error("❌ 정제 후 데이터가 없습니다.")
                
                except Exception as e:
                    st.error(f"❌ 차트 생성 오류: {str(e)}")
                    with st.expander("상세 오류"):
                        st.write(f"```\n{str(e)}\n```")
                    st.info("다른 기간을 선택하거나 다시 시도해주세요.")
        
        # ============ TAB 3: 배당 분석 ============
        with tab3:
            st.subheader("💰 배당금 분석")
            
            dividends = info.dividends
            
            if len(dividends) > 0:
                # 최근 배당금 테이블
                st.subheader("📋 최근 배당 내역")
                
                div_df = pd.DataFrame({
                    '날짜': dividends.index,
                    '배당금 ($)': dividends.values
                }).sort_index(ascending=False)
                
                # 배당금 반올림
                div_df['배당금 ($)'] = pd.to_numeric(div_df['배당금 ($)'], errors='coerce').round(4)
                
                st.dataframe(div_df.head(20), use_container_width=True)
                
                # 배당금 시각화
                st.subheader("📊 배당금 추이")
                
                try:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=dividends.index,
                        y=dividends.values,
                        marker_color='lightblue',
                        name='배당금'
                    ))
                    
                    fig.update_layout(
                        title=f'{ticker} 배당금 추이',
                        yaxis_title='배당금 ($)',
                        xaxis_title='날짜',
                        template='plotly_white',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"배당금 차트 오류: {str(e)}")
                
                # 배당 통계
                st.subheader("📈 배당 통계")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    try:
                        recent_div = float(dividends.iloc[-1])
                        st.metric("최근 배당금", f"${recent_div:.4f}")
                    except:
                        st.metric("최근 배당금", "N/A")
                
                with col2:
                    try:
                        avg_div = float(dividends.mean())
                        st.metric("평균 배당금", f"${avg_div:.4f}")
                    except:
                        st.metric("평균 배당금", "N/A")
                
                with col3:
                    try:
                        max_div = float(dividends.max())
                        st.metric("최대 배당금", f"${max_div:.4f}")
                    except:
                        st.metric("최대 배당금", "N/A")
                
                with col4:
                    div_count = len(dividends)
                    st.metric("배당 횟수", div_count)
                
                # 배당 성장률
                if len(dividends) > 12:
                    try:
                        recent_12 = float(dividends.iloc[-12:].mean())
                        if len(dividends) > 24:
                            previous_12 = float(dividends.iloc[-24:-12].mean())
                        else:
                            previous_12 = recent_12
                        
                        growth = ((recent_12 - previous_12) / previous_12 * 100) if previous_12 > 0 else 0
                        st.metric("연 배당 성장률 (YoY)", f"{growth:.2f}%")
                    except:
                        st.warning(f"배당 성장률 계산 불가")
                
                # 연간 배당금 합계
                st.subheader("💵 연간 배당금 합계")
                
                try:
                    div_annual = pd.DataFrame({
                        '년도': dividends.index.year,
                        '배당금': dividends.values
                    }).groupby('년도')['배당금'].sum()
                    
                    fig_annual = go.Figure()
                    fig_annual.add_trace(go.Bar(
                        x=div_annual.index,
                        y=div_annual.values,
                        marker_color='lightgreen',
                        name='연간 배당금'
                    ))
                    
                    fig_annual.update_layout(
                        title=f'{ticker} 연간 배당금',
                        yaxis_title='배당금 ($)',
                        xaxis_title='년도',
                        template='plotly_white',
                        height=400
                    )
                    
                    st.plotly_chart(fig_annual, use_container_width=True)
                except Exception as e:
                    st.error(f"연간 배당금 시각화 오류: {str(e)}")
                
            else:
                st.info("이 종목에 배당금 기록이 없습니다.")
        
        # ============ TAB 4: 회사 정보 ============
        with tab4:
            st.subheader("🏢 회사 정보")
            
            company_info = info.info
            
            # 기본 정보
            st.subheader("📌 기본 정보")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**회사명**: {company_info.get('longName', 'N/A')}")
                st.write(f"**국가**: {company_info.get('country', 'N/A')}")
                st.write(f"**업종**: {company_info.get('industry', 'N/A')}")
                st.write(f"**섹터**: {company_info.get('sector', 'N/A')}")
                st.write(f"**거래소**: {company_info.get('exchange', 'N/A')}")
            
            with col2:
                employees = company_info.get('fullTimeEmployees', None)
                if employees and not pd.isna(employees):
                    try:
                        st.write(f"**직원 수**: {int(employees):,}")
                    except:
                        st.write(f"**직원 수**: {employees}")
                else:
                    st.write(f"**직원 수**: N/A")
                st.write(f"**홈페이지**: {company_info.get('website', 'N/A')}")
                st.write(f"**도시**: {company_info.get('city', 'N/A')}")
                st.write(f"**주소**: {company_info.get('state', 'N/A')}")
            
            # 재무 지표
            st.subheader("💼 재무 지표")
            
            financial_metrics = {
                '시가총액': company_info.get('marketCap'),
                '총 자산': company_info.get('totalAssets'),
                '총 부채': company_info.get('totalDebt'),
                'P/E 비율': company_info.get('trailingPE'),
                'P/B 비율': company_info.get('priceToBook'),
                '부채비율': company_info.get('debtToEquity'),
                'ROE': company_info.get('returnOnEquity'),
                'ROA': company_info.get('returnOnAssets'),
                '배당 수익률': company_info.get('dividendYield'),
                '베타': company_info.get('beta')
            }
            
            metric_display = []
            for key, value in financial_metrics.items():
                try:
                    if value is None or pd.isna(value):
                        metric_display.append([key, 'N/A'])
                    elif isinstance(value, str):
                        metric_display.append([key, value])
                    elif isinstance(value, (int, float)):
                        metric_display.append([key, format_number(float(value))])
                    else:
                        metric_display.append([key, str(value)])
                except:
                    metric_display.append([key, 'Error'])
            
            metric_df = pd.DataFrame(metric_display, columns=['지표', '값'])
            st.dataframe(metric_df, use_container_width=True)
            
            # 회사 설명
            st.subheader("📝 회사 소개")
            summary = company_info.get('longBusinessSummary', None)
            if summary and summary != 'N/A':
                st.write(summary)
            else:
                st.info("회사 소개 정보가 없습니다.")
        
        # ============ TAB 5: 재무제표 ============
        with tab5:
            st.subheader("📑 재무제표")
            
            statement_type = st.selectbox(
                '재무제표 선택',
                ['손익계산서', '대차대조표', '현금흐름표'],
                key='statement'
            )
            
            period_type = st.radio('기간 선택', ['분기별', '연간'], horizontal=True)
            
            try:
                if statement_type == '손익계산서':
                    st.subheader("📈 손익계산서 (Income Statement)")
                    
                    if period_type == '분기별':
                        income = info.quarterly_income_stmt
                    else:
                        income = info.income_stmt
                    
                    if not income.empty:
                        # 숫자 변환
                        income_display = income.copy()
                        for col in income_display.columns:
                            income_display[col] = pd.to_numeric(income_display[col], errors='coerce')
                        
                        st.dataframe(income_display, use_container_width=True)
                        
                        # 핵심 지표 시각화
                        if 'Total Revenue' in income.index:
                            st.subheader("💹 주요 지표 추이")
                            
                            fig = go.Figure()
                            
                            try:
                                revenue_values = pd.to_numeric(income.loc['Total Revenue'], errors='coerce')
                                fig.add_trace(go.Scatter(
                                    x=range(len(income.columns)),
                                    y=revenue_values.values,
                                    mode='lines+markers',
                                    name='총 수익'
                                ))
                            except:
                                pass
                            
                            if 'Net Income' in income.index:
                                try:
                                    net_income_values = pd.to_numeric(income.loc['Net Income'], errors='coerce')
                                    fig.add_trace(go.Scatter(
                                        x=range(len(income.columns)),
                                        y=net_income_values.values,
                                        mode='lines+markers',
                                        name='순 수익'
                                    ))
                                except:
                                    pass
                            
                            fig.update_layout(
                                title='수익 추이',
                                xaxis_title='기간',
                                yaxis_title='금액 ($)',
                                template='plotly_white',
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("손익계산서 데이터를 찾을 수 없습니다.")
                
                elif statement_type == '대차대조표':
                    st.subheader("🏦 대차대조표 (Balance Sheet)")
                    
                    if period_type == '분기별':
                        balance = info.quarterly_balance_sheet
                    else:
                        balance = info.balance_sheet
                    
                    if not balance.empty:
                        balance_display = balance.copy()
                        for col in balance_display.columns:
                            balance_display[col] = pd.to_numeric(balance_display[col], errors='coerce')
                        
                        st.dataframe(balance_display, use_container_width=True)
                    else:
                        st.info("대차대조표 데이터를 찾을 수 없습니다.")
                
                elif statement_type == '현금흐름표':
                    st.subheader("💵 현금흐름표 (Cash Flow Statement)")
                    
                    if period_type == '분기별':
                        cashflow = info.quarterly_cashflow
                    else:
                        cashflow = info.cashflow
                    
                    if not cashflow.empty:
                        cashflow_display = cashflow.copy()
                        for col in cashflow_display.columns:
                            cashflow_display[col] = pd.to_numeric(cashflow_display[col], errors='coerce')
                        
                        st.dataframe(cashflow_display, use_container_width=True)
                    else:
                        st.info("현금흐름표 데이터를 찾을 수 없습니다.")
            
            except Exception as e:
                st.error(f"재무제표 오류: {str(e)}")
        
        # ============ TAB 6: 포트폴리오 ============
        with tab6:
            st.subheader("💼 포트폴리오 - 투자 수익률 계산")
            
            st.write("### 📝 매매 기록 입력")
            
            # 매매 방식 선택
            buy_method = st.radio("매수 가격 입력 방식", ["💰 직접 입력", "📅 종가 자동 조회"], horizontal=True, key="buy_method")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                buy_ticker = st.text_input("종목 티커", placeholder="AAPL", key="buy_ticker_input")
            
            with col2:
                buy_date = st.date_input("매수 날짜", key="buy_date_input")
            
            if buy_method == "💰 직접 입력":
                with col3:
                    buy_price = st.number_input("매수 가격 ($)", min_value=0.0, step=0.01, key="buy_price_input")
                
                manual_price = buy_price
                
                # 추가 버튼
                col_btn, col_empty = st.columns([1, 4])
                with col_btn:
                    if st.button("➕ 추가", use_container_width=True, key="add_portfolio_btn"):
                        if buy_ticker and manual_price > 0:
                            with col4:
                                quantity = st.number_input("주식 수", min_value=1, step=1, key="quantity_input_1")
                            
                            if quantity > 0:
                                try:
                                    # 현재 가격 가져오기
                                    current_ticker = yf.Ticker(buy_ticker)
                                    current_price = current_ticker.info.get('currentPrice', None)
                                    
                                    if current_price and not pd.isna(current_price):
                                        current_price = float(current_price)
                                        entry = {
                                            '종목': buy_ticker,
                                            '매수날짜': buy_date,
                                            '매수가': manual_price,
                                            '현재가': current_price,
                                            '수량': quantity,
                                            '매수액': manual_price * quantity,
                                            '현재가치': current_price * quantity,
                                            '수익/손실': (current_price - manual_price) * quantity,
                                            '수익률(%)': ((current_price - manual_price) / manual_price * 100)
                                        }
                                        st.session_state.portfolio_data.append(entry)
                                        st.success(f"✅ {buy_ticker} 매매 기록이 추가되었습니다!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {buy_ticker}의 현재 가격을 가져올 수 없습니다.")
                                except Exception as e:
                                    st.error(f"❌ 오류: {str(e)}")
                            else:
                                st.warning("⚠️ 주식 수를 입력해주세요.")
                        else:
                            st.warning("⚠️ 종목 티커와 매수 가격을 입력해주세요.")
                
                with col4:
                    st.write("")  # 빈 공간
            
            else:  # 종가 자동 조회
                with col3:
                    if st.button("🔍 종가 조회", use_container_width=True, key="closing_price_btn"):
                        if buy_ticker:
                            closing_price = get_closing_price_on_date(buy_ticker, buy_date)
                            if closing_price is not None and closing_price > 0:
                                st.session_state.closing_price = closing_price
                                st.session_state.closing_price_found = True
                                st.success(f"✅ {buy_date}의 종가: ${closing_price:.2f}")
                            else:
                                st.error(f"❌ {buy_date}의 종가를 조회할 수 없습니다.")
                        else:
                            st.warning("⚠️ 종목 티커를 입력해주세요.")
                
                with col4:
                    quantity = st.number_input("주식 수", min_value=1, step=1, key="quantity_input_2")
                
                # 종가 조회 결과 표시
                if st.session_state.closing_price_found and st.session_state.closing_price > 0:
                    st.info(f"📍 조회된 매수 가격: **${st.session_state.closing_price:.2f}**")
                    
                    # 추가 버튼
                    col_btn, col_empty = st.columns([1, 4])
                    with col_btn:
                        if st.button("➕ 추가", use_container_width=True, key="add_portfolio_auto_btn"):
                            if buy_ticker and st.session_state.closing_price > 0 and quantity > 0:
                                try:
                                    # 현재 가격 가져오기
                                    current_ticker = yf.Ticker(buy_ticker)
                                    current_price = current_ticker.info.get('currentPrice', None)
                                    
                                    if current_price and not pd.isna(current_price):
                                        current_price = float(current_price)
                                        entry = {
                                            '종목': buy_ticker,
                                            '매수날짜': buy_date,
                                            '매수가': st.session_state.closing_price,
                                            '현재가': current_price,
                                            '수량': quantity,
                                            '매수액': st.session_state.closing_price * quantity,
                                            '현재가치': current_price * quantity,
                                            '수익/손실': (current_price - st.session_state.closing_price) * quantity,
                                            '수익률(%)': ((current_price - st.session_state.closing_price) / st.session_state.closing_price * 100)
                                        }
                                        st.session_state.portfolio_data.append(entry)
                                        st.success(f"✅ {buy_ticker} 매매 기록이 추가되었습니다!")
                                        st.session_state.closing_price = 0.0
                                        st.session_state.closing_price_found = False
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {buy_ticker}의 현재 가격을 가져올 수 없습니다.")
                                except Exception as e:
                                    st.error(f"❌ 오류: {str(e)}")
                            else:
                                st.warning("⚠️ 모든 필드를 올바르게 입력해주세요.")
            
            # 포트폴리오 데이터 표시
            st.write("---")
            
            if len(st.session_state.portfolio_data) > 0:
                st.write("### 📊 포트폴리오 현황")
                
                # 데이터프레임 생성
                portfolio_df = pd.DataFrame(st.session_state.portfolio_data)
                
                # 포맷팅
                display_df = portfolio_df.copy()
                currency_cols = ['매수가', '현재가', '매수액', '현재가치', '수익/손실']
                for col in currency_cols:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
                display_df['수익률(%)'] = display_df['수익률(%)'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(display_df, use_container_width=True)
                
                # 포트폴리오 통계
                st.write("### 💰 포트폴리오 통계")
                
                total_investment = portfolio_df['매수액'].sum()
                total_current_value = portfolio_df['현재가치'].sum()
                total_profit_loss = portfolio_df['수익/손실'].sum()
                total_return_pct = (total_profit_loss / total_investment * 100) if total_investment > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("총 투자액", f"${total_investment:,.2f}")
                
                with col2:
                    st.metric("현재 자산 가치", f"${total_current_value:,.2f}")
                
                with col3:
                    st.metric("총 수익/손실", f"${total_profit_loss:,.2f}")
                
                with col4:
                    st.metric("총 수익률", f"{total_return_pct:.2f}%")
                
                # 종목별 수익률 차트
                st.write("### 📈 종목별 수익률")
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=display_df['종목'],
                        y=portfolio_df['수익률(%)'],
                        marker_color=['green' if x >= 0 else 'red' for x in portfolio_df['수익률(%)']]
                    )
                ])
                
                fig.update_layout(
                    title='종목별 수익률',
                    yaxis_title='수익률 (%)',
                    xaxis_title='종목',
                    template='plotly_white',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 매수액 vs 현재가치 비교
                st.write("### 💵 매수액 vs 현재 가치")
                
                fig = go.Figure(data=[
                    go.Bar(name='매수액', x=display_df['종목'], y=portfolio_df['매수액'], marker_color='lightblue'),
                    go.Bar(name='현재가치', x=display_df['종목'], y=portfolio_df['현재가치'], marker_color='lightgreen')
                ])
                
                fig.update_layout(
                    title='매수액 vs 현재 가치',
                    yaxis_title='금액 ($)',
                    xaxis_title='종목',
                    template='plotly_white',
                    height=400,
                    barmode='group'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 삭제 옵션
                st.write("### 🗑️ 기록 관리")
                if st.button("🗑️ 전체 기록 삭제", use_container_width=True, key="delete_portfolio_btn"):
                    st.session_state.portfolio_data = []
                    st.session_state.closing_price = 0.0
                    st.session_state.closing_price_found = False
                    st.success("✅ 모든 기록이 삭제되었습니다!")
                    st.rerun()
            else:
                st.info("📌 위에서 매매 기록을 입력하면 포트폴리오가 표시됩니다. (현재: 비어있음)")
    
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.info("올바른 종목 티커를 입력해주세요. 예: AAPL, 005930.KS")

else:
    st.info("🔍 왼쪽 사이드바에서 종목 티커를 입력하세요.")
    st.markdown("""
    ### 사용 예시:
    - **미국 종목**: AAPL, MSFT, GOOGL, TSLA, AMZN 등
    - **한국 종목**: 005930.KS (삼성전자), 000660.KS (SK하이닉스), 207940.KS (삼성바이오) 등
    - **암호화폐**: BTC-USD (비트코인), ETH-USD (이더리움)
    - **환율**: EURUSD=X (유로/달러)
    
    ### 주의사항:
    - 정확한 티커를 입력해주세요
    - 야후 파이낸스에서 지원하는 종목만 조회 가능합니다
    - 인터넷 연결을 확인하세요
    """)
