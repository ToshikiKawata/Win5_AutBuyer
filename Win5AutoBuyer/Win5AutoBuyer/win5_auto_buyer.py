# 標準モジュール
from functools import partial
import inspect
from time import sleep
import datetime
import sqlite3
from typing import Tuple
import os

# インストールモジュール
import pandas as pd
from playwright.sync_api import sync_playwright
from utilities.common_functions import is_empty_DataFrame
from pywebio.output import put_table, use_scope, put_tabs, put_buttons, span, put_row, clear, put_loading, toast
from pywebio.pin import put_input, put_checkbox, pin_wait_change, put_select
import pywebio.session as psession
import numpy as np

# 自作モジュール
from utilities.log_manager import LogManager
from utilities.common_log_manager import set_common_log_manager

# ログ設定
log_manager = LogManager(
    __name__, f'config{os.path.sep}log_config.json')
set_common_log_manager(log_manager)

from config.settings import *  # nopep8
from utilities.sqlite_utils import execute_select_sql_with_param, execute_select_sql_with_param_query, get_query  # nopep8
from win5_data_getter import get_entry_horce_info, get_playwright_page, get_win5_races, get_win5_races_page  # nopep8


# WIN5対象レース一覧
df_win5_races = pd.DataFrame()

# パラメーターで選択された値一覧
selected_values = []

# 初期化フラグ
# デバック用if文 実運用時は消して = Trueのほうを残す
is_need_init = True

# 現在購入対象となる馬券組み合わせ
combination_list = []

# 定数
# レース詳細の並び順
SORT_SELECT_VALS = {
    'horse_num_asc': 0,
    'horse_num_desc': 1,
    'popular_asc': 2,
    'popular_desc': 3,
}

# 初期ソート順
DEFAULT_SORT = SORT_SELECT_VALS['popular_asc']

# スコープ名
# 組み合わせ計算エリアスコープ名
COMBINATION_SCOPE_NM = 'combination_disp'

# タブエリアスコープ名
TAB_SCOPE_NM = 'tab_area'

# 対象レース一覧エリアスコープ名
RACE_SUMMARY_SCOPE_NM = 'race_summary'

# ローディングスタイル
LOADING_STYLE = 'grow'

# ローディングの色
LOADING_COLOR = 'primary'

# ローディングに適用するCSS
LOADING_CSS = 'position: fixed; top: 50%; left: 50%;'


