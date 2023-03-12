import pytest
import datetime
import pandas as pd

import os
import sys  # nopep8
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # nopep8
from config.settings import *  # nopep8
from playwright.sync_api import sync_playwright

from win5_data_getter import *
from utilities.common_functions import is_empty_DataFrame


def test_get_playwright_page():
    '''
    get_playwright_pageのテスト
    playwrightで正常に該当URLのページオブジェクトが取得できているかどうか判定する
    '''
    with sync_playwright() as playwright:
        page = get_playwright_page(
            playwright, 'https://www.yahoo.co.jp/', False)

    assert page is not None


def test_get_win5_races_page():
    '''
    get_win5_races_pageのテスト
    WIN5対象レース一覧が取得できているかどうか判定
    '''
    with sync_playwright() as playwright:
        soup = get_win5_races_page(
            playwright, JRA_TOP_URL)

    assert soup is not None and len(soup.text) > 0


def test_race_date_cnv_to_datetime_date():
    '''
    race_date_cnv_to_datetime_dateのテスト
    yyyy年M月d日形式の日付の文字列を正しく変換できているか確認する
    '''
    result = race_date_cnv_to_datetime_date('2022年12月31日')

    assert isinstance(result, datetime.datetime)


def test_get_entry_horce_info():
    '''
    get_entry_horce_infoのテスト
    ただしくレース詳細情報を取得できていることを確認する
    '''
    # 2022年12月18日の有松特別、中京10レース
    target_url = 'https://jra.jp/JRADB/accessD.html?CNAME=pw01dde0107202206061020221218/FA'
    race_date = '2022-12-18'
    race_no = 1
    df = get_entry_horce_info(target_url, race_date, race_no)

    assert not is_empty_DataFrame(df) and df.loc[0, :'馬名'] == 'メイショウイジゲン'
