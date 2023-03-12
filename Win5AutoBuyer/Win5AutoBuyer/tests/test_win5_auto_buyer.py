import pytest
import datetime
import pandas as pd

import os
import sys  # nopep8
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # nopep8
from config.settings import *  # nopep8

from pywebio.output import Output, span_

from win5_auto_buyer import *


@pytest.fixture(scope='module')
def get_test_data():
    '''
    test用データ作成処理
    '''
    s_race_detail = pd.Series()
    s_race_detail['レース日付'] = '2022-12-18'
    s_race_detail['レース番号'] = 1
    s_race_detail['枠番'] = 2
    s_race_detail['馬番'] = 3
    s_race_detail['馬名'] = 'テストワンダー'
    s_race_detail['オッズ'] = 4
    s_race_detail['人気'] = 5
    s_race_detail['年齢'] = '牝2/葦毛'
    s_race_detail['斤量'] = 52.4
    s_race_detail['ジョッキー'] = 'てすと太郎'
    s_race_detail['調教師名'] = 'テストやる三'

    return s_race_detail


def test_get_tab_table_vals_chk_lbls(get_test_data):
    '''
    get_tab_table_vals_chk_lblsのテスト
    指定した内容で正しく処理できているかどうかを確認する
    '''

    s_race_detail = get_test_data

    result = get_tab_table_vals_chk_lbls(s_race_detail)

    value_list = result['tab_vals']
    is_equal_waku = value_list[0] == s_race_detail['枠番']
    is_equal_horse_no = value_list[1] == s_race_detail['馬番']
    is_equal_chk_box = isinstance(value_list[2], Output)
    is_equal_horse_nm_span = isinstance(value_list[3], span_)
    is_equal_odds = value_list[4] == s_race_detail['オッズ']
    is_equal_popular = value_list[5] == s_race_detail['人気']
    is_equal_age = value_list[6] == s_race_detail['年齢']
    is_equal_weight = value_list[7] == s_race_detail['斤量']
    is_equal_jockey = isinstance(value_list[8], span_)
    is_equal_trainer = isinstance(value_list[9], span_)

    check_box_nm = result['chk_box_nms'][0]
    is_equal_chk_box_nm = check_box_nm == f'target_{s_race_detail["レース番号"]}_{s_race_detail["馬番"]}'

    result_list = (is_equal_waku, is_equal_horse_no,
                   is_equal_chk_box, is_equal_horse_nm_span,
                   is_equal_odds, is_equal_popular, is_equal_age,
                   is_equal_weight, is_equal_jockey, is_equal_trainer,
                   is_equal_chk_box_nm)

    assert all(result_list)


def test_get_race_detail_from_db(get_test_data):
    '''
    get_race_detail_from_dbのテスト
    正しくDBから取得できているかどうかを確認する
    '''
    df = get_race_detail_from_db(
        get_test_data['レース日付'], get_test_data['レース番号'], SORT_SELECT_VALS['popular_asc'])

    is_success_sorted = df.loc[0, '人気'] == df['人気'].min()

    assert not is_empty_DataFrame(df) and is_success_sorted


def test_output_race_detail_for_table_with_checkbox(get_test_data):
    # 複雑なのでちょっと自動テストにするかどうか考える
    pass


def test_output_params_for_table_with_checkbox():
    # 画面出力の関数なので目視のほうがいいかも
    pass


def test_is_even_number_all():
    '''
    is_even_number_allのテスト
    リスト内の要素が正しく判定できているかどうかを確認する
    '''
    test_list_all_even = [0, 2, 4, 8,]
    test_list_all_odd = [1, 3, 5, 7]
    test_list_mixed = [0, 1, 2, 3, 4, 5]

    result_all_even = is_even_number_all(test_list_all_even)
    result_all_odd = is_even_number_all(test_list_all_odd)
    result_mixed = is_even_number_all(test_list_mixed)

    assert result_all_even == 1 and result_all_odd == 0 and result_mixed == -1