def get_tab_table_vals_chk_lbls(s_race_detail: pd.Series, param_selected: list):
    '''
    レース詳細を出力するチェックボックス付テーブルとチェックボックスのラベルのリストを取得する処理
        Params
            s_race_detail: pd.Series
                レース詳細のSeries
            param_selected: list
                各tabコントロール内の選択リスト
        Return
            テーブルとチェックボックスのラベルのリストが入ったSeries
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    check_box_label_list = []
    value_list = []

    # 枠番、馬番、オッズ、人気は決まっていない場合があるので、その場合は出力しない
    if s_race_detail['枠番'] == -1:
        value_list.append('')
    else:
        value_list.append(s_race_detail['枠番'])

    if s_race_detail['馬番'] == -1:
        value_list.append('')
    else:

        # 対象レースの選択済みの値を取得
        is_selected = False
        if not param_selected is None:
            # 選択状態復元のため、選択済みの値から、現在のレース番号と馬番に合致するものを取得
            for tmp_selected_data in param_selected:

                # 選択済みコントロールのnameがlistとstrの場合があり、各レース詳細情報はlist
                # チェックボックスのnameの先頭にはtargetがついているので、パラメーターと混同しないように判定
                if isinstance(tmp_selected_data['name'], list) and 'target' in tmp_selected_data['name'][0]:
                    # 各レース詳細情報のvalueは[<レース番号>,<馬番>]になっているので、現在処理中のものと合致するかどうか判定
                    if tmp_selected_data['value'][0][0] == s_race_detail['レース番号'] and tmp_selected_data['value'][0][1] == s_race_detail['馬番']:
                        is_selected = True
                        break

        value_list.append(s_race_detail['馬番'])
        check_box_name = f'target_{s_race_detail["レース番号"]}_{s_race_detail["馬番"]}'
        value_list.append(put_checkbox(check_box_name, options=[
            {'label': '', 'value': [s_race_detail["レース番号"], s_race_detail['馬番']], 'selected':is_selected}], inline=True))
        check_box_label_list.append(check_box_name)

    value_list.append(span(s_race_detail['馬名'], col=3))

    if s_race_detail['オッズ'] == -1:
        value_list.append('')
    else:
        value_list.append(s_race_detail['オッズ'])

    if s_race_detail['人気'] == -1:
        value_list.append('')
    else:
        value_list.append(s_race_detail['人気'])

    value_list.append(s_race_detail['年齢'])
    value_list.append(s_race_detail['斤量'])
    value_list.append(span(s_race_detail['ジョッキー'],  col=3))
    value_list.append(span(s_race_detail['調教師名'], col=3))

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return pd.Series({'tab_vals': value_list, 'chk_box_nms': check_box_label_list})


def get_race_detail_from_db(race_date: str, race_no: int, sort_select_val: int):
    '''
    DBからレース詳細情報を取得する処理
        Params
            race_date: str
                レース日付
            race_no: int
                レース番号
            sort_select_val: int
                並び順
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    sql = get_query(GET_WIN5_RACE_DETAIL_SQL)

    # 選択済みの並び順に応じてSQLのORDER BYを変更
    if sort_select_val == SORT_SELECT_VALS['horse_num_asc']:
        order_by = 'ORDER BY 馬番 ASC'
        sql = sql.replace('@order_by', order_by)
    elif sort_select_val == SORT_SELECT_VALS['horse_num_desc']:
        order_by = 'ORDER BY 馬番 DESC'
        sql = sql.replace('@order_by', order_by)
    elif sort_select_val == SORT_SELECT_VALS['popular_asc']:
        order_by = 'ORDER BY 人気 ASC'
        sql = sql.replace('@order_by', order_by)
    elif sort_select_val == SORT_SELECT_VALS['popular_desc']:
        order_by = 'ORDER BY 人気 DESC'
        sql = sql.replace('@order_by', order_by)

    df_race_detail = execute_select_sql_with_param_query(
        DB_PATH, sql, {'race_date': race_date, 'race_no': race_no})

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return df_race_detail


