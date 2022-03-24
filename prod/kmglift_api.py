import datetime
from enum import Enum, unique

import numpy as np
import cv2
import openpyxl

from prod.data_visualizer import imshow

""" TIME CONVERTER """


def sec2hms(secArg, isH_visible=True, isM_visible=True, isS_visible=True):
    if secArg > 24*60*60:
        print("more than one day")
    res = ""
    spl = str(datetime.timedelta(seconds=secArg)).split(":")
    isFirst = True
    if isH_visible:
        res += spl[0]
        isFirst = False
    if isM_visible:
        res += spl[1] if isFirst else (":" + spl[1])
    if isS_visible:
        res += spl[2] if isFirst else (":" + spl[2])

    return res


def hms2sec(strHMS="", hours=0, minutes=0, seconds=0):
    if strHMS != "":
        arrHMS = str(strHMS).split(":")
        hours = int(arrHMS[0]) if len(arrHMS) > 0 else hours
        minutes = int(arrHMS[1]) if len(arrHMS) > 1 else minutes
        seconds = int(arrHMS[2]) if len(arrHMS) > 2 else seconds
    return int(datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds())


""" Labels Enum """


""" Label - вид процесса"""
@unique
class Label(Enum):
    NODATA = 0
    DOWN = 1
    UP = 2
    OTHER = 3
    ANOMALY = 4


"""  Data Wrappers """


"""
    Класс отвечает только за хранение данных в секундах.
    За обратную интерпретацию должен отвечать уже другой класс
"""
class LiftDataSec:
    def __init__(self):
        self._values = []
        self._labels = []

    """ Каждый индекс - секунда, пропуски обозначаются как NODATA """
    def add(self, sec, value, label=Label.OTHER):
        miss = (sec - len(self))
        self._values.extend([0] * miss + [value])
        self._labels.extend([Label.NODATA] * miss + [label])

    def __len__(self):
        # len(self._values) = len(self._labels)
        return len(self._values)

    def __str__(self):
        return f"_values: {str(self._values)}" \
               f"_labels: {str(self._labels)}"


""" 
    В периодах пока нет NODATA
    all periods - время обнаруженных операций, промежуток от первого ненулевого значения до нулевого значения
    Примеры: 
        1. list [0 1 2 3 0] -- period [1, 4), Label.UP
        2. list [0 1 2 3 4] -- period [1, len(list)), Label.UP
    Каждый период имеет label
    
    period - объединенные последовательные и одинаковые процессы
"""
class LiftDataPeriods:
    """
        @ periods - list of [startTime, endTime]
    """
    def __init__(self, periods):
        self._periods = periods
        self._labels = [Label.OTHER] * len(self._periods)

    # <-- Get all in list -->
    def getAllStartsHMS(self):
        return list(map(lambda x: sec2hms(x[0]), self._periods))

    def getAllEndsHMS(self):
        return list(map(lambda x: sec2hms(x[1]), self._periods))

    def getAllDurations(self):
        return list(map(lambda x: sec2hms(x[1] - x[0], isS_visible=False), self._periods))

    def getAllLabelsNames(self):
        return list(map(lambda x: x.name, self._labels))

    # <-- Get one by id -->
    def getStartS(self, id):
        return self._periods[id][0]

    def getEndS(self, id):
        return self._periods[id][1]

    def getDtS(self, id):
        return self.getEndS(id) - self.getStartS(id)

    def getStartHMS(self, id):
        return sec2hms(self.getStartS(id))

    def getEndHMS(self, id):
        return sec2hms(self.getEndS(id))

    def getDtHMS(self, id):
        return sec2hms(self.getDtS(id))

    def getLabel(self, id):
        return self._labels[id]

    def __len__(self):
        return len(self._periods)

    def __str__(self):
        return "periods: " + str(self._periods) + "\nlabels: " + str(self._labels)

