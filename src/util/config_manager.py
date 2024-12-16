import configparser

CONFIG_FILE_NAME = "config.ini"


def set_config(section: str, key: str, value):
    config = configparser.ConfigParser()
    # セクションチェック
    if section not in config:
        config[section] = {}

    # 値設定
    config[section][key] = str(value)

    with open(CONFIG_FILE_NAME, "w") as configfile:
        config.write(configfile)


def get_config(section: str, key: str, default=None):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME)
    if section in config:
        return config[section].get(key, default)
    else:
        return default
