import cv2
from matplotlib import pyplot as plt

from prod.data_visualizer import vis_labels
from prod.kmglift_api import LiftData

if __name__ == "__main__":
    dir = "..\\assets\\KMG\\AKSH-283\\"

    f = dir + "weight_12.06.xlsx"

    liftData = LiftData(f) # [f1, f2] для, перетекающих изо дня в день, процессов
    print(liftData.getData())

    f = dir + "weight_13.06.xlsx"

    liftData = LiftData(f)  # [f1, f2] для, перетекающих изо дня в день, процессов
    print(liftData.getData())