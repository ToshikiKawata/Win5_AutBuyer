# コンフィグファイル読み込み
from utilities.config_manager import ConfigManager
import os

os_path_joiner = os.sep
CONFIG_FILE_PATH = f'config{os_path_joiner}config.ini'
LOG_CONFIG_FILE_PATH = F'config{os_path_joiner}log_config.json'

# コンフィグファイル読み込み
scraping_config = ConfigManager(
    CONFIG_FILE_PATH, 'SCRAPING_CONFIG', encoding='utf-8')

ACCESS_INTERVAL = int(scraping_config.get_config_by_param_name(
    'ACCESS_INTERVAL'))

USER_AGENT = scraping_config.get_config_by_param_name(
    'USER_AGENT')

TIME_OUT = int(scraping_config.get_config_by_param_name(
    'TIME_OUT'))

ENCODING = scraping_config.get_config_by_param_name(
    'ENCODING')

# コンフィグファイル読み込み
db_config = ConfigManager(
    CONFIG_FILE_PATH, 'DB_CONFIG', encoding='utf-8')

DB_PATH = db_config.get_config_by_param_name(
    'DB_PATH')

WIN5_TARGET_RACES_TABLE_NAME = db_config.get_config_by_param_name(
    'WIN5_TARGET_RACES_TABLE_NAME')

WIN5_TARGET_RACE_DETAIL_TABLE_NAME = db_config.get_config_by_param_name(
    'WIN5_TARGET_RACE_DETAIL_TABLE_NAME')

GET_WIN5_TARGET_RACES_SQL = db_config.get_config_by_param_name(
    'GET_WIN5_TARGET_RACES_SQL')

GET_WIN5_RACE_DETAIL_SQL = db_config.get_config_by_param_name(
    'GET_WIN5_RACE_DETAIL_SQL')

GET_WIN5_RACE_DETAIL_BY_DATE_ONLY_SQL = db_config.get_config_by_param_name(
    'GET_WIN5_RACE_DETAIL_BY_DATE_ONLY_SQL')

# コンフィグファイル読み込み
jra_config = ConfigManager(
    CONFIG_FILE_PATH, 'JRA_CONFIG', encoding='utf-8')

JRA_TOP_URL = jra_config.get_config_by_param_name(
    'JRA_TOP_URL')

JRA_ENTRY_HORSE_PAGE_URL = jra_config.get_config_by_param_name(
    'JRA_ENTRY_HORSE_PAGE_URL')

SOKU_PAT_LOGIN_URL = jra_config.get_config_by_param_name(
    'SOKU_PAT_LOGIN_URL')

SOKU_PAT_INET_ID = jra_config.get_config_by_param_name(
    'SOKU_PAT_INET_ID')

SOKU_PAT_KANYU_NUM = jra_config.get_config_by_param_name(
    'SOKU_PAT_KANYU_NUM')

SOKU_PAT_PASSWORD = jra_config.get_config_by_param_name(
    'SOKU_PAT_PASSWORD')

SOKU_PAT_P_ARS_NUM = jra_config.get_config_by_param_name(
    'SOKU_PAT_P_ARS_NUM')

BUY_AMOUNT_PER_1TICKET = jra_config.get_config_by_param_name(
    'BUY_AMOUNT_PER_1TICKET')
