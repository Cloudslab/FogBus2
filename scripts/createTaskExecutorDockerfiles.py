import os

from camelToSnake import camelToSnake


def run():
    workplace = '../containers/' \
                'taskExecutor/' \
                'dockerfiles/'
    sourceBasename = 'BlurAndPHash'
    sourceFolder = os.path.join(workplace, sourceBasename)
    if not os.path.exists(sourceFolder):
        return

    for folder in os.listdir(workplace):
        destFolderPath = os.path.join(workplace, folder)
        if not os.path.isdir(destFolderPath):
            continue
        destBasename = os.path.basename(destFolderPath)
        if destBasename == sourceBasename:
            continue

        replace('docker-compose.yml', sourceFolder, destFolderPath,
                sourceBasename, destBasename)
        replace('Dockerfile', sourceFolder, destFolderPath, sourceBasename,
                destBasename)


def replace(composeFilename, sourceFolder, destFolderPath, sourceBasename,
            destBasename):
    sourceComposePath = os.path.join(sourceFolder, composeFilename)
    sourceCompose = open(sourceComposePath, 'r')
    sourceComposeContent = sourceCompose.read()
    sourceCompose.close()
    toReplace = camelToSnake(sourceBasename)
    replaceWith = camelToSnake(destBasename)
    destComposeContent = sourceComposeContent.replace(toReplace,
                                                      replaceWith)
    destComposeContent = destComposeContent.replace(sourceBasename,
                                                    destBasename)
    destComposePath = os.path.join(destFolderPath, composeFilename)

    destCompose = open(destComposePath, 'w+')
    destCompose.write(destComposeContent)
    destCompose.close()


if __name__ == '__main__':
    run()
