import os
import re
import shutil


def camel_to_snake(name):
    # https://stackoverflow.com/questions/1175208
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def run():
    for i in range(62):
        name = 'GameOfLife%d' % i
        shutil.rmtree(name)
        shutil.copytree('OCR', name, False, None)
        f = open('%s/Dockerfile' % name, 'r+')
        content = f.read()
        content = content.replace(
            '\n# Hostname\n'
            'RUN echo "OCR" > /etc/hostname\n\n'
            '# Run OCR', '')
        f.seek(0)
        f.write(content)
        f.truncate()
        f.close()

        f = open('%s/docker-compose.yml' % name, 'r+')
        content = f.read()
        content = content.replace('ocr', camel_to_snake(name))
        content = content.replace('OCR', name)
        f.seek(0)
        f.write(content)
        f.truncate()
        f.close()
        print(name)


if __name__ == '__main__':
    run()
