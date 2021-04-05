from typing import Union

from ..applications import ApplicationUserSide
from ..applications import ColorTracking
from ..applications import FaceAndEyeDetection
from ..applications import FaceDetection
from ..applications import GameOfLifeParallelized
from ..applications import GameOfLifePyramid
from ..applications import GameOfLifeSerialized
from ..applications import NaiveFormulaParallelized
from ..applications import NaiveFormulaSerialized
from ..applications import VideoOCR
from ...component.basic import BasicComponent


def initActuator(
        appName: str,
        videoPath: str,
        label: str,
        showWindow: bool,
        basicComponent: BasicComponent,
        golInitText: str) -> Union[ApplicationUserSide, None]:
    actuator = None
    if appName == 'FaceDetection':
        actuator = FaceDetection(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent)
    elif appName == 'FaceAndEyeDetection':
        actuator = FaceAndEyeDetection(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent)
    elif appName == 'ColorTracking':
        actuator = ColorTracking(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent)
    elif appName == 'VideoOCR':
        actuator = VideoOCR(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent)
    elif appName in {'GameOfLifeSerialized', 'GameOfLifeSerialised'}:
        actuator = GameOfLifeSerialized(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent,
            golInitText=golInitText)
    elif appName == 'GameOfLifeParallelized':
        actuator = GameOfLifeParallelized(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent,
            golInitText=golInitText)
    elif appName == 'GameOfLifePyramid':
        actuator = GameOfLifePyramid(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent,
            golInitText=golInitText)
    elif appName == 'NaiveFormulaSerialized':
        actuator = NaiveFormulaSerialized(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent)
    elif appName == 'NaiveFormulaParallelized':
        actuator = NaiveFormulaParallelized(
            videoPath=videoPath,
            targetHeight=int(label),
            showWindow=showWindow,
            basicComponent=basicComponent)
    return actuator