def output_race_detail_for_table_with_checkbox(row: pd.Series, sort_select_val: int, param_selected: list):
    '''
    各レースの出馬表をチェックボックス付テーブルとして出力する処理
        Params
            row: pd.Series
                対象レース情報
            sort_select_val
                レース詳細の並び順
            param_selected: list
                各tabコントロール内の選択リスト
        Returns
            出力したチェックボックス付テーブル
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    global is_need_init

    # すでにWIN5対象レース一覧データが存在している場合は、スクレイピング不要
    df_race_detail = get_race_detail_from_db(
        row['レース日付'], row['レース番号'], sort_select_val)

    # 起動時は必ずレース詳細をJRAから取得するため、is_need_initがTrueの場合は必ず取得しに行く
    if is_need_init or is_empty_DataFrame(df_race_detail):
        # 各レース詳細を取得し、コントロールを出力
        df_race_detail = get_entry_horce_info(
            row['対象レースURL'], row['レース日付'], row['レース番号'])

        # ソート順の設定
        # いずれも仮番号が振られている場合はソートしない
        if sort_select_val == SORT_SELECT_VALS['horse_num_asc']:
            if (df_race_detail['馬番'] != -1).all():
                df_race_detail = df_race_detail.sort_values(
                    '馬番', ascending=True)

        elif sort_select_val == SORT_SELECT_VALS['horse_num_desc']:
            if (df_race_detail['馬番'] != -1).all():
                df_race_detail = df_race_detail.sort_values(
                    '馬番', ascending=False)

        elif sort_select_val == SORT_SELECT_VALS['popular_asc']:
            if (df_race_detail['人気'] != -1).all():
                df_race_detail = df_race_detail.sort_values(
                    '人気', ascending=True)

        elif sort_select_val == SORT_SELECT_VALS['popular_desc']:
            if (df_race_detail['人気'] != -1).all():
                df_race_detail = df_race_detail.sort_values(
                    '人気', ascending=False)

    header = ['枠番', '馬番', '選択',
              span('馬名', col=3), 'オッズ', '人気', '年齢', '斤量', span('騎手', col=3), span('厩屋', col=3), ]

    value_list = []
    # 値を取得するために、チェックボックスのlabelが必要なので格納する
    check_box_label_list = []

    # dfの行(対象レース)ごとにチェックボックス付きテーブルを出力
    tmp = df_race_detail.apply(
        get_tab_table_vals_chk_lbls, param_selected=param_selected, axis=1)

    value_list.extend(tmp['tab_vals'].values)
    check_box_label_list.extend(tmp['chk_box_nms'].values)

    del tmp

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return put_table(value_list, header=header), check_box_label_list, df_race_detail


def output_params_for_table_with_checkbox(param_selected: list = None):
    '''
    組合せ抽出パラメーターをチェックボックス付テーブルとして出力する処理
        Params
            param_selected: list
                tab内の各コントロール選択状態
        Returns
            出力したチェックボックス付テーブル
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    # パラメーターtableのヘッダ
    header = ['人気和', '1人気頭数', '枠', '馬番']

    # 値を取得するためにチェックボックスのlabelが必要なので取得するためのlist
    check_box_label_list = []

    # 人気和チェックボックス
    ninkiwa = []
    for rg in range(5, 29):
        is_selected = False
        ctl_nm = f'ninkiwa_{rg}'
        check_box_label_list.append(ctl_nm)

        # 選択状態が存在しない場合は処理不要
        if param_selected is not None:
            # 人気和のコントロールの値のみ抽出
            for selected_ninkiwa in [param for param in param_selected if 'ninkiwa' in param['name']]:
                if selected_ninkiwa['value'][0] == rg:
                    is_selected = True
                    break

        ninkiwa.append(put_checkbox(ctl_nm, options=[
            {'label': f'{rg}', 'value': rg, 'selected': is_selected}], inline=True))

    # 1人気頭数チェックボックス
    ninki_tousu = []
    for rg in range(6):
        is_selected = False
        ctl_nm = f'ninki_tousu_{rg}'
        check_box_label_list.append(ctl_nm)

        # 選択状態が存在しない場合は処理不要
        if param_selected is not None:
            # 人気和のコントロールの値のみ抽出
            for selected_ninki_tousu in [param for param in param_selected if 'ninki_tousu' in param['name']]:
                if selected_ninki_tousu['value'][0] == rg:
                    is_selected = True
                    break
        ninki_tousu.append(put_checkbox(ctl_nm, options=[
            {'label': f'{rg}', 'value': rg, 'selected': is_selected}], inline=True))

    # 枠チェックボックス
    inner_outer_labels = ['外枠のみを除く', '内枠のみを除く']
    waku = []
    for rg in range(2):
        is_selected = False
        ctl_nm = f'waku_{rg}'
        check_box_label_list.append(ctl_nm)

        # 選択状態が存在しない場合は処理不要
        if param_selected is not None:
            # 人気和のコントロールの値のみ抽出
            for selected_waku in [param for param in param_selected if 'waku' in param['name']]:
                if selected_waku['value'][0] == rg:
                    is_selected = True
                    break

        waku.append(put_checkbox(ctl_nm, options=[
            {'label': inner_outer_labels[rg], 'value': rg, 'selected': is_selected}], inline=True))

    # 馬番
    odd_even_labels = ['奇数のみを除く', '偶数のみを除く']
    horse_num = []
    for rg in range(2):
        is_selected = False
        ctl_nm = f'horse_num_{rg}'
        check_box_label_list.append(ctl_nm)

        # 選択状態が存在しない場合は処理不要
        if param_selected is not None:
            # 人気和のコントロールの値のみ抽出
            for selected_horse_num in [param for param in param_selected if 'horse_num' in param['name']]:
                if selected_horse_num['value'][0] == rg:
                    is_selected = True
                    break

        horse_num.append(put_checkbox(ctl_nm, options=[
            {'label': odd_even_labels[rg], 'value': rg, 'selected': is_selected}], inline=True))

    # 表示用に値を行ごとに並べ替える
    value_list = []
    for idx, nikiwa_el in zip(range(len(ninkiwa)), ninkiwa):
        row_list = []
        row_list.append(nikiwa_el)

        if len(ninki_tousu) <= idx:
            row_list.append('')
        else:
            row_list.append(ninki_tousu[idx])

        if len(waku) <= idx:
            row_list.append('')
        else:
            row_list.append(waku[idx])

        if len(horse_num) <= idx:
            row_list.append('')
        else:
            row_list.append(horse_num[idx])

        value_list.append(row_list)

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return put_table(value_list, header=header), check_box_label_list


