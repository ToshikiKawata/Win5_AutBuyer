import configparser


class ConfigManager():
    '''
    コンフィグ管理クラス
    '''

    def __init__(self, config_path: str, encoding: str = 'utf-8', not_use_interpolation: bool = False):
        '''
        コンストラクタ
            Params
                config_path: str
                    コンフィグファイルのパス
                encoding: str = 'utf-8'
                    コンフィグファイルのエンコーディング
                not_use_interpolation: bool = False
                    ConfigParserにconfigファイル変換を任せるかどうか
        '''
        # not_use_interpolation
        if not_use_interpolation:
            self.config_ini = configparser.ConfigParser(interpolation=None)
        else:
            self.config_ini = configparser.ConfigParser()

        self.config_ini.read(config_path, encoding=encoding)

    def __init__(self, config_path: str,  config_name: str, encoding: str = 'utf-8', not_use_interpolation: bool = False):
        '''
        コンストラクタ
            Params
                config_path: str
                    コンフィグファイルのパス
                config_name: str
                    コンフィグの名前
                encoding: str = 'utf-8'
                    コンフィグファイルのエンコーディング
                not_use_interpolation: bool = False
                    ConfigParserにconfigファイル変換を任せるかどうか
        '''
        # not_use_interpolation
        if not_use_interpolation:
            self.config_ini = configparser.ConfigParser(interpolation=None)
        else:
            self.config_ini = configparser.ConfigParser()

        self.config_ini.read(config_path, encoding=encoding)
        self.target_config = self.config_ini[config_name]

    def set_target_config(self, config_name: str):
        '''
        取得対象の設定をクラスのメンバーに設定する処理
        '''
        self.target_config = self.config_ini[config_name]

    def get_config_by_param_name(self, param_name: str) -> str:
        '''
        パラメーター名(個別の設定の名前)から設定を取得する処理
            Params
                param_name: str
                    パラメーター(個別の設定)の名前
            Returns
                取得した設定の値
        '''
        if self.target_config is None:
            print('この関数は引数を3個取るコンストラクタ専用です。')
            return None

        target_param = self.target_config.get(param_name)

        return target_param

    def get_config_by_names(self, config_name: str, param_name: str) -> str:
        '''
        コンフィグの名前から設定を取得する処理
            Params
                config_name: str
                    設定の名前
                param_name: str
                    パラメーター(個別の設定)の名前
            Returns
                取得した設定の値
        '''
        target_config = self.config_ini[config_name]
        target_param = target_config.get(param_name)

        return target_param
