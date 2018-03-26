import os
import scipy
import numpy as np
import math
import kivy
import cv2
from copy import deepcopy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout

kivy.require('1.9.1')

from scipy import misc


class Controller(BoxLayout):
    def __init__(self):
        super(Controller, self).__init__()
        self.ids.file_chooser.rootpath = PATH
        self.ids.slider.max = SLIDER_MAX
        self.ids.slider.value = SLIDER_MAX

    def first_button_clicked(self):
        global image
        self.ids.first_image.source = self.ids.file_chooser.selection[0]
        self.ids.first_image.reload()
        image = misc.imread(self.ids.file_chooser.selection[0], flatten=1)
        image = scipy.misc.imresize(image, (len(image) // 5, len(image[0]) // 5))

    def second_button_clicked(self):
        global image, sinogram, RANGE, STEPS, R, HALF_DETECTORS, WIDTH, HEIGHT, DETECTORS, STEP
        RANGE = float(self.ids.detectors_range_input.text)*math.pi/180
        DETECTORS = int(self.ids.detectors_number_input.text)
        STEPS = int(self.ids.steps_input.text)
        STEP = math.pi / STEPS
        R = (len(image) ** 2 + len(image[0]) ** 2) ** 0.5
        HALF_DETECTORS = DETECTORS // 2
        WIDTH = len(image[0]) - 1
        HEIGHT = len(image) - 1
        sinogram = build_sinogram(image, self)
        for i in range(1,SLIDER_MAX+1):
            misc.imsave("sinogram_{0}.jpg".format(i), sinogram[:int(STEPS*i/SLIDER_MAX)])
        self.ids.second_image.source = 'sinogram_{0}.jpg'.format(SLIDER_MAX)
        self.ids.second_image.reload()

    def third_button_clicked(self):
        recoveredImage = recover_image(sinogram)
        self.ids.third_image.source = "recovered_image_{0}.jpg".format(SLIDER_MAX)
        self.ids.third_image.reload()

    def slider_touched_up(self):
        value = self.ids.slider.value
        self.ids.second_image.source = "sinogram_{0}.jpg".format(value)
        self.ids.third_image.source = "recovered_image_{0}.jpg".format(value)
        self.ids.second_image.reload()
        self.ids.third_image.reload()


class ActionApp(App):
    def build(self):
        return Controller()



class SinogramExecutor:
    result = 0
    pixel_count = 0
    image = None

    def __init__(self, image):
        self.image = image

    def perform(self, y, x):
        self.pixel_count += 1
        self.result += image[y][x]

    def return_result(self):
        if self.pixel_count == 0:
            return 0
        return int(self.result / self.pixel_count)

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

def build_sinogram(image, self):
    sinogram = []
    for i in range(int(STEPS)): # * (self.ids.first_image_slider.value / 4))):
        middle_angle = i * STEP
        projection = []
        for ray in range(-HALF_DETECTORS, HALF_DETECTORS, 1):
            shift_angle = ray * RANGE / DETECTORS
            start_point = compute_coordinates(middle_angle + shift_angle)
            end_point = compute_coordinates(middle_angle + math.pi - shift_angle)
            projection.append(bresenhamLine(start_point, end_point, SinogramExecutor(image)))
        sinogram.append(projection)
        # if i % STEPS/15:
        #     misc.imsave("sinogram.jpg", sinogram)
        #     self.ids.second_image.source = 'sinogram.jpg'
        #     self.ids.second_image.reload()
    return sinogram

def recover_image(sinogram):
    recoveredImage = [[0 for x in range(len(image[0]))] for y in range(len(image))]
    for z in range(SLIDER_MAX):
        CHUNK = STEPS // SLIDER_MAX
        for i in range(z*CHUNK, (z+1) * CHUNK):
            middle_angle = i * STEP
            for ray in range(-HALF_DETECTORS, HALF_DETECTORS, 1):
                shift_angle = ray * RANGE / DETECTORS
                start_point = compute_coordinates(middle_angle + shift_angle)
                end_point = compute_coordinates(middle_angle + math.pi - shift_angle)
                value = sinogram[i][ray + HALF_DETECTORS]
                recoveredImage = bresenhamLine(start_point, end_point, RecoveryExecutor(recoveredImage, value))

        # filtered_image = None
        # filtered_image = cv2.bilateralFilter(np.asarray(deepcopy(recoveredImage)), 15, 80, 80)
        misc.imsave("recovered_image_{0}.jpg".format(z+1), recoveredImage)
    return recoveredImage


def filtering(image):
    #return image
    return cv2.blur(np.asarray(image), (5, 5)) #cv2.filter2D(image, -1, kernel)

if __name__ == '__main__':

    image = []
    sinogram = []
    R, HALF_DETECTORS, WIDTH, HEIGHT, STEPS, STEP, RANGE, DETECTORS, SLIDER_MAX = 0, 0, 0, 0, 0, 0, 0, 0, 10
    PATH = 'zdjecia'
    Window.fullscreen = True
    myApp = ActionApp()
    myApp.run()