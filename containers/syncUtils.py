import os
import sys

absDir = os.path.abspath(
    __file__[:-len(os.path.basename(__file__))])


def removeFolder(folderName):
    if not os.path.exists(folderName):
        return
    os.system('rm -rf %s' % folderName)


def removeFile(filename):
    if not os.path.exists(filename):
        return
    os.system('rm -f %s' % filename)


def removeAll(utilsPath):
    removeFolder(os.path.join(utilsPath, 'component'))
    removeFolder(os.path.join(utilsPath, 'connection'))
    removeFolder(os.path.join(utilsPath, 'container'))
    removeFolder(os.path.join(utilsPath, 'debugLogPrinter'))
    removeFolder(os.path.join(utilsPath, 'tools'))
    removeFolder(os.path.join(utilsPath, 'types'))
    removeFolder(os.path.join(utilsPath, 'config'))
    removeFolder(os.path.join(utilsPath, 'resourceDiscovery'))
    removeFile(os.path.join(utilsPath, '__init__.py'))
    removeFile(os.path.join(utilsPath, '../.env'))


def copyFolder(fromFolder, toFolder):
    os.system('cp -r %s %s' % (fromFolder, toFolder))


def copyFile(fromFile, toFiler):
    os.system('cp  %s %s' % (fromFile, toFiler))


def copyAll(fromUtils, toUtils):
    copyFolder(os.path.join(fromUtils, 'component'),
               os.path.join(toUtils, 'component'))
    copyFolder(os.path.join(fromUtils, 'connection'),
               os.path.join(toUtils, 'connection'))
    copyFolder(os.path.join(fromUtils, 'container'),
               os.path.join(toUtils, 'container'))
    copyFolder(os.path.join(fromUtils, 'debugLogPrinter'),
               os.path.join(toUtils, 'debugLogPrinter'))
    copyFolder(os.path.join(fromUtils, 'tools'),
               os.path.join(toUtils, 'tools'))
    copyFolder(os.path.join(fromUtils, 'types'),
               os.path.join(toUtils, 'types'))
    copyFolder(os.path.join(fromUtils, 'config'),
               os.path.join(toUtils, 'config'))
    copyFolder(os.path.join(fromUtils, 'resourceDiscovery'),
               os.path.join(toUtils, 'resourceDiscovery'))
    copyFile(os.path.join(fromUtils, '__init__.py'),
             os.path.join(toUtils, '__init__.py'))
    copyFile(os.path.join(fromUtils, '../.env'),
             os.path.join(toUtils, '../.env'))


def sync(fromFolder):
    folders = {
        'actor',
        'master',
        'remoteLogger',
        'taskExecutor',
        'user'}
    if fromFolder not in folders:
        print('[!] %s not in %s' % (fromFolder, str(folders)))
        return
    folders.remove(fromFolder)
    fromUtilsPath = os.path.join(absDir, fromFolder, 'sources/utils')

    for folder in folders:
        utilsPath = os.path.join(absDir, folder, 'sources/utils')
        removeAll(utilsPath)
        copyAll(fromUtilsPath, utilsPath)


if __name__ == '__main__':
    fromFolder_ = sys.argv[1]
    sync(fromFolder_)
    print('[*] Override with %s Done.' % fromFolder_)