def is_even_number_all(target_list: list) -> int:
    '''
    リスト内の値がすべて偶数か奇数か判定する処理
        Param
            target_list: list
                判定対象のリスト
        Return
            -1: 奇数と偶数が混じっている
             0: 奇数のみ
             1: 偶数のみ
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    # 偶数判定
    results_even = [val % 2 == 0 for val in target_list]

    # 奇数判定
    results_odd = [val % 2 != 0 for val in target_list]

    # 偶数かどうか
    is_even = all(results_even)

    # 奇数かどうか
    is_odd = all(results_odd)

    ret = -1

    if not is_even and is_odd:
        ret = 0
    elif is_even and not is_odd:
        ret = 1
    else:
        ret = -1

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return ret


def get_param_list_by_name(name: str, selected_params: list) -> list:
    '''
    画面に表示されているコントロールの値をnameで取得してlistで返す処理
        Params
            name: str
                取得するコントロールのname
            selected_params: list
                入力値に変更のあったコントロールのlist
        Returns
            指定したnameの値が入ったlist
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    ret = []
    for selected_param in selected_params:
        if not name in selected_param['name']:
            continue

        # valueはリストの形になっているので最初の要素を取得
        ret.append(selected_param['value'][0])

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return ret


def calc_ticket_combination(selected_params: list):
    '''
    選択した条件および出走馬から購入組合せを計算する処理
        Params
            selected_params: list
                入力値に変更のあったコントロールのlist
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    if selected_params is None or len(selected_params) == 0:
        toast('選択は必須です。', position='center',
              color='info', duration=3)
        log_manager.info('何も選択されていないため、処理を終了します。')
        return

    global combination_list

    # 組み合わせ計算のため、対象レース詳細をDBから取得
    # すでにWIN5対象レース一覧データが存在している場合は、スクレイピング不要
    df_win5_race_detail = execute_select_sql_with_param(
        DB_PATH, GET_WIN5_RACE_DETAIL_BY_DATE_ONLY_SQL, {'race_date': datetime.datetime.now().strftime('%Y-%m-%d')})

    # 選択された馬のみの組み合わせを作成する

    # 選択された各レースの馬番を抽出し、list化
    race_detail_selected_params = []
    for selected_param in selected_params:
        # 馬番選択チェックボックスのnameには「target」が含まれているはずなので、判定
        if not 'target' in selected_param['name'][0]:
            continue

        race_detail_selected_params.append(selected_param['value'][0])

    if race_detail_selected_params is None or len(race_detail_selected_params) == 0:
        toast('馬番の選択は必須です。', position='center',
              color='info', duration=3)
        log_manager.info('馬番が選択されていないため、処理を終了します。')
        return

    # 各レース詳細DFから選択された馬番の情報のみ抽出
    target_race_details = []
    for selected_val in race_detail_selected_params:
        target_race_details.append(
            df_win5_race_detail.loc[(df_win5_race_detail.loc[:, 'レース番号'] == selected_val[0]) & (df_win5_race_detail.loc[:, '馬番'] == selected_val[1])])

    if len(target_race_details) > 0:
        df_target_race_details = pd.concat(target_race_details)

        df_target_race_details.reset_index(drop=True, inplace=True)

    # 人気和の選択状況を抽出
    ninkiwa_selected_params = get_param_list_by_name(
        'ninkiwa', selected_params)

    # 1番人気頭数チェック
    ninki_tousu_selected_params = get_param_list_by_name(
        'ninki_tousu', selected_params)

    # 枠の条件を抽出
    waku_selected_params = get_param_list_by_name('waku', selected_params)

    # 枠の条件を抽出
    odd_even_selected_params = get_param_list_by_name(
        'horse_num', selected_params)

    # 各組合せの直積を算出し、リスト化
    product_list = []

    # 必ず5レース分存在しているので、5重ループする
    for _, first_race in df_target_race_details.loc[df_target_race_details['レース番号'] == 1].iterrows():
        for _, second_race in df_target_race_details.loc[df_target_race_details['レース番号'] == 2].iterrows():
            for _, third_race in df_target_race_details.loc[df_target_race_details['レース番号'] == 3].iterrows():
                for _, fourth_race in df_target_race_details.loc[df_target_race_details['レース番号'] == 4].iterrows():
                    for _, fifth_race in df_target_race_details.loc[df_target_race_details['レース番号'] == 5].iterrows():

                        tmp_ninki_list = [first_race.loc['人気'], second_race.loc['人気'],
                                          third_race.loc['人気'], fourth_race.loc['人気'], fifth_race.loc['人気']]

                        # 人気がまだ決定していない馬が含まれている場合は組み合わせに含めない
                        if -1 in tmp_ninki_list:
                            continue

                        # 組み合わせ内の人気の合計が選択された人気和になるものだけを抽出
                        if len(ninkiwa_selected_params) > 0:
                            tmp_ninkiwa = (sum(tmp_ninki_list))

                            if not tmp_ninkiwa in ninkiwa_selected_params:
                                continue

                        # 一番人気が指定の数になっているものだけを抽出
                        if len(ninki_tousu_selected_params) > 0:
                            ninki_1st_cnt = tmp_ninki_list.count(1)
                            if not ninki_1st_cnt in ninki_tousu_selected_params:
                                continue

                        # 内枠のみまたは外枠のみを除く
                        if len(waku_selected_params) > 0:
                            tmp_waku_list = [first_race.loc['枠番'], second_race.loc['枠番'],
                                             third_race.loc['枠番'], fourth_race.loc['枠番'], fifth_race.loc['枠番']]
                            tmp_waku_list = np.array(tmp_waku_list)

                            # 枠番がまだ決定していない馬が含まれている場合は組み合わせに含めない
                            if -1 in tmp_waku_list:
                                continue

                            for waku_selected_param in waku_selected_params:
                                is_continue = False
                                # 外枠のみを除く
                                if waku_selected_param == 0:
                                    if all(tmp_waku_list >= 7):
                                        is_continue = True
                                        break
                                elif waku_selected_param == 1:
                                    # 内枠のみを除く
                                    if all(tmp_waku_list <= 2):
                                        is_continue = True
                                        break

                            if is_continue:
                                continue

                        # 馬番は組み合わせの生成に使用するので、抽出条件の判定前に作成すること
                        tmp_horse_num_list = [first_race.loc['馬番'], second_race.loc['馬番'],
                                              third_race.loc['馬番'], fourth_race.loc['馬番'], fifth_race.loc['馬番']]

                        # 馬番が奇数のみまたは偶数のみを除く
                        if len(odd_even_selected_params) > 0:

                            # 馬番がまだ決定していない馬が含まれている場合は組み合わせに含めない
                            if -1 in tmp_horse_num_list:
                                continue

                            for odd_even_selected_param in odd_even_selected_params:
                                even_or_odd = is_even_number_all(
                                    tmp_horse_num_list)
                                is_continue = False
                                # 奇数のみを除く
                                if odd_even_selected_param == 0:
                                    if even_or_odd == 0:
                                        is_continue = True
                                        break
                                elif odd_even_selected_param == 1:
                                    # 偶数のみを除く
                                    if even_or_odd == 1:
                                        is_continue = True
                                        break

                            if is_continue:
                                continue

                        product_list.append(tmp_horse_num_list)

    # メンバ変数に算出した組み合わせをセット
    combination_list = product_list

    # 組み合わせ点数を画面に表示
    set_calc_buy_buttons_area()

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')


def buy_tickets(buy_target_list: list):
    '''
    JRAの即PATから指定した組合せのWIN5馬券を購入する処理
        Params
            buy_target_list: list
                購入対象の組合せlist
    '''
    try:
        log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

        # 購入対象が存在しない場合は処理不要
        if buy_target_list is None or len(buy_target_list) == 0:
            toast('組合せが存在しません。', position='center',
                  color='info', duration=3)
            return

        # 即patログイン
        with sync_playwright() as playwright:
            page = get_playwright_page(playwright, SOKU_PAT_LOGIN_URL, False)

            # INET iID 入力

            # nameはHTMLのname属性ではないことに注意！（まぎらわしい！）
            # ここでいうnameは画面上に表示されている名前(文字列)のことで、例えばボタンに表示されている名称など
            # page.get_by_role("textbox", exact=False,
            #                  name='inetid').fill(SOKU_PAT_INET_ID)

            # ログイン画面はテキストボックス一つしかないのでこれで通る
            page.get_by_role('textbox').fill(SOKU_PAT_INET_ID)

            # ログインボタンをクリック
            page.get_by_title('ログイン').click()

            page.wait_for_load_state('networkidle')

            # 加入者番号入力
            page.get_by_role('row').filter(
                has_text='加入者番号').get_by_role('textbox').fill(SOKU_PAT_KANYU_NUM)

            # 暗証番号入力
            page.get_by_role('row').filter(
                has_text='暗証番号').get_by_role('textbox').fill(SOKU_PAT_PASSWORD)

            # P-ARS番号入力
            page.get_by_role('row').filter(
                has_text='P-ARS番号').get_by_role('textbox').fill(SOKU_PAT_P_ARS_NUM)

            # ネット投票メニューへクリック
            page.get_by_title('ネット投票メニューへ').click()

            page.wait_for_load_state('networkidle')

            # WIN5を選択
            page.get_by_title('指定された5レースの1着を予想する投票方式です。').click()
            page.wait_for_load_state('networkidle')

            # このまま進むを選択
            # 残高が足りていない場合のみ、以下のコントロールが表示される
            # page.get_by_role('button').filter(has_text='このまま進む').click()
            # page.wait_for_load_state('networkidle')

            # 完全セレクトを選択
            page.get_by_role('link').filter(
                has=page.get_by_text('完全セレクト')).click()
            page.wait_for_load_state('networkidle')

            # 組み合わせに応じて各レースの馬番を選択
            for horse_nums in buy_target_list:
                for idx, num in zip(range(len(horse_nums)),  horse_nums):
                    # 各レースのロケーターを取得
                    race_locator = page.locator(
                        'div.race-buttons').nth(idx)

                    # 各レースの馬番選択ボタンの順序とhorse_numの馬番は対応しているので、これでチェックボックスを取得し、チェック
                    race_locator.get_by_text(
                        str(num), exact=True).check()

                # 金額入力
                page.fill(
                    '#win5-all-amount', BUY_AMOUNT_PER_1TICKET)

                # セットボタンをクリック
                page.get_by_role('button').filter(has_text='セット').click()
                page.wait_for_load_state('networkidle')

            # 入力終了
            page.get_by_role('button').filter(has_text='入力終了').click()

            page.wait_for_load_state('networkidle')

            # ★★★★★★★★★注意！！★★★★★★★★★
            # ★★★★★★★★★ここから下のコメントアウトを外すと実際に購入する★★★★★★★★★

            # 合計金額入力
            total_amount = (len(buy_target_list) *
                            (int(BUY_AMOUNT_PER_1TICKET)*100))
            page.get_by_role('row').filter(
                has_text='合計金額入力').get_by_role('textbox').fill(str(total_amount))

            # 購入するボタンクリック
            page.get_by_role('button').filter(has_text='購入する').click()

            page.wait_for_load_state('networkidle')

            # OKボタンクリック
            page.get_by_role('button').filter(has_text='OK').click()
            page.wait_for_load_state('networkidle')

            # 購入完了まで待機
            is_complete = False
            while not is_complete:
                tmp = page.get_by_text(
                    'お客様の投票を受け付けました。').all_inner_texts()

                if tmp is not None:
                    is_complete = len(tmp) > 0
                sleep(ACCESS_INTERVAL)

            toast('購入完了', position='center',
                  color='success', duration=3)

            log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    except Exception as e:
        log_manager.logging_error_traceback()


def set_calc_buy_buttons_area():
    '''
    組合せ計算・購入ボタンおよび組合せ点数テキストボックスを出力する処理
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    with use_scope(COMBINATION_SCOPE_NM, clear=True):
        put_row([put_input(name='combination_cnt', label='組合せ点数',
                           value=f'{len(combination_list)}', readonly=True), ], size='100px')

        put_buttons(['組合せ計算', '購入'],
                    onclick=[
                        partial(calc_ticket_combination,
                                selected_params=selected_values),
                        partial(buy_tickets,
                                buy_target_list=combination_list)
        ]
        )

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')


