import pandas as pd
import requests
import json
import pandas as pd
import numpy as np
import streamlit as st
import locale

from pathlib import Path
from elasticsearch import Elasticsearch, JSONSerializer, helpers
from random import randint
from time import sleep

# https://github.com/elastic/elasticsearch-py/issues/378


class NumpyEncoder(JSONSerializer):
    """ Special json encoder for numpy types """

    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):  # This is the fix
            return obj.tolist()
        return JSONSerializer.default(self, obj)


class EsWrapper():

    def __init__(self):
        self.es = Elasticsearch(
            hosts=st.secrets['db_credentials']['hostname'] + ":9200", port=9200, serializer=NumpyEncoder())

    def search(self, body={}):
        response = self.es.search(index='apt-trade', body=body)
        if 'aggregations' in response:
            if 'apt' in response['aggregations']:
                return pd.DataFrame(response['aggregations']['apts']['buckets'])
            elif 'apt_name' in response['aggregations']:
                return pd.DataFrame(response['aggregations']['apt_name']['buckets'])
        df = pd.DataFrame(response['hits']['hits'])
        df = df['_source'].apply(pd.Series)
        return df


def get_hoga(hscpNo, n=3) -> pd.DataFrame:
    '''{"result":{"list":[{"repImgUrl":"","atclNo":"2108360426","repImgTpCd":"","vrfcTpCd":"OWNER","atclNm":"이매삼환","bildNm":"1109동","tradTpCd":"A1","tradTpNm":"매매","rletTpCd":"A01","rletTpNm":"아파트","spc1":"154.37","spc2":"132.37","flrInfo":"3/15","atclFetrDesc":"5월입주 가능한 올수리한 깨끗한 집","cfmYmd":"21.04.02","prcInfo":"15억","sameAddrCnt":13,"sameAddrDirectCnt":0,"sameAddrHash":"26A01A1Nb9c20bda439e7bc5eed2120420c9f1e67db658cbf827af3e6d6f58f21b031fb1","sameAddrMaxPrc":"15억 5,000","sameAddrMinPrc":"15억","tradCmplYn":"N","tagList":["25년이상","올수리","대형평수","방네개이상"],"atclStatCd":"R0","cpid":"bizmk","cpNm":"매경부동산","cpCnt":3,"cpLinkVO":{"cpId":"bizmk","mobileArticleLinkTypeCode":"NONE","mobileBmsInspectPa'''
    column_dict = {'direction': '향', 'tagList': '특징', 'flrInfo': '층', 'cfmYmd': '확인',
                   'prcInfo': '가격', 'atclFetrDesc': '설명', 'spc1': '공급면적', 'spc2': '전용면적'}
    # url = f"https://m.land.naver.com/complex/getComplexArticleList?hscpNo={hscpNo}&cortarNo=4113510600&tradTpCd=A1&order=point_&showR0=N&page=1"

    frames = []
    next_null = False
    for page in range(1, 100):
        if next_null:
            break
        url = f"https://m.land.naver.com/complex/getComplexArticleList?hscpNo={hscpNo}&tradTpCd=A1&order=point_&showR0=N&page={page}"
        payload = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.220 Whale/1.3.51.7 Safari/537.36',
            'Referer': 'https://m.land.naver.com/'
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        sleep(randint(3, 6) / 100)

        print(response.status_code)
        print(response.text)

        # parse result
        data = json.loads(response.text)
        data = data.get('result').get('list')
        frame = pd.DataFrame(data)
        if len(frame) < 1:
            next_null = True
        frames.append(frame)

    df = pd.concat(frames, axis=0)
    total_count = len(df)
    df = df.rename(columns=column_dict)
    df = df[['가격', '층', '전용면적', '향', '특징', '설명']]
    df['score'] = df['가격'].apply(lambda x: int(
        x.replace('억', '').replace(',', '').replace(' ', '')))
    df['특징'] = df['특징'].apply(lambda x: ','.join(x) + '\t\t')
    df['전용면적'] = df['전용면적'].astype(float)
    df = df[df['전용면적'] < 85]
    df.drop_duplicates(keep=False, inplace=True)

    # 전용면적 별로 가격 topN
    df = df.sort_values('score', ascending=True).groupby(['전용면적']).head(n)
    df = df.sort_values('score', ascending=True)
    # df = df.drop('score', axis=0)
    df = df.reset_index(drop=True)
    return df, total_count


