from logging import getLogger, config
import json
import traceback


class LogManager():
    """
    ログ出力管理クラス
    """

    def __init__(self, logger_name: str, config_file_path: str):
        """
        コンストラクタ
        Params
            logger_name: str
                loggerの名称
            config_file_path: str
                コンフィグファイルのパス(絶対パス)
        """

        # 念のためnullチェックをしておく
        if(not logger_name):
            raise Exception("logger_nameを指定してください")

        if(not config_file_path):
            raise Exception("config_file_pathを指定してください")

        self.logger_name = logger_name
        self.config_file_path = config_file_path

        # コンフィグファイルが指定されている場合は読み込む
        self.load_config()
        self.logger = getLogger(logger_name)

    def load_config(self):
        """
        logger用configファイル読み込み
        """
        with open(self.config_file_path, "r", encoding="utf-8") as f:
            config.dictConfig(json.load(f))

    def info(self, message):
        """
        infoレベルログ出力
        """
        self.logger.info(message)

    def warning(self, message):
        """
        warningレベルログ出力
        """
        self.logger.warning(message)

    def error(self, message):
        """
        errorレベルログ出力
        """
        self.logger.error(message)

    def debug(self, message):
        """
        debugレベルログ出力
        """
        self.logger.debug(message)

    def logging_error_traceback(self):
        """
        例外のスタックトレースを出力する処理
        """
        self.logger.error('例外が発生しました。')
        self.logger.error(
            '---------------------------------------------スタックトレース---------------------------------------------')
        self.logger.error(traceback.format_exc())
        self.logger.error(
            '---------------------------------------------スタックトレース　以上---------------------------------------')
