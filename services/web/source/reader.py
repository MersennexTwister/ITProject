import configparser

parser = configparser.ConfigParser()
parser.read('source/config.ini')

APP_ROOT = '/usr/src/mars/source/'
SESSION_DUR = int(parser['session']['time'])