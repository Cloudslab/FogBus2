import argparse
import os
from datetime import datetime
from logging import INFO
from time import sleep

from dotenv import dotenv_values

from tools import newDebugLogger

logger = newDebugLogger(loggerName='MariaDBSetup', levelName=INFO)
scriptPath = os.path.abspath(
    __file__[:-len(os.path.basename(__file__))])
environmentPath = os.path.join(scriptPath, '.env')
environment = dotenv_values(environmentPath)


def terminate():
    logger.info('Bye')
    os._exit(0)


def create():
    mysqlPath = os.path.join(scriptPath, 'mysql')
    if not os.path.exists(mysqlPath):
        logger.info('Please create path:'
                    '\n    %s', mysqlPath)
        terminate()
    while True:
        if len(os.listdir(mysqlPath)) == 1:
            gitKeepPath = os.path.join(mysqlPath, '.gitkeep')
            if os.path.exists(gitKeepPath):
                break
        logger.info('Please EMPTY the following folder'
                    ' BUT DO NOT DELETE IT.'
                    ' By doing so, your will lose data there.'
                    ' Make sure you have backup.'
                    ' If not, use "--backup"'
                    '\n    %s' % mysqlPath)
        logger.info('\nI have emptied %s'
                    '\n(Y to continue, E to exit,'
                    ' other keys to reuse the folder): ',
                    mysqlPath)
        userInput = input()
        if userInput not in {'y', 'Y', 'yes'}:
            break
        if userInput in {'E', 'e', 'Exit', 'exit'}:
            terminate()

    containerName = 'fogbus2-mariadb'
    logger.info('Creating MariaDB: %s', containerName)
    password = environment['MYSQL_PASSWORD']
    command = 'docker container rm -f %s' % containerName + \
              '; docker run -p 3306:3306' + \
              ' --name %s' % containerName + \
              ' -v "%s":/var/lib/mysql' % mysqlPath + \
              ' -e MYSQL_ROOT_PASSWORD="%s"' % password + \
              ' -e MYSQL_USER=fogbus2' + \
              ' -e MYSQL_PASSWORD="%s"' % password + \
              ' -d mariadb:10.5.9'
    ret = os.system(command=command)
    if ret != 0:
        return terminate()
    logger.info('Created MariaDB'
                '\n    Container name: %s'
                '\n    Password: %s (You may change this in %s)',
                containerName,
                password,
                environmentPath)


def backup():
    nowTime = datetime.now()
    sqlFilePath = os.path.join(
        scriptPath,
        'sqlFiles',
        'allDatabases-%s.sql' % str(nowTime).replace(' ', '-'))

    command = 'docker run --rm -it' \
              ' --net host' \
              ' -e MYSQL_PWD=%s ' % environment['MYSQL_PASSWORD'] + \
              ' mariadb:10.5.9' \
              ' bash -c ' \
              '"mysqldump -h 127.0.0.1' \
              ' -u root' \
              ' --all-databases"' \
              ' > %s' % sqlFilePath
    ret = os.system(command)

    if ret != 0:
        sqlFile = open(sqlFilePath, 'r')
        sqlFileContent = sqlFile.read()
        sqlFile.close()
        logger.info('Backup failed:'
                    '\n    %s' % sqlFileContent)
        os.system('rm %s' % sqlFilePath)
        return terminate()
    logger.info('Backup is at:'
                '\n    %s' % sqlFilePath)


def init():
    sqlFilename = 'allDatabases.sql'
    sqlFilePath = os.path.join(scriptPath, 'sqlFiles', sqlFilename)
    sqlFileFolder = os.path.dirname(sqlFilePath)
    sqlFilenames = os.listdir(sqlFileFolder)
    if not os.path.exists(sqlFilePath):
        logger.info('The following sql file does not exits:'
                    '\n    %s', sqlFilePath)
        terminate()
    if len(sqlFilenames) > 1:
        hint = ''
        for i, filename in enumerate(sqlFilenames):
            hint += '\n    [%d] %s' % (i, filename)
        logger.info('Your have many sql files under %s,'
                    '    %s'
                    '\nWhich one to use(number):', sqlFileFolder, hint)

        while True:
            userInput = input()
            if userInput in {'q', 'Q', 'Quit', 'e', 'E', 'exit'}:
                terminate()
            try:
                index = int(userInput)
                if index >= len(sqlFilenames):
                    continue
                sqlFilename = sqlFilenames[index]
                sqlFilePath = os.path.join(sqlFileFolder, sqlFilename)
                break
            except Exception:
                continue
    logger.info('Initializing database with file:'
                '\n    %s', sqlFilePath)
    command = 'docker run --rm -it' \
              ' --net host' \
              ' -e MYSQL_PWD=%s ' % environment['MYSQL_PASSWORD'] + \
              ' -v %s:/sqlFiles/' % sqlFileFolder + \
              ' mariadb:10.5.9' \
              ' bash -c ' \
              '"mysql -h 127.0.0.1' \
              ' -u root' \
              ' < /sqlFiles/%s"' % sqlFilename
    ret = os.system(command)

    if ret != 0:
        return terminate()
    logger.info('Initialized MariaDb')


def createParser():
    parser = argparse.ArgumentParser(
        description='MariaDB Setup')
    parser.add_argument(
        '--create',
        metavar='CreateMariaDB',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Create MariaDB container')
    parser.add_argument(
        '--init',
        metavar='InitMariaDB',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Initialize MariaDB databases')
    parser.add_argument(
        '--backup',
        metavar='BackupMariaDB',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Backup MariaDB databases')
    return parser


if __name__ == '__main__':
    parser_ = createParser()
    args = parser_.parse_args()

    if args.backup:
        backup()
    if args.create:
        create()
    if args.init:
        if args.create:
            toSleep = 30
            logger.info('Sleep %d seconds waiting for creation...', toSleep)
            while True:
                print('%d seconds left...' % toSleep, end='\r')
                sleep(1)
                toSleep -= 1
                if toSleep < 0:
                    break
        init()
    if not args.backup and not args.create and not args.init:
        parser_.print_help()