def get_local_data():
    df = get_local_data('./data_out/price_dedicatedarea_floor/41135.csv')
    df = filtering(df)
    df = df.set_index('apt_name')
    df = df.sort_index()
    '''
    if apt_name in df.index:
        df = df.loc[apt_name]
    else:
        st.error(f'{apt_name}은 존재하지 않습니다.')
    '''
    return df


def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()


def int_to_string_with_comma(value):
    # Use '' for auto, or force e.g. to 'en_US.UTF-8'
    locale.setlocale(locale.LC_ALL, '')
    return locale.format("%d", value, grouping=True)


def get_kor_amount_string_no_change(num_amount, ndigits_keep=3):
    """잔돈은 자르고 숫자를 자릿수 한글단위와 함께 리턴한다 """
    return get_kor_amount_string(num_amount, -(len(str(num_amount)) - ndigits_keep))


def get_kor_amount_string(num_amount, ndigits_round=0, str_suffix='원'):
    """숫자를 자릿수 한글단위와 함께 리턴한다 """
    assert isinstance(num_amount, int) and isinstance(ndigits_round, int)
    assert num_amount >= 1, '최소 1원 이상 입력되어야 합니다'
    # 일, 십, 백, 천, 만, 십, 백, 천, 억, ... 단위 리스트를 만든다.
    maj_units = ['만', '억', '조', '경', '해', '자',
                 '양', '구', '간', '정', '재', '극']  # 10000 단위
    units = [' ']  # 시작은 일의자리로 공백으로하고 이후 십, 백, 천, 만...
    for mm in maj_units:
        units.extend(['십', '백', '천'])  # 중간 십,백,천 단위
        units.append(mm)

    list_amount = list(str(round(num_amount, ndigits_round))
                       )  # 라운딩한 숫자를 리스트로 바꾼다
    list_amount.reverse()  # 일, 십 순서로 읽기 위해 순서를 뒤집는다

    str_result = ''  # 결과
    num_len_list_amount = len(list_amount)

    for i in range(num_len_list_amount):
        str_num = list_amount[i]
        # 만, 억, 조 단위에 천, 백, 십, 일이 모두 0000 일때는 생략
        if num_len_list_amount >= 9 and i >= 4 and i % 4 == 0 and ''.join(list_amount[i:i+4]) == '0000':
            continue
        if str_num == '0':  # 0일 때
            if i % 4 == 0:  # 4번째자리일 때(만, 억, 조...)
                str_result = units[i] + str_result  # 단위만 붙인다
        elif str_num == '1':  # 1일 때
            if i % 4 == 0:  # 4번째자리일 때(만, 억, 조...)
                str_result = str_num + units[i] + str_result  # 숫자와 단위를 붙인다
            else:  # 나머지자리일 때
                str_result = units[i] + str_result  # 단위만 붙인다
        else:  # 2~9일 때
            str_result = str_num + units[i] + str_result  # 숫자와 단위를 붙인다
    str_result = str_result.strip()  # 문자열 앞뒤 공백을 제거한다
    if len(str_result) == 0:
        return None
    if not str_result[0].isnumeric():  # 앞이 숫자가 아닌 문자인 경우
        str_result = '1' + str_result  # 1을 붙인다
    return str_result + str_suffix  # 접미사를 붙인다


def get_wonwha_string(num_wonwha_amout):
    """ 입력된 원화를 4자리단위 한글로 변환한다 """
    str_result = ""  # 결과문자열 초기화
    str_sign = ""  # 부호 초기화
    num_change = num_wonwha_amout  # 최초값을 모두 잔돈에 넣는다

    if num_change == 0:  # 0원이면
        str_result = "0"
    elif num_change < 0:  # 음수이면
        str_sign = "-"  # 음의 부호(Negative Sign)를 붙이고
        num_change = abs(num_change)  # 절대값으로 변환 후 변환을 계속한다

    if num_change >= 100000000:  # 1억 이상
        str_result += f"{int(num_change // 100000000):,}억"
        num_change = num_change % 100000000
    if num_change >= 10000:  # 1만 이상
        str_result += f" {int(num_change // 10000):,}만"
        num_change = num_change % 10000
    if num_change >= 1:  # 1 이상
        str_result += f" {int(num_change):,}"

    # Return a copy of the string with the leading and trailing characters removed
    str_result = str_result.strip()
    if len(str_result) >= 1:
        return str_sign + str_result + "원"
    else:
        return str_result
