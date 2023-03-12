# 標準モジュール

# 自作モジュール
from utilities.log_manager import LogManager

# ログ設定
log_manager = None


def set_common_log_manager(logger: LogManager):
    global log_manager

    log_manager = logger
