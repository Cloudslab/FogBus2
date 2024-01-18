import csv
import os.path
from queue import Empty
from time import time, sleep

from .base import ApplicationUserSide
from ...component.basic import BasicComponent


class DiabetesPrediction(ApplicationUserSide):

    def __init__(
            self,
            csvPath: str,
            basicComponent: BasicComponent):
        super().__init__(
            appName='DiabetesPrediction',
            basicComponent=basicComponent)
        self.csvPath = csvPath
        self.csvFile = None
        self.headers = ''
        self.rows = {}
        self.required_headers = {'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI',
                                 'DiabetesPedigreeFunction', 'Age'}

        self.unresolved_row_id = set([])

    def prepare(self):
        with open(self.csvPath, newline='') as csvfile:
            csvreader = csv.reader(csvfile)

            self.headers = next(csvreader)

            if self.required_headers.intersection(self.headers) != self.required_headers:
                raise ValueError(
                    'The CSV file does not contain all the required headers.:\r\n Requires: %s\r\n Found: %s' % (
                        self.required_headers, self.headers))
            row_id_index = self.headers.index('RowID')
            for row in csvreader:
                self.rows[row[row_id_index]] = row
                self.unresolved_row_id.add(row[row_id_index])
        pass

    def send_unresolved(self):
        for row_id in self.unresolved_row_id:
            row = self.rows[row_id]
            temp_data = {}
            for i, key in enumerate(self.headers):
                temp_data[key] = row[i]

            input_data = {
                'RowID': temp_data['RowID'],
                'Pregnancies': int(temp_data['Pregnancies']),
                'Glucose': int(temp_data['Glucose']),
                'BloodPressure': int(temp_data['BloodPressure']),
                'SkinThickness': int(temp_data['SkinThickness']),
                'Insulin': int(temp_data['Insulin']),
                'BMI': float(temp_data['BMI']),
                'DiabetesPedigreeFunction': float(temp_data['DiabetesPedigreeFunction']),
                'Age': int(temp_data['Age']),
            }

            self.dataToSubmit.put(input_data)
        self.basicComponent.debugLogger.info('Sent %d rows', len(self.unresolved_row_id))

    def _run(self):
        self.prepare()

        self.basicComponent.debugLogger.info("[*] Sending rows ...")

        self.send_unresolved()

        self.basicComponent.debugLogger.info(
            "[*] Sent all rows and waiting for result ...")
        result_headers = ''
        results = []

        sleep(2)
        while len(self.unresolved_row_id) > 0:
            try:
                last_data_sent_time = time()
                (row_id, result_headers, row) = self.resultForActuator.get(block=True, timeout=5)
                response_time = (time() - last_data_sent_time) * 1000
                self.responseTime.update(response_time)
                self.responseTimeCount += 1
                if row_id in self.unresolved_row_id:
                    results.append(row)
                    self.unresolved_row_id.remove(row_id)
            except Empty:
                self.send_unresolved()

        result_path = os.path.realpath(self.csvPath) + "_result.csv"
        with open(result_path, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(result_headers)
            for row in results:
                csvwriter.writerow(row)
        self.basicComponent.debugLogger.info("[*] Done! Result is saved to %s", result_path)
