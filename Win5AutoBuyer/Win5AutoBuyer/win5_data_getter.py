# 標準モジュール
import inspect
import datetime
import sqlite3
import re

# インストールモジュール
import pandas as pd
from bs4 import BeautifulSoup as bs
from playwright.sync_api import Playwright, Page
import requests


# 自作モジュール
from utilities.common_log_manager import log_manager
from utilities.log_manager import LogManager

from config.settings import *

# ログ設定
if log_manager is None:
    # ログマネージャー設定
    log_manager = LogManager(
        __name__, f'config{os.path.sep}log_config.json')
else:
    log_manager = log_manager

# 定数


def get_playwright_page(playwright: Playwright, target_url: str, use_headless=True) -> Page:
    '''
    playwrightで対象urlのページオブジェクトを取得する処理
        Params
            playwright: Playwright
                playwrightオブジェクト
            target_url: str
                取得するページのurl
        Returns
            対象urlのページオブジェクト
    '''
    try:
        log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

        # playwrightオブジェクトからページオブジェクトを生成
        browser = playwright.chromium.launch(headless=use_headless)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        page.set_default_timeout(TIME_OUT)

        # 対象urlへ遷移
        page.goto(target_url, wait_until='networkidle')

        return page
    except Exception as e:
        log_manager.logging_error_traceback()
        page.close()
        context.close()
        browser.close()
    finally:
        log_manager.info(f'end {inspect.currentframe().f_code.co_name}')


def get_win5_races_page(playwright: Playwright, target_url: str) -> bs:
    '''
    WIN5対象レース一覧ページを取得する処理
        Params
            playwright: Playwright
                playwrightオブジェクト
            target_url: str
                取得するページのurl
        Returns
            WIN5対象レース一覧ページのbs4オブジェクト
    '''
    try:
        log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

        # トップページ
        page = get_playwright_page(playwright, target_url)

        # 出馬表クリック
        page.click('#kaisai > ul > li:nth-child(2) > a')
        page.wait_for_load_state('networkidle')

        # win5をクリック
        # WIN5が複数存在する場合があるので、ヘッダの日付からWIN5を含む直近のもの(=現在より未来かつ一番日付が近いもの)を選択する
        race_dates = page.locator('#main > div.panel.no-padding.no-border')\
            .filter(has=page.locator('h3.sub_header'))\
            .filter(has=page.locator('div.link_list.win5')).all_inner_texts()

        target_re = re.compile('([0-9]{1,2}月[0-9]{1,2}日).+')
        now_date = datetime.datetime.now().date()
        now_year = str(datetime.datetime.now().year)
        diff_result = -1
        target_date = None
        for race_date in race_dates:
            # 一つしかグルーピングしていないので、先頭を取得
            tmp = re.match(target_re, race_date).groups()[0]

            # 比較のため、先頭に現在の年を付与し、datetime型に変換
            tmp = now_year + '年' + tmp
            tmp = race_date_cnv_to_datetime_date(tmp)

            # 現在の日付よりも前の日付は不要
            if now_date > tmp:
                continue

            # レース日付から現在の日付を引く
            diff_race_date = (tmp - now_date).days

            # 計算結果に-1が設定されている場合、初回の計算なので条件なしに結果を代入
            if diff_result == -1:
                diff_result = diff_race_date
                target_date = tmp
            else:
                # 2回目以降の計算の場合、現在の計算結果が前回の計算結果よりも小さい(=日付が近い)場合のみ結果を代入
                if diff_result > diff_race_date:
                    diff_result = diff_race_date
                    target_date = tmp

        # WIN5対象レースが存在しない場合は以降の処理は不要
        if target_date == None:
            return None

        # 対象のWIN5をクリック
        target_race_date_month = target_date.strftime('%m')
        target_race_date_day = target_date.strftime('%d')

        # JRAサイトは0埋めではないので、先頭が0の場合は先頭を除く
        if target_race_date_month[0] == '0':
            target_race_date_month = target_race_date_month[1:]

        if target_race_date_day[0] == '0':
            target_race_date_day = target_race_date_day[1:]

        formatted_target_date = f'{target_race_date_month}月{target_race_date_day}日'

        page.locator('#main > div.panel.no-padding.no-border').filter(
            has=page.locator('h3.sub_header').get_by_text(formatted_target_date)).get_by_role('link').filter(has=page.get_by_alt_text('ウインファイヴ')).click()

        page.wait_for_load_state('networkidle')

        html = page.content()

        # BeautifulSoup4
        soup = bs(html, "lxml")

        return soup
    except Exception as e:
        log_manager.logging_error_traceback()
    finally:
        page.close()
        log_manager.info(f'end {inspect.currentframe().f_code.co_name}')


