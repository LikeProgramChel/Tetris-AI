import pygame
import random
import pickle
import subprocess
import os
import sys
import cv2
import mediapipe as mp
import math
import numpy as np
import time


# Класс для распознавания рук
class handDetector():
    def __init__(self, mode=False, maxHands=2, modelComplexity=1, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.modelComplexity = modelComplexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modelComplexity, self.detectionCon,
                                        self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax

            if draw:
                cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20), (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)
        return self.lmList, bbox

    def fingersUp(self):
        fingers = []

        # Thumb
        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 Fingers
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers


# Класс для фигур в Тетрисе
class Figure:
    x = 0
    y = 0

    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]],
        [[4, 5, 9, 10], [2, 6, 5, 9]],
        [[6, 7, 9, 10], [1, 5, 6, 10]],
        [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
        [[1, 2, 5, 6]],
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(self.figures) - 1)
        self.color = random.randint(1, len(colors) - 1)
        self.rotation = 0

    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        time.sleep(0.5)
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])


# Класс для игры Тетрис
class Tetris:
    def __init__(self, height, width):
        self.level = 1
        self.score = 0
        self.state = "start"
        self.field = []
        self.height = 0
        self.width = 0
        self.x = 100
        self.y = 60
        self.zoom = 20
        self.figure = None
        self.paused = False
        self.speed = fps // self.level // 2

        self.height = height
        self.width = width
        self.field = []
        self.score = 0
        self.state = "start"
        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    def new_figure(self):
        self.figure = Figure(3, 0)

    def intersects(self):
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y > self.height - 1 or \
                            j + self.figure.x > self.width - 1 or \
                            j + self.figure.x < 0 or \
                            self.field[i + self.figure.y][j + self.figure.x] > 0:
                        intersection = True
        return intersection

    def break_lines(self):
        lines = 0
        for i in range(1, self.height):
            zeros = 0
            for j in range(self.width):
                if self.field[i][j] == 0:
                    zeros += 1
            if zeros == 0:
                lines += 1
                for i1 in range(i, 1, -1):
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]
        if lines > 0:
            pass
        self.score += lines ** 2

    def go_space(self):
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

    def go_down(self):
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()


    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        self.break_lines()
        self.new_figure()
        if self.intersects():
            self.state = "gameover"
            game_over_sound.play()  # Звук завершения игры

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if not self.intersects():
            rotate_sound.play()  # Звук вращения фигуры
        else:
            self.figure.rotation = old_rotation

    def increase_level(self):
        self.level += 1
        self.speed = fps // self.level // 2

    def save_game(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    def restart(self):
        self.__init__(20, 10)

    @staticmethod
    def load_game(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)


# Класс для кнопок
class Button:
    def __init__(self, x, y, width, height, text, font, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen):
        if self.is_hovered:
            pygame.draw.rect(screen, self.hover_color, self.rect)
        else:
            pygame.draw.rect(screen, self.color, self.rect)

        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)


# Функция для создания кнопок меню
def create_menu_buttons():
    button_width = 200
    button_height = 50
    button_x = size[0] // 2 - button_width // 2
    buttons = [
        Button(button_x, 200, button_width, button_height, "Новая игра", font, BUTTON_COLOR, BUTTON_HOVER_COLOR),
        Button(button_x, 270, button_width, button_height, "Загрузить игру", font, BUTTON_COLOR, BUTTON_HOVER_COLOR),
        Button(button_x, 340, button_width, button_height, "Выход", font, BUTTON_COLOR, BUTTON_HOVER_COLOR),
    ]
    return buttons