def get_win5_races_proc() -> pd.DataFrame:
    '''
    直近のWIN5対象レース一覧を取得する処理
        Returns
            WIN5レース一覧情報が入ったDataFrame
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    # 現在の日付より過去のレースは表示しないようにするため、今日の日付を取得
    today = datetime.datetime.now().date()

    # すでにWIN5対象レース一覧データが存在している場合は、スクレイピング不要
    df_win5_races = execute_select_sql_with_param(
        DB_PATH, GET_WIN5_TARGET_RACES_SQL, {'race_date': today.strftime('%Y-%m-%d')})

    if is_empty_DataFrame(df_win5_races):
        # WIN5対象レース一覧を取得
        with sync_playwright() as playwright:
            soup = get_win5_races_page(
                playwright, JRA_TOP_URL)

            if soup is None:
                return pd.DataFrame()

        df_win5_races = get_win5_races(soup)

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return df_win5_races


def get_win5_race_detail_ctls(df_win5_races: pd.DataFrame, sort_select_val: int, param_selected: list = None) -> Tuple[list, list, list, list, list, list]:
    '''
    WIN5の各レース詳細情報の入ったチェックボックス付きテーブルを取得する処理
        Params
            df_win5_races: pd.DataFrame
                WIN5対象レース一覧のDataFrame
            sort_select_val: int
                WIN5レース詳細の並び順
            param_selected: list
                各tabコントロール内の選択リスト
        Returns
            chk_label_list:list
                pywebioのpinコントロールの取得に使用するチェックボックスの名前のリスト
            tabs_list:list
                タブ表示するコントロールのリスト
            race_round_list:list
                WIN5対象レース一覧テーブルの対象ラウンド名
            race_name_list:list
                WIN5対象レース一覧テーブルの対象レース名
            course_info_list
                各レースのコース情報
            handicap_info_list
                各レースのハンデ情報
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    global is_need_init

    # 選択状況を取得するために必要なチェックボックスのlabelを格納するlist
    chk_label_list = []

    # 各レースの概要と詳細を取得し、概要はそのままテーブルへ
    # 詳細はタブで区切ってチェックボックス付きテーブルへ
    race_round_list = []
    race_name_list = []
    course_info_list = []
    handicap_info_list = []
    tabs_list = []
    df_race_detail = pd.DataFrame()
    for idx, row in df_win5_races.iterrows():

        # race_round_list.append(put_text(row.loc['対象レース']))
        race_round_list.append(row.loc['対象レース'])
        race_name_list.append(row.loc['レース名'])

        # レースデータから各レースの詳細情報を取得し、チェックボックス付table出力
        content, tmp_label_list, df_tmp = output_race_detail_for_table_with_checkbox(
            row, sort_select_val, param_selected)

        # 各レースの詳細をタブでひとまとめにするため、レース詳細情報にタイトルをつけて格納
        tabs_list.append({'title': f'{(idx+1)}レース',
                          'content': content})

        # チェック状態を取得するために必要なlabelを格納
        chk_label_list.extend(tmp_label_list)

        # 各レースのコース情報をlistに格納
        course_info_list.append(df_tmp.loc[0, 'コース'])

        # 各レースのハンデ情報をlistに格納
        handicap_info_list.append(df_tmp.loc[0, 'ハンデ'])

        if len(df_race_detail) == 0:
            df_race_detail = df_tmp
        else:
            df_race_detail = pd.concat([df_race_detail, df_tmp])

        sleep(ACCESS_INTERVAL)

    is_need_init = False

    # DBに対象レース詳細を保存
    with sqlite3.connect(DB_PATH) as conn:
        df_race_detail.to_sql(WIN5_TARGET_RACE_DETAIL_TABLE_NAME, conn,
                              if_exists='replace', index=None)

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return chk_label_list, tabs_list, race_round_list, race_name_list, course_info_list, handicap_info_list


