
import pandas as pd


def is_empty_DataFrame(target_df: pd.DataFrame):
    '''
    対象のDataFrameが空かどうか判定する処理
        Params
            target_df: pd.DataFrame
                検査対象のDataFrame
        Returns
            True: 空 False: 空ではない
    '''

    return target_df is None or len(target_df.index) == 0
