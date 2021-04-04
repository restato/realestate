import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, time

column_dict = {'dedicated_area': '전용면적(m2)', 'transaction_date': '거래날짜',
               'floor': '층', 'transaction_amount': '거래금액(억)', 'transaction_year': '거래일자'}


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
    st.sidebar.header('Navigation')
    side_menu_selectbox = st.sidebar.radio(
        '메뉴', ('홈', '통계'))

    if side_menu_selectbox == '홈':
        main()
    elif side_menu_selectbox == '통계':
        statistic_ui()


def statistic_ui():
    st.write("statistic")


def main():

    @st.cache
    def get_data(filename):
        df = pd.read_csv(filename)
        return raw_preprocessing(df)

    st.title('🏠 사고시펑?')
    st.markdown("""
        📢 공지
        * 현재는 **분당구**만 구성했습니다.
        * 평소에 궁금했던 부동산 관련한 내용을 차트와 글로 채워갈 계획입니다.
        * 아이디어/문의는 `direcision@gmail.com`로 ✉️ 주세요.
        """)
    df = get_data('./data_out/price_dedicatedarea_floor/41135.csv')
    # df = filtering(df)
    df = df.set_index('apt_name')
    df = df.sort_index()
    st.markdown(f"분당구에는 현재 아파트가 {len(df.index.unique().tolist())}개 있습니다.")

    # sigungu_info
    # floor_list = df['floor'].unique().tolist()
    # st.markdown(f"가장 높은 층은 {max(floor_list)}, 가장 낮은 층은 {min(floor_list)}")
    # st.markdown(f"{df['dedicated_area'].unique().tolist()}")

    # APT INFO
    apt_name = st.selectbox(
        "👇 아파트를 선택해주세요.", df.index.unique().tolist())

    if apt_name in df.index:
        df = df.loc[apt_name]
    else:
        st.error(f'{apt_name}은 존재하지 않습니다.')

    # Chart #1
    st.markdown("""
        # 우리 옆집은 얼마 🤫
     
        * 문득 궁금했습니다. 지금 얼마에 사서 살고 있는걸까?
        * 층/전용면적(m2) 단위로 언제 얼마에 매매했는지 차트에 나타냈습니다.
        * 차트에서 흰색은 거래 이력이 없음을 의미합니다.
                """)

    col1, col2 = st.beta_columns([1, 2])
    latest_df = df.loc[[apt_name]][['transaction_date', 'floor', 'dedicated_area', 'transaction_amount']].sort_values('transaction_date', ascending=True).groupby(
        ['floor', 'dedicated_area']).tail(1)
    latest_df['dedicated_area'] = latest_df['dedicated_area'].astype(object)
    latest_df = latest_df.sort_values('floor', ascending=False)
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

    df['transaction_amount'] = df['transaction_amount'].apply(
        lambda x: str(round(x, 1)))
    df = df.reset_index(drop=True)
    df = df.assign(hack='').set_index('hack')
    df = df.rename(columns=column_dict)
    col2.dataframe(df)

    # Chart #1
    df = get_data('./data_out/apt_amount_per_year/41135.csv')
    df = df.set_index('apt_name')
    df = df.loc[apt_name]
    st.markdown("""
                # 연도별 평균거래금액

                * 연도별 거래금액 평균을 나타냈습니다.

                """)

    col1, col2 = st.beta_columns([3, 1])
    chart = df[['transaction_year', 'transaction_amount']].groupby([
        'apt_name', 'transaction_year'
    ]).mean().reset_index()
    chart = chart.pivot(index='transaction_year',
                        columns='apt_name', values='transaction_amount')
    # st.dataframe(chart)
    chart = chart.fillna(0)
    chart.columns = [x for x in chart.columns]
    col1.line_chart(chart)

    df = df.reset_index(drop=True)
    df['transaction_year'] = df['transaction_year'].apply(
        lambda x: str(x).split('-')[0])
    df['transaction_amount'] = df['transaction_amount'].apply(
        lambda x: str(round(x, 1)))
    df = df.assign(hack='').set_index('hack')
    df = df.rename(columns=column_dict)
    col2.dataframe(df)


def run_the_app():
    slider()


if __name__ == "__main__":
    run_the_app()