# """
#     Объединение одинаковых последовательных операций в одну
#     Не учитаваются, перескакивает промежутки между оперциями
# """
# def sameSequence(self):
#     #На этой стадии нет лейбла OTHER, только UP and DOWN
#     lastLabel = Label.OTHER
#     isClosed = True
#     for i in range(len(self)):
#         if isClosed:
#             # Открытие
#             self._periods.append([self.startS(i), self.endS(i)])
#             lastLabel = self.label(i)
#             isClosed = False
#         else:
#             # закрытие
#             if i == (len(self)-1): # Последняя оперция
#                 self._periods[len(self._periods) - 1][1] = self.endS(i)
#                 isClosed = True
#             elif lastLabel != self.label(i+1):
#                 self._periods[len(self._periods) - 1][1] = self.endS(i)
#                 isClosed = True
#
#             # Добавляем label
#             if isClosed == True:
#                 self._labels.append(lastLabel)


""" Пероиды от нуля до нуля: 00-1234-000-123-... """
def periods_between_zeros(values):
    periods = []
    # Сложнаватая логика, пересмотреть!
    isClose = True
    start = 0
    for i in range(len(values)):
        if values[i] == 0:
            if not isClose:
                periods.append([start, i])
            isClose = True
        elif isClose:
            isClose = False
            start = i

    if not isClose:
        periods.append([start, len(values)])

    return LiftDataPeriods(periods)


""" DATA IO"""


""" 
    Stretches data by seconds.
    Returns holder of (values, labels).
"""
def unpackData(xlsx_dir, liftData=LiftDataSec(), day=0):
    book = openpyxl.open(xlsx_dir, read_only=True)
    sheet = book.active

    daySec = day*86400

    for xlsx_strHMS, xlsx_val, xlsx_dur in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=0, max_col=3):
        if not (isinstance(xlsx_val.value, float) or isinstance(xlsx_val.value, int)):
            continue

        timeInSec = hms2sec(xlsx_strHMS.value)
        duration = hms2sec(xlsx_dur.value)

        for s in range(timeInSec, timeInSec+duration):
            liftData.add(daySec + s, xlsx_val.value)

    return liftData


def loadDataSec(xlsx_files):
    liftDataSec = LiftDataSec()

    for i in range(len(xlsx_files)):
        unpackData(xlsx_files[i], liftDataSec, i)

    return liftDataSec


""" VISUAL FILTER """


def vec2Mat(vec, isPlot=False):
    # можем указать любую яркость
    px_brightness = 255
    # Значение всегда с десятичной дробью
    rows = int(max(vec) * 10)
    cols = len(vec)

    mat = np.zeros((rows, cols))

    for col in range(cols):
        # В зависимости от направления роста координат
        row = rows - int(vec[col] * 10) - 1
        mat[row][col] = px_brightness

        # Дальше еще должны нарисовать линии от точки до следующей
        if isPlot:
            if col == cols - 1:
                break
            row1 = rows - int(vec[col + 1] * 10) - 1
            s = min(row, row1)
            e = max(row, row1)
            for i in range(s, e + 1):
                mat[i][col] = px_brightness

    return mat


def mat2vec(plotMat):
    rows = len(plotMat)
    cols = len(plotMat[0])

    vec = np.zeros(cols)
    # Берем самое большое(высокое) значение
    for c in range(cols):
        for r in range(rows):
            if plotMat[r][c] > 0:
                vec[c] = (rows - r - 1) / 10
                break
    return vec


""" 
    Как лучше назвать, чтобы понятно было, что матрицы возвращает, а не вектор
    Фильтрует и находит аномалии
"""
def visual_filter(liftDataSec):
    plotMat = vec2Mat(liftDataSec._values, isPlot=True)

    # Убираем горизонтальные линии типа ---
    kernel = np.ones((7, 1), np.uint8) # value*100kg
    lines = cv2.morphologyEx(plotMat, cv2.MORPH_OPEN, kernel)
    # imshow("orig", plotMat)
    # imshow("lines", lines)

    # Заполняем фигуру
    kernel = np.ones((1, hms2sec(minutes=3)), np.uint8)
    fill = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, kernel)
    # imshow("fill", fill)

    # Фильтруем шум - выбросы
    kernel = np.ones((1, hms2sec(seconds=7)), np.uint8)
    filtered = cv2.morphologyEx(fill, cv2.MORPH_OPEN, kernel)
    # imshow("filtered", filtered)

    # anomalies = fill - filtered
    # imshow("anomalies", anomalies)
    # kernel = np.ones((5, 1), np.uint8)  # value*100kg
    # anomalies = cv2.morphologyEx(anomalies, cv2.MORPH_OPEN, kernel)
    # imshow("anomalies", anomalies)
    # anomalies = mat2vec(anomalies)

    return fill, filtered


