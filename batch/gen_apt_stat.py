# encoding: utf8
from __future__ import print_function
import multiprocessing
from joblib import Parallel, delayed

import argparse
import tqdm
import os
import glob
import pandas as pd

# trade
# area_code,transaction_amount,year_of_construction,transaction_year,legal_dong,apt_name,transaction_month,transaction_day,dedicated_area,jibun,floor,해제사유발생일,해제여부,si,gu,sigungu,area,dedicated_area_level,amount_per_area,transaction_date,description
# rent
# area_code,year_of_construction,transaction_year,legal_dong,deposit,apt_name,transaction_month,monthly_rent,transaction_day,dedicated_area,jibun,floor,si,gu,sigungu,sale_type,transaction_amount,area,dedicated_area_level,amount_per_area,transaction_date,description
COLS = {}
COLS['apt-trade'] = ['si', 'gu', 'sigungu', 'legal_dong', 'apt_name', 'transaction_amount', 'transaction_date', 'description',
                     'transaction_year', 'transaction_month', 'floor', 'dedicated_area', 'year_of_construction']
COLS['apt-rent'] = ['si', 'gu', 'sigungu', 'legal_dong', 'apt_name', 'transaction_amount', 'transaction_date',
                    'transaction_year', 'transaction_month', 'floor', 'dedicated_area', 'monthly_rent', 'deposit']


def preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    # preprocessing
    df['transaction_amount'] = df['transaction_amount'].astype(float)
    # df['transaction_amount'] = df['transaction_amount'].astype(
    # float).apply(lambda x: round(x / 10000, 2))
    # 2016-05-26 0:00:00
    df['transaction_date'] = pd.to_datetime(
        df['transaction_date'], format="%Y-%m-%d %H:%M:%S").dt.date
    df['transaction_year'] = df['transaction_year'].astype(object)
    df['transaction_month'] = df['transaction_month'].astype(object)
    df['year_of_construction'] = df['year_of_construction'].astype(int)
    df['floor'] = df['floor'].astype(int)
    df['dedicated_area'] = df['dedicated_area'].astype(float)

    if 'monthly_rent' in df.columns:
        df['monthly_rent'] = df['monthly_rent'].astype(int)
    return df


def price_dedicatedarea_floor(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index('apt_name')
    frames = []
    print(f' apt counts : {len(df.index)}')
    for desc in tqdm.tqdm(df.index):
        data = df.loc[[desc]]
        data = data.set_index(
            ['apt_name', 'dedicated_area', 'floor', 'transaction_amount'])[['transaction_date']]
        data = data.sort_values('transaction_date', ascending=True).tail(1)
        data = data.reset_index()
        frames.append(data)
    result_df = pd.concat(frames, axis=0)


def tempFunc(df: pd.DataFrame) -> pd.DataFrame:
    df['mean_transaction_amount'] = df['transaction_amount'].mean()
    return df


def applyParallel(dfGrouped, func):
    retLst = Parallel(n_jobs=multiprocessing.cpu_count())(
        delayed(func)(group) for name, group in dfGrouped)
    return pd.concat(retLst)


def transaction_amount_year(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index('apt_name')
    print(len(df))
    frames = []
    print(f' apt counts : {len(df.index)}')
    apt_names = df.index[:10]
    for apt_name in tqdm.tqdm(apt_names):
        data = df.loc[[apt_name]]
        # data = applyParallel(
        # data[['transaction_amount']].groupby(data.index), tempFunc)
        data = data[['transaction_year', 'transaction_amount']
                    ].groupby(data.index).mean()
        data = data.reset_index()
        frames.append(data)
    result_df = pd.concat(frames, axis=0)
    return result_df


def main(args):
    trade_type = args.trade_type
    if trade_type not in ('apt-trade', 'apt-rent'):
        Exception('not supported trade_type')

    area_code_dirs = glob.glob(os.path.join(args.data_path, trade_type, '*'))
    for area_code_dir in tqdm.tqdm(area_code_dirs):
        area_code = area_code_dir.split('/')[-1]
        print(area_code_dir)
        filelist = glob.glob(os.path.join(area_code_dir, '*.csv'))

        frames = []
        for filepath in tqdm.tqdm(filelist):
            frame = pd.read_csv(filepath, usecols=COLS[trade_type])
            frames.append(frame)
        df = pd.concat(frames, axis=0)
        df = preprocessing(df)
        # df = price_dedicatedarea_floor(df)
        df = transaction_amount_year(df)
        print(df.head(3))
        print(len(df))
        df.to_csv(
            f'/home/pi/data/apt_amount_per_year/{area_code}_{trade_type}.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--trade_type', required=True)
    args = parser.parse_args()
    args.data_path = '/home/pi/data/preprocessed'
    main(args)
