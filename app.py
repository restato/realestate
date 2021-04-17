from utils import *
from datetime import datetime, time, date
import streamlit as st
import pandas as pd
import altair as alt
import glob
import queries


st.set_page_config(page_title='부동산', page_icon=':eyeglasses:', layout='wide')

# Horizontal Radio Button
# https://discuss.streamlit.io/t/horizontal-radio-buttons/2114/3
st.write(
    '<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

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
        '메뉴', ('홈', '계산기', '통계', '신고가', '세금', '뉴스'))  # , '관심목록'))

    if side_menu_selectbox == '홈':
        calculator_home()  # main()
    elif side_menu_selectbox == '계산기':
        calculator_home()
    elif side_menu_selectbox == '통계':
        statistic_home()
    elif side_menu_selectbox == '신고가':
        new_high_home()
    elif side_menu_selectbox == '세금':
        tax_home()
    elif side_menu_selectbox == '뉴스':
        news_home()
    elif side_menu_selectbox == '관심목록':
        fav_home()


def calculator_home():
    st.title("💰계산기")


def new_high_home():
    @ st.cache(allow_output_mutation=True)
    def get_data():
        df = es.search(queries.new_high())
        return df

    df = get_data()
    df['values'] = df['raw_values'].apply(
        lambda x: pd.Series(x['hits']['hits'][0]))[['_source']]
    df = pd.concat([df['key'], df['values'].apply(pd.Series)], axis=1)
    # print(df['transaction_amount'].apply(
    # lambda x: x['hits']['hits'][0]['_source']))
    st.text("신고가")
    st.dataframe(df)


def tax_home():
    st.title('💸 세금')
    filelist = glob.glob('./images/tax/*')
    filelist.sort()
    for filename in filelist:
        st.image(f'{filename}')


def news_home():
    st.header("# 늬우스 🔈", 'news')
    d = st.date_input('start date', datetime.now())
    filelist = glob.glob(f'./images/news/{d}/*')
    filelist.sort()
    for filename in filelist:
        st.image(f'{filename}')


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