# Функция для отображения главного меню
def main_menu(screen, buttons):
    while True:
        screen.blit(background, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        for button in buttons:
            button.check_hover(mouse_pos)
            button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.is_hovered:
                        if button.text == "Новая игра":
                            return "new_game"
                        elif button.text == "Загрузить игру":
                            return "load_game"
                        elif button.text == "Выход":
                            return "quit"

        pygame.display.flip()
        clock.tick(fps)


# Инициализация игры
pygame.init()
pygame.mixer.init()
pygame.mixer.music.load('background_music.mp3')
pygame.mixer.music.play(-1)

# Загрузка звуковых эффектов

rotate_sound = pygame.mixer.Sound("rotate.wav")
game_over_sound = pygame.mixer.Sound("game_over.wav")

# Инициализация детектора рук
detector = handDetector()

# Определение цветов
colors = [
    (255, 255, 255),
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
]

WHITE = (0, 0, 0)
BLACK = (255, 255, 255)
GRAY = (128, 128, 128)
BUTTON_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (150, 150, 150)

size = (1000, 600)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Tetris")

# Загрузка фона
background = pygame.image.load("background.jpg")
background = pygame.transform.scale(background, size)

# Загрузка пользовательского шрифта
font_path = "font.ttf"
font = pygame.font.Font(font_path, 25)
font1 = pygame.font.Font(font_path, 65)

# Основной цикл игры
done = False
clock = pygame.time.Clock()
fps = 15
game = Tetris(20, 10)
counter = 0

# Захват видео с веб-камеры
cap = cv2.VideoCapture(0)

# Создание кнопок меню
buttons = create_menu_buttons()
menu_result = main_menu(screen, buttons)

if menu_result == "new_game":
    game = Tetris(20, 10)
elif menu_result == "load_game":
    game = Tetris.load_game("save.pkl")
elif menu_result == "quit":
    pygame.quit()
    sys.exit()

while not done:
    if not game.paused:
        if game.figure is None:
            game.new_figure()
        counter += 1
        if counter > 100000:
            counter = 0

        if counter % (fps // 2) == 0:
            if game.state == "start":
                game.go_down()

    # Захват изображения с веб-камеры
    success, img = cap.read()
    img = detector.findHands(img, draw=True)
    lmList, bbox = detector.findPosition(img, draw=True)

    if len(lmList) != 0:
        fingers = detector.fingersUp()

        # Управление жестами
        if fingers[1] == 1 and fingers[4] == 0:
            game.go_side(-1)
        elif fingers[1] == 0 and fingers[4] == 1:
            game.go_side(1)
        elif fingers[1] == 1 and fingers[4] == 1:
            game.rotate()

    # Преобразование изображения из OpenCV в формат Pygame
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = np.rot90(img)
    img = pygame.surfarray.make_surface(img)
    img = pygame.transform.scale(img, (320, 240))

    # Отрисовка фона
    screen.blit(background, (0, 0))

    # Отрисовка изображения с камеры
    screen.blit(img, (size[0] - 320, 0))

    # Отрисовка игрового поля
    for i in range(game.height):
        for j in range(game.width):
            pygame.draw.rect(screen, GRAY, [game.x + game.zoom * j, game.y + game.zoom * i, game.zoom, game.zoom], 1)
            if game.field[i][j] > 0:
                pygame.draw.rect(screen, colors[game.field[i][j]],
                                 [game.x + game.zoom * j + 1, game.y + game.zoom * i + 1, game.zoom - 2, game.zoom - 1])

    if game.figure is not None:
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.figure.image():
                    pygame.draw.rect(screen, colors[game.figure.color],
                                     [game.x + game.zoom * (j + game.figure.x) + 1,
                                      game.y + game.zoom * (i + game.figure.y) + 1,
                                      game.zoom - 2, game.zoom - 2])

    # Отрисовка счета и состояния игры
    text = font.render("Счет: " + str(game.score), True, BLACK)
    text_game_over = font1.render("Вы проиграли", True, (255, 125, 0))
    text_game_over1 = font1.render("Нажмите ESC", True, (255, 215, 0))

    screen.blit(text, [0, 0])
    if game.state == "gameover":
        screen.blit(text_game_over, [20, 200])
        screen.blit(text_game_over1, [25, 265])

    pygame.display.flip()
    clock.tick(fps)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game.restart()
            if event.key == pygame.K_p:
                game.paused = not game.paused

# Освобождение ресурсов
cap.release()
cv2.destroyAllWindows()
pygame.quit()
