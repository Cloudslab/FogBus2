from .base import BaseTask
import joblib
import requests
from os import getcwd
import numpy as np
import warnings


def _load_model():
    url = "https://raw.github.com/zhiywang1/DiaPredModels/main/scaler.pkl"
    directory = getcwd()
    filename = directory + '/scaler.pkl'
    r = requests.get(url)
    f = open(filename, 'wb')
    f.write(r.content)

    url = "https://raw.github.com/zhiywang1/DiaPredModels/main/model.pkl"
    directory = getcwd()
    filename = directory + '/model.pkl'
    r = requests.get(url)
    f = open(filename, 'wb')
    f.write(r.content)

    scaler = joblib.load("scaler.pkl")
    predictor = joblib.load("model.pkl")
    return scaler, predictor


class DiabetesPrediction(BaseTask):
    def __init__(self):
        super().__init__(taskID=120, taskName='DiabetesPrediction')
        self.scaler, self.predictor = _load_model()
        self.headers = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI',
                        'DiabetesPedigreeFunction', 'Age']
        self.headersPred = ['RowID'] + self.headers + ['Prediction']
        warnings.filterwarnings("ignore", category=UserWarning)

    def exec(self, input_data):
        row_id = input_data['RowID']
        row = np.asarray([[input_data[key] for key in self.headers]])
        transformed = self.scaler.transform(row)
        prediction = self.predictor.predict(transformed)
        result_row = row.tolist()[0] + [prediction[0]]
        return row_id, self.headersPred, [row_id] + result_row
