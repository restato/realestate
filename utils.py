import pandas as pd
import requests
import json
import pandas as pd
import numpy as np
import streamlit as st

from elasticsearch import Elasticsearch,JSONSerializer, helpers
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
        elif isinstance(obj,(np.ndarray,)): #### This is the fix
            return obj.tolist()
        return JSONSerializer.default(self, obj)
        

class EsWrapper():
    
    def __init__(self):
        self.es = Elasticsearch(hosts=st.secrets.db.credentials.hostname + ":9200", port=9200, serializer=NumpyEncoder())
        
    def search(self, body={}):
        response = self.es.search(index='apt-trade', body=body)
        if 'aggregations' in response:
            return pd.DataFrame(response['aggregations']['apts']['buckets'])
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