def get_tab_area_ctls(df_win5_races: pd.DataFrame, sort_select_val: int, param_selected: list = None) -> Tuple[list, list, list, list, list, list]:
    '''
    タブエリアのコントロールを取得する処理
        Params
            df_win5_races: pd.DataFrame
                WIN5対象レース一覧
            sort_selected_val: int
                並び順
            param_selected: list 
                tab内の各コントロール選択状態
        Returns
            chk_label_list:list
                チェックボックスの名前一覧
            tabs_list:list
                タブコントロール
            race_round_list:list
                対象レースのラウンド(例: 中京10R)
            race_name_list:list
                対象レース名
            course_info_list
                各レースのコース情報
            handicap_info_list
                各レースのハンデ情報
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    chk_label_list, tabs_list, race_round_list, race_name_list, course_info_list, handicap_info_list = get_win5_race_detail_ctls(
        df_win5_races, sort_select_val, param_selected)

    # パラメーター選択タブ用のチェックボックス付テーブル出力
    tmp_table, tmp_label_list, = output_params_for_table_with_checkbox(
        param_selected)
    tabs_list.append({'title': 'パラメーター',
                      'content': tmp_table})
    chk_label_list.extend(tmp_label_list)

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')

    return chk_label_list, tabs_list, race_round_list, race_name_list, course_info_list, handicap_info_list


def set_sorted_tab_area_ctls(df_win5_races: pd.DataFrame, sort_selected_val: int):
    '''
    並び順ドロップダウンリスト選択時に呼び出すソート済みのtabエリアを設定する処理
        Params
            df_win5_races: pd.DataFrame
                WIN5対象レース一覧
            sort_selected_val: int
                並び順
    '''
    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    clear(TAB_SCOPE_NM)
    _, tabs_list, _, _, _, _ = get_tab_area_ctls(
        df_win5_races, sort_selected_val, selected_values)

    put_tabs(tabs_list, scope=TAB_SCOPE_NM).style('width:fit-content;')

    log_manager.info(f'end {inspect.currentframe().f_code.co_name}')


def main():

    log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

    # ローディング画面表示
    with put_loading(LOADING_STYLE, LOADING_COLOR).style(LOADING_CSS):

        # WIN5対象レース一覧を取得
        df_win5_races = get_win5_races_proc()

        if is_empty_DataFrame(df_win5_races):

            toast('対象レース一覧が存在しないため、処理を終了します。', position='center',
                  color='info', duration=3)
            log_manager.info('対象レース一覧が存在しないため、処理を終了します。')
            exit()

        # WIN5の各レース詳細からタブ出力するチェックボックス付きテーブルを作成
        # デフォルトの並び淳は人気昇順
        chk_label_list, tabs_list, race_round_list, race_name_list, course_info_list, handicap_info_list = get_tab_area_ctls(
            df_win5_races, DEFAULT_SORT)

        # win5対象レースをテーブル出力
        header_list = ['1レース',
                       '2レース',
                       '3レース',
                       '4レース',
                       '5レース', ]

        with use_scope(RACE_SUMMARY_SCOPE_NM):
            put_table([header_list,
                       race_round_list,
                       race_name_list,
                       handicap_info_list,
                       course_info_list,
                       ]).style('vertical-align: middle;text-align:center;')

            # 組合せ計算・購入ボタンおよび組合せ点数表示テキストボックス出力
            set_calc_buy_buttons_area()

        # 並び替えドロップダウンリスト
        sort_select_options = [{'label': '馬番 昇順', 'value': [SORT_SELECT_VALS['horse_num_asc'], ]},
                               {'label': '馬番 降順',
                                   'value': [SORT_SELECT_VALS['horse_num_desc'], ]},
                               {'label': '人気 昇順',
                                   'value': [SORT_SELECT_VALS['popular_asc'], ], 'selected':True},
                               {'label': '人気 降順',
                                   'value': [SORT_SELECT_VALS['popular_desc'], ]},
                               ]
        sort_select_name = 'sort_select'
        put_row(put_select(name=sort_select_name, options=sort_select_options,
                           label='並び順', value=DEFAULT_SORT), size='200px')
        chk_label_list.append(sort_select_name)

        with use_scope(TAB_SCOPE_NM, clear=True):
            # 各レース詳細とパラメーターをタブに出力
            put_tabs(tabs_list).style('width:fit-content;')

    # pinオブジェクトの変更のあったものを取得(メインループ処理)
    while True:
        new_selection = pin_wait_change(chk_label_list)

        # 選択解除された場合は、すでに格納済みのlabelと比較し、一致したものを削除
        if new_selection['value'] is None or len(new_selection['value']) == 0:
            del_target_val = None
            for selected_val in selected_values:
                if selected_val['name'] == new_selection['name']:
                    del_target_val = selected_val
                    break

            if not del_target_val is None:
                selected_values.remove(del_target_val)

        elif not new_selection in selected_values:
            # 並び順変更時は選択状態を保持する
            if new_selection['name'] == sort_select_name:
                with put_loading(LOADING_STYLE, LOADING_COLOR).style(LOADING_CSS):

                    set_sorted_tab_area_ctls(
                        df_win5_races, new_selection['value'][0])
            else:

                # 選択結果一覧に値が格納されていなければ追加
                selected_values.append(new_selection)


if __name__ == '__main__':
    try:
        psession.set_env(title='WIN5_AutoBuyer', output_max_width='65%')

        main()

    except Exception as e:
        log_manager.logging_error_traceback()
