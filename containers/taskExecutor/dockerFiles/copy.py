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
        content = content.replace('OCR', name)
        content = content.replace('## Python libararies\n', '')
        content = content.replace(
            'ADD ./taskSample/requirements.txt /workplace/requirements.txt\n',
            '')
        content = content.replace(
            'RUN python -m pip install --retries 100 --default-timeout=600  -r requirements.txt --no-cache-dir\n',
            '## Python libararies\n'
            'RUN python -m \\\n'
            '    pip install --retries 100 --default-timeout=600  --no-cache-dir \\\n'
            '    numpy pytesseract editdistance\n')
        content = content.replace(
            'ENTRYPOINT ["python", "taskExecutor.py"]',
            'ENTRYPOINT ["python", "taskExecutor.py"]')
        content = content.replace(
            'ADD ./taskSample/*.py /workplace/',
            'ADD ./taskExecutors/*.py /workplace/')

        f.seek(0)
        f.write(content)
        f.truncate()
        f.close()

        f = open('%s/docker-compose.yml' % name, 'r+')
        content = f.read()
        content = content.replace('ocr', camel_to_snake(name))
        content = content.replace('OCR', name)

        content = content.replace(
            'dockerfile: ./tasks/',
            'dockerfile: ./taskExecutorsDockerfile/')
        f.seek(0)
        f.write(content)
        f.truncate()
        f.close()


if __name__ == '__main__':
    run()
