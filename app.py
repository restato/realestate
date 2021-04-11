import streamlit as st
import pandas as pd
import altair as alt

from datetime import datetime, time
from utils import get_hoga
from utils import EsWrapper
from quries import apt_list

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

column_dict = {'dedicated_area': '전용면적(m2)', 'transaction_date': '거래날짜', 'year_of_construction': '건축년도',
               'floor': '층', 'transaction_amount': '거래금액(억)', 'transaction_year': '거래일자'}

es = EsWrapper()


def raw_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    if 'apt_name' in df.columns:
        df['apt_name'] = df['apt_name'].apply(
            lambda x: str(x) + "\t")  # fix bug for display as tabl
    if 'transaction_amount' in df.columns:
        df['transaction_amount'] = df['transaction_amount'].astype(object)
        df['transaction_amount'] = df['transaction_amount'].apply(
            lambda x: round(x / 10000, 1))
        # df['transaction_amount'] = df['transaction_amount'].apply(
        # lambda x: round(x, 1))

    # df['transaction_amount'] = df['transaction_amount'].astype(
    # float).apply(lambda x: round(x / 10000, 2))
    # 2016-05-26 0:00:00
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(
            df['transaction_date'], format="%Y-%m-%d %H:%M:%S").dt.date
    if 'transaction_year' in df.columns:
        df['transaction_year'] = pd.to_datetime(
            df['transaction_year'], format="%Y").dt.date
        # df['transaction_year'] = df['transaction_year'].astype(int)
    if 'year_of_construction' in df.columns:
        df['year_of_construction'] = df['year_of_construction'].astype(int)
    if 'floor' in df.columns:
        df['floor'] = df['floor'].astype(int)
    if 'dedicated_area' in df.columns:
        df['dedicated_area'] = df['dedicated_area'].apply(lambda x: round(x))
        df['dedicated_area'] = df['dedicated_area'].astype(object)
        df['dedicated_area'] = df['dedicated_area'].apply(
            lambda x: str(x))  # fix bug for display as tabl

    return df


def filtering(df: pd.DataFrame) -> pd.DataFrame:
    start_dt = st.date_input(
        "시작:",
        datetime(1988, 7, 6))
    end_dt = st.date_input(
        "종료:",
        datetime.now().date())
    if end_dt > datetime.now().date():
        st.warning('종료 날짜를 현재 날짜보다 이전으로 입력해주세요.')

    year_of_construction = st.slider(
        "건축년도:",
        value=(1992, 2007),
        min_value=1988,
        max_value=2020
    )
    df = df[(df['year_of_construction'] >= int(year_of_construction[0])) &
            (df['year_of_construction'] <= int(year_of_construction[1]))]
    df = df[(df['transaction_date'] >= start_dt)
            & (df['transaction_date'] <= end_dt)]
    return df


def slider():
    '''Slider'''
    st.sidebar.write('')  # Line break
    # st.sidebar.header('메뉴')
    side_menu_selectbox = st.sidebar.radio(
        '메뉴', ('홈', '통계', '세금', '뉴스'))  # , '관심목록'))

    if side_menu_selectbox == '홈':
        main()
    elif side_menu_selectbox == '통계':
        statistic_home()
    elif side_menu_selectbox == '세금':
        tax_home()
    elif side_menu_selectbox == '뉴스':
        news_home()
    elif side_menu_selectbox == '관심목록':
        fav_home()


def tax_home():
    st.markdown("# 세금 💸")


def news_home():
    st.markdown("# 늬우스 🔈")


def statistic_home():
    st.markdown("# 토옹계")


def fav_home():
    st.markdown("# 픽미픽미 🍢")

    apt_code_dict = {'광교센트럴파크60단지': 138183, '광교센트럴타운62단지': 136913, '광교마을45단지': 137232,
                     '광교마을40단지': 137233, '광교호반마을21단지': 135549, '광교호반마을22단지': 135550}

    for k, v in apt_code_dict.items():
        df, total_count = get_hoga(v, n=3)
        st.markdown(
            f'### [{k}](https://new.land.naver.com/complexes/{v}?), {total_count}개의 매물')
        st.dataframe(df)
    st.markdown("**NOTE**: 네이버에서 제공하는 데이터로 사용, 더 자세한 내용은 네이버 부동산에서 확인")


