import winreg
import os
import configparser
import sys

config = configparser.ConfigParser()


def check_registry_entry_for_osu():
    reg_table = winreg.ConnectRegistry(None, winreg.HKEY_CLASSES_ROOT)

    try:
        with winreg.OpenKey(reg_table, r'osu\shell\open\command', 0, winreg.KEY_READ) as handle:
            _, osu_exe_path, _ = winreg.EnumValue(handle, 0)

        osu_exe_path = osu_exe_path.split(" ")[0].strip('"')
        osu_path = os.path.split(osu_exe_path)[0]
    except:
        osu_path = None

    return osu_path


if os.path.exists('analyzer.cfg'):
    config.read('analyzer.cfg')
    osu_path = config['OSU']['OSU_PATH']
else:
    osu_path = check_registry_entry_for_osu()
    if osu_path is None:
        config['OSU'] = {'OSU_PATH': 'YOUR OSU! PATH HERE INSTEAD OF THIS TEXT'}
        with open('analyzer.cfg', 'w') as configfile:
            config.write(configfile)

        print("Please put the osu root path into analyzer.cfg")
        sys.exit(1)
    else:
        config['OSU'] = {'OSU_PATH': osu_path}
        with open('analyzer.cfg', 'w') as configfile:
            config.write(configfile)


