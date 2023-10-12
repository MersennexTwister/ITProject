import configparser

parser = configparser.ConfigParser()
parser.read('config.ini')

APP_ROOT = parser['root']['path']
SESSION_DUR = int(parser['session']['time'])