def property_home():
    '''
    재산세
    '''
    st.header('재산세 계산 💸', 'property_calculator')
    st.markdown('''
                > 재산세의 [공정시장가액비율](/#news) 60% 입니다.
                ''')
    # https://discuss.streamlit.io/t/how-to-overwrite-the-value-user-input/7771
    price = 100000  # None
    col1, col2 = st.beta_columns(2)
    with col1:
        price = st.text_input(
            '공시가격 (단위: 만원)', price, help='입력하고 엔터를 쳐주세요.', key=1)
    with col2:
        st.markdown('''
            > 👇 에서 내 집 공시가격 확인
            - [공공주택(아파트)](https://www.realtyprice.kr:447/notice/town/nfSiteLink.htm)
            - [단독주택](http://kras.seoul.go.kr/land_info/info/baseInfo/baseInfo.do)
            ''')
    if price is not '':
        st.write(f'공시가격: {get_wonwha_string(int(price) * 10000)}')
    # col1, col2, col3, col4, col5, col6 = st.beta_columns(
    #     (1, 1, 1, 1, 1, 1))
    # with col1:
    #     if st.button('+5억', key=1):
    #         init_price += 50000
    #         price = placeholder.text_input(
    #             '공시가격', value=init_price, help='단위는 만원입니다.', key=1)
    # with col2:
    #     st.button('+1억', key=1)
    #     init_price += 10000
    # with col3:
    #     st.button('+5천만원')
    #     init_price += 5000
    # with col4:
    #     st.button('+1천만원')
    #     init_price += 1000
    # with col5:
    #     st.button('+500만원')
    #     init_price += 500
    # with col6:
    #     st.button('+100만원')
    #     init_price += 100

    col1, col2 = st.beta_columns(2)
    special_case = None
    with col1:
        checkbox = st.checkbox('1세대 1주택')
    with col2:
        if checkbox:
            special_case = 1
            st.markdown('''
                    > 2023년까지 특례 재산세율이 적용 (-0.05%)
                    ''')
        else:
            special_case = -1

       # result
    if (price != '') and (special_case is not None):
        st.markdown("> 계산서 (단위: 원)")
        price = int(price) * 10000
        data = []
        data.append([1, '시가표준액', '', int_to_string_with_comma(price)])
        price = price * 0.6
        data.append([2, '과세표준', '시가표준액 X 공정시장가액비율(60%)',
                    int_to_string_with_comma(price)])

        tax_text = None
        tax_ratio = None
        additional_tax = None
        base_tax = None

        if price <= 6000 * 10000:  # 6천만원 이하이면
            tax_text = '6천만원 이하'
            tax_ratio = 0.1
            additional_tax = 0
            base_tax = 0
        elif price <= 15000 * 10000:  # 1억 5천만원 이하
            tax_text = '1억 5천만원 이하'
            tax_ratio = 0.15
            additional_tax = 6
            base_tax = 6000 * 10000
        elif price <= 30000 * 10000:  # 3억원 이하
            tax_text = '3억 이하'
            tax_ratio = 0.25
            if special_case == 1:
                additional_tax = 120000
            else:
                additional_tax = 195000
            base_tax = 15000 * 10000
        elif price > 30000 * 10000:  # 3억원 초과
            tax_text = '3억 초과'
            tax_ratio = 0.4
            if special_case == 1:
                additional_tax = 420000
            else:
                additional_tax = 570000
            base_tax = 30000 * 10000

        if special_case == 1:
            tax_ratio -= 0.05
            tax_ratio = round(tax_ratio, 2)

        tax = additional_tax + (price-base_tax) * tax_ratio / 100
        desc = None
        if base_tax > 0:
            desc = f'{tax_text}: {get_wonwha_string(additional_tax)} + {get_wonwha_string(base_tax)} 초과금액의 {tax_ratio}%'
        else:
            desc = f'{tax_text}: 과세표준의 {tax_ratio}%'
        data.append([3, '재산세', desc,  int_to_string_with_comma(tax)])
        city_tax = price * 0.14 / 100
        data.append([4, '도시지역분', '과세표준액의 0.14%',
                    int_to_string_with_comma(city_tax)])
        edu_tax = tax * 0.2
        data.append([5, '지방교육세', '재산세액의 20%',
                    int_to_string_with_comma(edu_tax)])
        total_tax = tax + city_tax + edu_tax
        data.append([6, '총납부액', '재산세 + 도시지역분 + 지방교육세',
                    int_to_string_with_comma(total_tax)])

        st.markdown(f'최종 납부해야 하는 세금은 **{get_wonwha_string(total_tax)}** 입니다.')
        df = pd.DataFrame(
            data=data, columns=['순서', '내용', '상세', '금액'])
        df = df.set_index('순서')
        st.table(df)


def possession_home():
    '''
    보유세
    '''

    price = st.text_input('공시가격')
    st.markdown('''
                > 공시가격은 아래에서 확인
                - [단독주택](http://kras.seoul.go.kr/land_info/info/baseInfo/baseInfo.do)
                - [공공주택(아파트)](https://www.realtyprice.kr:447/notice/town/nfSiteLink.htm)
                ''')
    radio = st.radio('대상연도(공정시장가액비율)', ('2020년 (90%)',
                                        '2021년 (95%)', '2022년 (100%)'))
    if radio == '2021년 (95%)':
        ratio = 0.95
    elif radio == '2022년 (100%)':
        ratio = 1.
    elif radio == '2020년 (90%)':
        ratio = 0.9

    st.markdown(
        "> 공정시장가액비율: 재산세 또는 종합부동산세를 산출하기 위해 과세표준을 정하는 데 있어서 공시가격에서 할인을 적용하여 최종 결정되는 과세표준 기준")

    radio = st.radio('정보', ('1세대 1주택자', '1세대 1주택'))
    if radio == '1세대 1주택':
        ratio = 0.95
    elif radio == '1세대 1주택자':
        ratio = 1.

    st.markdown('''
        > 종합부동산세법에서의 1세대 1주택자란 과세기준일 현재
        > * 세대원 중 1인이 주택 한 채를 단독으로 소유한 경우 \n
        > * 부부가 주택 한 채를 공동으로 소유하고 1주택자로 신청한 경우
        '''
                )


