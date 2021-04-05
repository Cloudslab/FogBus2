from typing import Union

from ..tasks import *


def initTask(taskName: str) -> Union[BaseTask, None]:
    task = None
    if taskName == 'FaceDetection':
        task = FaceDetection()
    elif taskName == 'EyeDetection':
        task = EyeDetection()
    elif taskName == 'ColorTracking':
        task = ColorTracking()
    elif taskName == 'BlurAndPHash':
        task = BlurAndPHash()
    elif taskName == 'OCR':
        task = OCR()
    elif taskName == 'GameOfLife0':
        task = GameOfLife0()
    elif taskName == 'GameOfLife1':
        task = GameOfLife1()
    elif taskName == 'GameOfLife2':
        task = GameOfLife2()
    elif taskName == 'GameOfLife3':
        task = GameOfLife3()
    elif taskName == 'GameOfLife4':
        task = GameOfLife4()
    elif taskName == 'GameOfLife5':
        task = GameOfLife5()
    elif taskName == 'GameOfLife6':
        task = GameOfLife6()
    elif taskName == 'GameOfLife7':
        task = GameOfLife7()
    elif taskName == 'GameOfLife8':
        task = GameOfLife8()
    elif taskName == 'GameOfLife9':
        task = GameOfLife9()
    elif taskName == 'GameOfLife10':
        task = GameOfLife10()
    elif taskName == 'GameOfLife11':
        task = GameOfLife11()
    elif taskName == 'GameOfLife12':
        task = GameOfLife12()
    elif taskName == 'GameOfLife13':
        task = GameOfLife13()
    elif taskName == 'GameOfLife14':
        task = GameOfLife14()
    elif taskName == 'GameOfLife15':
        task = GameOfLife15()
    elif taskName == 'GameOfLife16':
        task = GameOfLife16()
    elif taskName == 'GameOfLife17':
        task = GameOfLife17()
    elif taskName == 'GameOfLife18':
        task = GameOfLife18()
    elif taskName == 'GameOfLife19':
        task = GameOfLife19()
    elif taskName == 'GameOfLife20':
        task = GameOfLife20()
    elif taskName == 'GameOfLife21':
        task = GameOfLife21()
    elif taskName == 'GameOfLife22':
        task = GameOfLife22()
    elif taskName == 'GameOfLife23':
        task = GameOfLife23()
    elif taskName == 'GameOfLife24':
        task = GameOfLife24()
    elif taskName == 'GameOfLife25':
        task = GameOfLife25()
    elif taskName == 'GameOfLife26':
        task = GameOfLife26()
    elif taskName == 'GameOfLife27':
        task = GameOfLife27()
    elif taskName == 'GameOfLife28':
        task = GameOfLife28()
    elif taskName == 'GameOfLife29':
        task = GameOfLife29()
    elif taskName == 'GameOfLife30':
        task = GameOfLife30()
    elif taskName == 'GameOfLife31':
        task = GameOfLife31()
    elif taskName == 'GameOfLife32':
        task = GameOfLife32()
    elif taskName == 'GameOfLife33':
        task = GameOfLife33()
    elif taskName == 'GameOfLife34':
        task = GameOfLife34()
    elif taskName == 'GameOfLife35':
        task = GameOfLife35()
    elif taskName == 'GameOfLife36':
        task = GameOfLife36()
    elif taskName == 'GameOfLife37':
        task = GameOfLife37()
    elif taskName == 'GameOfLife38':
        task = GameOfLife38()
    elif taskName == 'GameOfLife39':
        task = GameOfLife39()
    elif taskName == 'GameOfLife40':
        task = GameOfLife40()
    elif taskName == 'GameOfLife41':
        task = GameOfLife41()
    elif taskName == 'GameOfLife42':
        task = GameOfLife42()
    elif taskName == 'GameOfLife43':
        task = GameOfLife43()
    elif taskName == 'GameOfLife44':
        task = GameOfLife44()
    elif taskName == 'GameOfLife45':
        task = GameOfLife45()
    elif taskName == 'GameOfLife46':
        task = GameOfLife46()
    elif taskName == 'GameOfLife47':
        task = GameOfLife47()
    elif taskName == 'GameOfLife48':
        task = GameOfLife48()
    elif taskName == 'GameOfLife49':
        task = GameOfLife49()
    elif taskName == 'GameOfLife50':
        task = GameOfLife50()
    elif taskName == 'GameOfLife51':
        task = GameOfLife51()
    elif taskName == 'GameOfLife52':
        task = GameOfLife52()
    elif taskName == 'GameOfLife53':
        task = GameOfLife53()
    elif taskName == 'GameOfLife54':
        task = GameOfLife54()
    elif taskName == 'GameOfLife55':
        task = GameOfLife55()
    elif taskName == 'GameOfLife56':
        task = GameOfLife56()
    elif taskName == 'GameOfLife57':
        task = GameOfLife57()
    elif taskName == 'GameOfLife58':
        task = GameOfLife58()
    elif taskName == 'GameOfLife59':
        task = GameOfLife59()
    elif taskName == 'GameOfLife60':
        task = GameOfLife60()
    elif taskName == 'GameOfLife61':
        task = GameOfLife61()
    elif taskName == 'KineticEnergy0':
        task = KineticEnergy0()
    elif taskName == 'KineticEnergy1':
        task = KineticEnergy1()
    elif taskName == 'KineticEnergy2':
        task = KineticEnergy2()
    elif taskName == 'KineticEnergy3':
        task = KineticEnergy3()
    elif taskName == 'NaiveFormula0':
        task = NaiveFormula0()
    elif taskName == 'NaiveFormula1':
        task = NaiveFormula1()
    elif taskName == 'NaiveFormula2':
        task = NaiveFormula2()
    elif taskName == 'NaiveFormula3':
        task = NaiveFormula3()

    return task