def get_win5_races(soup) -> pd.DataFrame:
    '''
    WIN5対象レース一覧から各レースの情報を取得する処理
        Params
            soup
                対象レース一覧ページのbs4オブジェクト
        Returns
            各レース情報の入ったDataFrame
    '''
    try:
        log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

        # 対象が存在しない場合は処理不要
        if soup.select_one(
                '#contentsBody > div.contents_header.opt > div > div.main > h2') is None:
            return pd.DataFrame()

        # 月日の取得
        race_date = soup.select_one(
            '#contentsBody > div.contents_header.opt > div > div.main > h2').text
        race_date = race_date_cnv_to_datetime_date(race_date[:-4])
        today = datetime.datetime.now().date()

        # 現在よりレース月日が後でない場合は処理不要
        if not today <= race_date:
            return pd.DataFrame()

        # win5テーブル取得
        wi5_table = soup.select_one(
            '#contentsBody > div.result_detail.mt30 > table')

        # 出走時刻
        start_times = [td.text.replace('\n', '').replace(' ', '')
                       for td in wi5_table.select('tr.time.red > td')]

        # レース名
        race_names = [span.text for span in wi5_table.select(
            'tr.race.yellow > td > span')]

        # 対象レースラウンド
        target_race_rounds = [
            a.text for a in wi5_table.select('tr.race.yellow > td > a')]

        # 対象レース詳細URL
        target_race_detail_urls = ['https://jra.jp' + a.attrs['href']
                                   for a in wi5_table.select('tr.race.yellow > td > a')]

        # レース日付
        list_race_date = [race_date.strftime(
            '%Y-%m-%d') for _ in range(len(race_names))]

        race_nums = [rg for rg in range(1, len(race_names)+1)]

        df_races = pd.DataFrame({
            'レース日付': list_race_date,
            'レース番号': race_nums,
            'レース名': race_names,
            '対象レース': target_race_rounds,
            '出走時刻': start_times,
            '対象レースURL': target_race_detail_urls,
        })

        # DBに対象レース一覧を保存
        with sqlite3.connect(DB_PATH) as conn:
            df_races.to_sql(WIN5_TARGET_RACES_TABLE_NAME, conn,
                            if_exists='replace', index=None)

        return df_races

    except Exception as e:
        log_manager.logging_error_traceback()

        # エラーの場合は空のリストを返す
        return pd.DataFrame()
    finally:
        log_manager.info(f'end {inspect.currentframe().f_code.co_name}')


def race_date_cnv_to_datetime_date(race_date: str) -> datetime.datetime:
    '''
    yyyy年M月d日形式の日付をdatatime.datetimeオブジェクトに変換する処理
        Params
            race_date: str
                対象日付(通常はレース日付)
        Returns
            変換済みの対象日付
    '''

    return datetime.datetime.strptime(race_date, '%Y年%m月%d日').date()


