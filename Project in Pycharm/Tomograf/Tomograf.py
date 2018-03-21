import os
import scipy
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import math
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

kivy.require('1.9.1')

from scipy import misc





class Controller(BoxLayout):
    def __init__(self):
        super(Controller, self).__init__()

    def first_button_clicked(self):
        self.ids.first_image.source = os.path.join(PATH, 'Shepp_logan.jpg')
        self.ids.first_image.reload()

    def second_button_clicked(self):
        self.ids.second_image.source = 'sinogram.jpg'
        self.ids.second_image.reload()

    def third_button_clicked(self):
        self.ids.third_image.source = 'recovered.jpg'
        self.ids.third_image.reload()


class ActionApp(App):

    def build(self):
        return Controller()


class SinogramExecutor:
    result = 0
    image = None

    def __init__(self, image):
        self.image = image

    def perform(self, y, x):
        self.result += image[y][x]

    def return_result(self):
        return int(self.result)

class RecoveryExecutor:
    value = 0
    image = None

    def __init__(self, img, value):
        self.value = value
        self.image = img

    def perform(self, y, x):
        self.image[y][x] += self.value

    def return_result(self):
        return self.image

def bresenhamLine(startPoint, endPoint, executor):
    y0, x0 = startPoint
    y1, x1 = endPoint
    "Bresenham's line algorithm"
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            if 0 <= x <= WIDTH and 0 <= y <= HEIGHT:
                executor.perform(y, x)
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            if 0 <= x <= WIDTH and 0 <= y <= HEIGHT:
                executor.perform(y, x)
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    if 0 <= x <= WIDTH and 0 <= y <= HEIGHT:
        executor.perform(y, x)
    return executor.return_result()

def compute_coordinates(phi):
    x = R * np.cos(phi)
    y = R * np.sin(phi)
    y = int(y + 0.5 * len(image))
    x = int(x + 0.5 * len(image[0]))
    return (y, x)

def build_sinogram(image):
    sinogram = []
    for i in range(STEPS):
        middle_angle = i * STEP
        projection = []
        for ray in range(-HALF_DETECTORS, HALF_DETECTORS, 1):
            shift_angle = ray * RANGE / DETECTORS
            start_point = compute_coordinates(middle_angle + shift_angle)
            end_point = compute_coordinates(middle_angle + math.pi - shift_angle)
            projection.append(bresenhamLine(start_point, end_point, SinogramExecutor(image)))
        sinogram.append(projection)
    return sinogram

def recover_image(sinogram):
    recoveredImage = [[0 for x in range(len(image[0]))] for y in range(len(image))]
    for i in range(STEPS):
        middle_angle = i * STEP
        for ray in range(-HALF_DETECTORS, HALF_DETECTORS, 1):
            shift_angle = ray * RANGE / DETECTORS
            start_point = compute_coordinates(middle_angle + shift_angle)
            end_point = compute_coordinates(middle_angle + math.pi - shift_angle)
            value = sinogram[i][ray + HALF_DETECTORS]
            recoveredImage = bresenhamLine(start_point, end_point, RecoveryExecutor(recoveredImage, value))
    return recoveredImage

if __name__ == '__main__':
    STEP = math.pi / 90
    RANGE = 0.2 * math.pi
    DETECTORS = 201

    STEPS = math.floor(math.pi / STEP)
    PATH = 'zdjecia'
    image = misc.imread(os.path.join(PATH, 'Shepp_logan.jpg'), flatten=1)
    image = scipy.misc.imresize(image, (len(image) // 5, len(image[0]) // 5))
    R = (len(image) ** 2 + len(image[0]) ** 2) ** 0.5
    HALF_DETECTORS = DETECTORS // 2
    WIDTH = len(image[0]) - 1
    HEIGHT = len(image) - 1
    myApp = ActionApp()
    sinogram = build_sinogram(image)
    misc.imsave("sinogram.jpg", sinogram)
    recoveredImage = recover_image(sinogram)
    misc.imsave("recovered.jpg", recoveredImage)
    myApp.run()



    # plt.imshow(tuple(sinogram), interpolation='nearest', cmap='gray')
    # plt.show()
    #
    # recoveredImage = recover_image(sinogram)
    # plt.imshow(tuple(recoveredImage), interpolation='nearest', cmap='gray')
    # plt.show()