def main():
    @ st.cache
    def get_local_data(filename):
        # use local data for debug
        df = pd.read_csv(filename)
        return raw_preprocessing(df)

    @ st.cache
    def get_apt_list(body):
        return es.search(body)

    @ st.cache(allow_output_mutation=True)
    def get_remote_data(body):
        df = es.search(body)
        return raw_preprocessing(df)

    st.title('🏠 사고시펑?')
    st.markdown("""
        📢 공지
        * 현재는 ** 분당구**만 구성했습니다.
        * 평소에 궁금했던 부동산 관련한 내용을 차트와 글로 채워갈 계획입니다.
        * 아이디어/문의는 `direcision@gmail.com`로 ✉️ 주세요.
        """)

    apts = get_apt_list(apt_list())
    apts = apts['key'].unique().tolist()
    st.markdown(f"분당구에는 현재 아파트가 {len(apts)}개 있습니다.")

    # sigungu_info
    # floor_list = df['floor'].unique().tolist()
    # st.markdown(f"가장 높은 층은 {max(floor_list)}, 가장 낮은 층은 {min(floor_list)}")
    # st.markdown(f"{df['dedicated_area'].unique().tolist()}")

    # APT INFO
    apt_name = st.selectbox(
        "👇 아파트를 선택해주세요.", apts)

    data_load_state = st.text('데이터를 조회하고 있습니다.🍞')
    body = {"from": 0, "size": 10000, "query": {
        "match": {"apt_name": apt_name}}}
    df = get_remote_data(body)
    data_load_state.text("데이터 불러오기 완료")

    df = df[['transaction_date', 'floor', 'dedicated_area',
             'transaction_amount', 'transaction_year']]
    # Chart #1
    st.markdown("""
        # 우리 옆집은 얼마 🤫

        * 문득 궁금했습니다. 지금 얼마에 사서 살고 있는걸까?
        * 층/전용면적(m2) 단위로 언제 얼마에 매매했는지 차트에 나타냈습니다.
        * 차트에서 흰색은 거래 이력이 없음을 의미합니다.
                """)

    col1, col2 = st.beta_columns([1, 2])
    latest_df = df[['transaction_date', 'floor', 'dedicated_area', 'transaction_amount']].sort_values('transaction_date', ascending=True).groupby(
        ['floor', 'dedicated_area']).tail(1)
    latest_df['dedicated_area'] = latest_df['dedicated_area'].astype(float)
    latest_df = latest_df.sort_values(
        ['floor', 'dedicated_area'], ascending=False)
    latest_df = latest_df.rename(
        columns=column_dict)

    # https://stackoverflow.com/questions/55907130/how-to-force-altair-to-order-heatmaprect-on-a-specific-axis
    c = alt.Chart(latest_df).mark_rect().encode(
        alt.X(column_dict['dedicated_area'] + ':O'),
        alt.Y(column_dict['floor'] + ':O',
              sort=alt.EncodingSortField(field='order', order='ascending')),
        size=column_dict['transaction_amount'],
        color=column_dict['transaction_amount'] + ':Q',
        tooltip=[column_dict['transaction_date'],
                 column_dict['floor'],
                 column_dict['dedicated_area'],
                 column_dict['transaction_amount']])
    col1.altair_chart(c)
    col2.dataframe(latest_df)

    # Chart #1
    st.markdown("""
                # 연도별 평균거래금액
                """)

    col1, col2 = st.beta_columns([3, 1])
    df['transaction_amount'] = df['transaction_amount'].apply(
        lambda x: float(x))
    chart = df[['transaction_year', 'transaction_amount']
               ].groupby('transaction_year').mean()
    chart = chart.fillna(0)
    chart = chart.rename(columns=column_dict)
    chart.columns = [x for x in chart.columns]
    col1.line_chart(chart)
    col2.dataframe(chart)
    st.markdown("""**Note**: X축은 년도, Y축은 거래금액""")


def run_the_app():
    slider()


if __name__ == "__main__":
    run_the_app()
