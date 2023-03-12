
import sqlite3
import pandas as pd
from .common_log_manager import log_manager
from .log_manager import LogManager
import os
LOG_CONFIG_FILE_PATH = f'config{os.sep}log_config.json'

if log_manager is None:
    # ログマネージャー設定
    log_manager = LogManager(
        __name__, LOG_CONFIG_FILE_PATH)
else:
    log_manager = log_manager


def get_query(sql_path: str):
    '''
    実行するSQLを取得する処理
        Params
            sql_path: str
                取得するSQLのファイルパス
        Return
            取得したSQL
    '''
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql = f.read()
            f.close()

        return sql

    except Exception as e:
        log_manager.logging_error_traceback()

        return None


def execute_select_sql_non_param(db_path: str, sql_path: str):
    '''
    パラメーターなしのSELECT文をpandasで実行する処理
        Params
            db_path: str
                sqliteファイルまでのパス
            sql_path: str
                実行するsqlファイルまでのパス
        Returns
            sqlの実行結果
            例外発生時はNone
    '''
    try:
        sql = get_query(sql_path)

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(sql, conn, )

        # すべての値がNoneの場合、行を返してほしくないので、DF自体をNoneにして返す
        if ((df.values == None).all()):
            df = None

        return df

    except Exception as e:
        log_manager.logging_error_traceback()

        return None


def execute_select_sql_with_param(db_path: str, sql_path: str, params: dict):
    '''
    パラメーターありのSELECT文をpandasで実行する処理
        Params
            db_path: str
                sqliteファイルまでのパス
            sql_path: str
                実行するsqlファイルまでのパス
            params: dict
                実行するsqlのパラメーター
                バインド変数名:代入する値のdict
        Returns
            sqlの実行結果
            例外発生時はNone
    '''
    try:
        sql = get_query(sql_path)

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(sql, conn, params=params)

        # すべての値がNoneの場合、行を返してほしくないので、DF自体をNoneにして返す
        if ((df.values == None).all()):
            df = None

        return df

    except Exception as e:
        log_manager.logging_error_traceback()

        return None


def execute_select_sql_with_param_query(db_path: str, query: str, params: dict):
    '''
    パラメーターありのSELECT文をpandasで実行する処理
        Params
            db_path: str
                sqliteファイルまでのパス
            query: str
                実行するsql
            params: dict
                実行するsqlのパラメーター
                バインド変数名:代入する値のdict
        Returns
            sqlの実行結果
            例外発生時はNone
    '''
    try:
        sql = query

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(sql, conn, params=params)

        # すべての値がNoneの場合、行を返してほしくないので、DF自体をNoneにして返す
        if ((df.values == None).all()):
            df = None

        return df

    except Exception as e:
        log_manager.logging_error_traceback()

        return None


def save_sqlite_from_df(df: pd.DataFrame, db_path: str, table_name: str, if_exist: str = 'append', index: bool = None):
    '''
    DataFrameのデータをsqliteに保存する処理
        Params
            df: pd.DataFrame
                保存するDataFrame
            db_path: str
                保存先のsqliteのパス
            table_name: str
                保存先のテーブル名
            if_exist: str = 'append'
                テーブルが存在している場合どうするか
                    append : 追記(デフォルト)
                    replace: 置換
                    fail   : 失敗(例外発生)
            index: bool = None
                DataFrameのインデックスを含めて保存するか
                    True: 保存する False: 保存しない(デフォルト)
        Returns
            実行結果
                True: 保存成功 False: 保存失敗
    '''
    try:
        with sqlite3.connect(db_path) as conn:
            df.to_sql(
                table_name, conn, if_exists=if_exist, index=index)

        return True
    except Exception as e:
        log_manager.logging_error_traceback()
        return False