def home():
    # row 1
    row1_spacer1, row1_1, row1_spacer2, row1_2, row1_spacer3, row1_3, row1_spacer4 = st.beta_columns(
        (.1, .1, .1, 1, .1, 1, .1))
    row1_1.title('부동산계산기')
    with row1_2:
        st.subheader('보유세 (재산세, 종합부동산세)')
        st.markdown('''
                    > 소유한 재산에 따라 부과되는 지방세로 6월 1일을 기준으로 과세 \n
                    > 재산세는 매년 7월, 9월에 1~2회 분납 \n
                    > 종부세는 매년 12월에 한번 납부 (일정 가격 이상 부동산을 소유하고 있는 사람에게 부과) \n
                    > ㄴ 현재 공시지가 6억원을 넘는 경우 과세
                    ''')
        st.markdown(read_markdown_file("docs/tax-base.md"),
                    unsafe_allow_html=True)
        df = pd.DataFrame()
        st.table(df)
    with row1_3:
        st.markdown(read_markdown_file("docs/tax-description.md"),
                    unsafe_allow_html=True)


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

    apts = get_apt_list(queries.apt_list())
    apts = apts['key'].unique().tolist()
    st.markdown(f"분당구에는 현재 아파트가 {len(apts)}개 있습니다.")

    # sigungu_info
    # floor_list = df['floor'].unique().tolist()
    # st.markdown(f"가장 높은 층은 {max(floor_list)}, 가장 낮은 층은 {min(floor_list)}")
    # st.markdown(f"{df['dedicated_area'].unique().tolist()}")

    # APT INFO
    apt_name = st.selectbox(
        "👇 아파트를 선택해주세요.", apts)

    body = {"from": 0, "size": 10000, "query": {
        "match": {"apt_name": apt_name}}}
    df = get_remote_data(body)

    df = df[['transaction_date', 'floor', 'dedicated_area',
             'transaction_amount', 'transaction_year']]
    # Chart #1
    st.markdown("""
        # 우리 옆집은 얼마 🤫

        * 문득 궁금했습니다. 지금 얼마에 사서 살고 있는걸까?
        * 층/전용면적(m2) 단위로 언제 얼마에 매매했는지 차트에 나타냈습니다.
        * 차트에서 흰색은 거래 이력이 없음을 의미합니다.
                """)

    col1, col2 = st.beta_columns([3, 5])
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
    col2.dataframe(latest_df.set_index(column_dict['transaction_date']))

    # Chart #1
    st.markdown("""
                # 연도별 평균거래금액
                """)

    col1, col2 = st.beta_columns([5, 3])
    df['transaction_amount'] = df['transaction_amount'].apply(
        lambda x: float(x))
    chart = df[['transaction_year', 'transaction_amount']
               ].groupby('transaction_year').mean()
    chart = chart.fillna(0)
    chart = chart.rename(columns=column_dict)
    chart.columns = [x for x in chart.columns]
    col1.line_chart(chart)
    col2.dataframe(chart.sort_index(ascending=False))
    st.markdown("""**Note**: X축은 년도, Y축은 거래금액""")


def run_the_app():
    # possession_home()
    property_home()
    hide_menu_style = """
    <style>
    # MainMenu {visibility: hidden;}
    </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    # slider()
    # home()


if __name__ == "__main__":
    run_the_app()