""" PREDICTOR """


def classify_process(y):
    y = mat2vec(y)

    label = Label.OTHER
    # print(len(y))
    # if len(y) < 10:
    #     return label
    # y = np.delete(y, [0, 1, len(y)-2, len(y)-1])

    x = range(len(y))
    z = np.polyfit(x, np.array(y), 1)

    k = z[0]
    # print(k)
    min_grad = 0.0005
    if k > min_grad:
        label = Label.UP
    elif k < -min_grad:
        label = Label.DOWN

    return label

# returns periods with labels(OTHER, UP, DOWN)
def classify_periods(filteredMat, process_periods):
    for i in range(len(process_periods)):
        s = process_periods.getStartS(i)
        e = process_periods.getEndS(i)

        window = filteredMat[0:len(filteredMat), s:e]

        process_periods._labels[i] = classify_process(window)

    return process_periods


def combine_periods(periods):
    return periods


def findAnomalies(fillMat, filteredMat, liftDataSec, process_periods):
    # fill-filtered должно быть выше диагонали и с соседями что-то больше чем 5тонн
    anomaliesAt = []

    anomalies = mat2vec(fillMat - filteredMat)
    for i, v in enumerate(anomalies):
        if v > 0:
            anomaliesAt.append(i)

    for i in range(len(process_periods)):
        s = process_periods.getStartS(i)
        e = process_periods.getEndS(i)

        window = filteredMat[0:len(filteredMat), s:e]

        # anomalies должны быть выше диагонали

    return anomaliesAt


def inspectData(liftDataSec):
    # Если получится сделать идею с диагональю без матрицы, то можно возвращать вектор фильтрованных значений и возможных аномалий
    fillMat, filteredMat = visual_filter(liftDataSec)

    filteredVals = mat2vec(filteredMat)
    process_periods = periods_between_zeros(filteredVals)

    process_periods = classify_periods(filteredMat, process_periods)

    anomaliesAt = findAnomalies(fillMat, filteredMat, liftDataSec, process_periods)

    periods = combine_periods(process_periods)

    setSecLabels(liftDataSec, periods, anomaliesAt)

    return periods, anomaliesAt


def setSecLabels(liftDataSec, liftDataPeriods, anomaliesAt):
    for i in range(len(liftDataPeriods)):
        s = liftDataPeriods.getStartS(i)
        e = liftDataPeriods.getEndS(i)

        liftDataSec._labels[s:e] = [liftDataPeriods._labels[i]] * (e - s)

    for i, v in enumerate(anomaliesAt):
        liftDataSec._labels[v] = Label.ANOMALY


""" MAIN ABSTRACTION """

"""
    Проблема в том, что процессы могут перетекать изо дня в день, 
    данная реализация тестировалась только на одном дне
"""


class LiftData:
    """
        @param xlsx_files -- лист файлов должен быть, можно передавать один файл
        <- процессы могут перетекать изо дня в день -> брать день по названию файла, не совсем правильно, если это лист
    """
    def __init__(self, xlsx_files):
        if type(xlsx_files) != list:
            xlsx_files = [xlsx_files]

        self.liftDataSec = loadDataSec(xlsx_files)

        self.periods, self.anomaliesAt = inspectData(self.liftDataSec)

    """ 
        Расчитан на данные одного дня,
        но процессы могут длиться днями
    """
    def getData(self):
        p = self.periods
        start = p.getAllStartsHMS()
        end = p.getAllEndsHMS()
        duration = p.getAllDurations()
        y = p.getAllLabelsNames()

        return {
            'data': {
                'start': start,
                'end': end,
                'duration': duration,
                'y': y
            }
        }