def get_entry_horce_info(target_url: str, race_date: str, race_no: str) -> pd.DataFrame:
    '''
    WIN5対象レースの出馬表から各出走馬の詳細情報を取得する処理
        Params
            target_url: str
                出馬表URL
            race_date: str
                レース日付
            race_no: str
                レース番号
        Returns
            出馬表情報の入ったDataFrame
    '''
    try:
        log_manager.info(f'start {inspect.currentframe().f_code.co_name}')

        response = requests.get(target_url)

        # ↓この処理は重すぎるので、エンコードはshift-jis決め打ち
        # chardetresult = chardet.detect(response.content)
        response.encoding = ENCODING
        soup = bs(response.content, 'html.parser')

        tbody = soup.select_one('#syutsuba > table > tbody')

        # 枠番
        if tbody.select_one('tr > td.waku > img') is not None:
            waku_list = [int(waku_img.attrs['alt'][1:-1])
                         for waku_img in tbody.select('tr > td.waku > img')]
        else:
            waku_list = [int(waku.text.replace('\n', '')) if waku.text.replace('\n', '') != '' else -1
                         for waku in tbody.select('tr > td.waku')]

        # 馬番
        num_list = [int(num.text.replace('\n', '')) if num.text.replace('\n', '') != '' else -1
                    for num in tbody.select('tr > td.num')]

        # 馬名
        horse_name_list = [hourse_name.text.replace('\n', '').replace('\r', '') for hourse_name in tbody.select(
            'tr > td.horse > div.name_line > div.name > a')]

        # オッズ
        if tbody.select_one(
                'tr > td.horse > div.name_line > div.odds > div.odds_line > span.num > strong') is not None:
            odds_list = [float(odds_num.text) for odds_num in tbody.select(
                'tr > td.horse > div.name_line > div.odds > div.odds_line > span.num > strong')]
        else:
            odds_list = [-1 for rg in range(len(horse_name_list))]

        # 人気
        if tbody.select_one(
                'tr > td.horse > div.name_line > div.odds > div.odds_line > span.pop_rank') is not None:
            pop_rank_list = [int(pop_rank.text.replace('(', '').replace('番人気)', '')) for pop_rank in tbody.select(
                'tr > td.horse > div.name_line > div.odds > div.odds_line > span.pop_rank')]
        else:
            pop_rank_list = [-1 for rg in range(len(horse_name_list))]

        # 調教師名
        trainer_list = [trainer.text for trainer in tbody.select(
            'tr > td.horse > p.trainer')]

        # 年齢
        age_list = [age.text for age in tbody.select('tr > td.jockey > p.age')]

        # 斤量
        weight_list = [float(weight.next.text.replace('\r\n', '')) if weight.next.text.replace('\r\n', '') != '' else -1
                       for weight in tbody.select('tr > td.jockey > p.weight')]

        # ジョッキー
        jockey_list = [jockey.text for jockey in tbody.select(
            'tr > td.jockey > p.jockey > a')]

        # コース
        course_list = [soup.select_one('div.cell.course').text.replace(
            '\n', '').replace('コース：', '') for _ in range(len(horse_name_list))]

        # ハンデ
        handicap_list = [soup.select_one('div.cell.weight').text.replace(
            '\n', '') for _ in range(len(horse_name_list))]

        # DF変換
        df_race_detail = pd.DataFrame({
            'レース日付': [race_date for _ in range(len(horse_name_list))],
            'レース番号': [race_no for _ in range(len(horse_name_list))],
            '枠番': waku_list,
            '馬番': num_list,
            '馬名': horse_name_list,
            'オッズ': odds_list,
            '人気': pop_rank_list,
            '調教師名': trainer_list,
            '年齢': age_list,
            '斤量': weight_list,
            'ジョッキー': jockey_list,
            'コース': course_list,
            'ハンデ': handicap_list,
        })

        return df_race_detail

    except Exception as e:
        log_manager.logging_error_traceback()

        # エラーの場合は空を返す
        return pd.DataFrame()
    finally:
        log_manager.info(f'end {inspect.currentframe().f_code.co_name}')
