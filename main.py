import pygame
import random
import pickle
import subprocess
import os
import sys
import cv2
# Функция для синхронизации с GitHub
def sync_with_github():
    try:
        # Проверяем, существует ли папка .git (чтобы убедиться, что это репозиторий)
        if not os.path.exists(".git"):
            print("Папка .git не найдена. Инициализация нового репозитория...")
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "remote", "add", "origin", "https://github.com/LikeProgramChel/Tetris-AI.git"], check=True)

        # Получаем последние изменения с GitHub
        print("Получение изменений с GitHub...")
        subprocess.run(["git", "fetch", "origin"], check=True)
        subprocess.run(["git", "reset", "--hard", "origin/master"], check=True)
        print("Синхронизация завершена.")
        sys.exit()
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при синхронизации с GitHub: {e}")
        sys.exit(1)

# Синхронизация при запуске программы
sync_with_github()

# Остальной код игры...
colors = [
    (255, 255, 255),
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
]

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
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])

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

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation

    def increase_level(self):
        self.level += 1
        self.speed = fps // self.level // 2

    def save_game(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
    def restaer(self):
        game.__init__(20, 10)

    @staticmethod
    def load_game(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

# Initialize the game engine
pygame.init()

# Initialize the mixer module for sound
pygame.mixer.init()

# Load and play background music
pygame.mixer.music.load('background_music.mp3')
pygame.mixer.music.play(-1)  # -1 means the music will loop indefinitely

# Define some colors
WHITE = (0, 0, 0)
BLACK = (255, 255, 255)
GRAY = (128, 128, 128)
BUTTON_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (150, 150, 150)

size = (1000, 600)  # Увеличиваем ширину экрана для боковой панели
screen = pygame.display.set_mode(size)

pygame.display.set_caption("Tetris")

# Loop until the user clicks the close button.
done = False
clock = pygame.time.Clock()
fps = 25
game = Tetris(20, 10)
counter = 0

pressing_down = False

# Параметры кнопок
button_width = 200
button_height = 50
button_x = 820  # Позиция кнопок по X
button_y1 = 100  # Позиция первой кнопки по Y
button_y2 = 200  # Позиция второй кнопки по Y
button_y3 = 300

def draw_button(screen, x, y, width, height, text, hover):
    color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
    pygame.draw.rect(screen, color, [x, y, width, height])
    font = pygame.font.SysFont('Calibri', 25, True, False)
    text_surface = font.render(text, True, BLACK)
    screen.blit(text_surface, (x + 10, y + 10))

while not done:
    if not game.paused:
        if game.figure is None:
            game.new_figure()
        counter += 1
        if counter > 100000:
            counter = 0

        if counter % game.speed == 0 or pressing_down:
            if game.state == "start":
                game.go_down()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                game.rotate()
            if event.key == pygame.K_DOWN:
                pressing_down = True
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
            if event.key == pygame.K_SPACE:
                game.go_space()
            if event.key == pygame.K_ESCAPE:
                game.__init__(20, 10)
            if event.key == pygame.K_p:
                game.paused = not game.paused
            if event.key == pygame.K_l:
                game.increase_level()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # Проверка клика по кнопке "Сохранить игру"
            if button_x <= mouse_pos[0] <= button_x + button_width and button_y1 <= mouse_pos[1] <= button_y1 + button_height:
                game.save_game('savegame.pkl')
            # Проверка клика по кнопке "Загрузить игру"
            if button_x <= mouse_pos[0] <= button_x + button_width and button_y2 <= mouse_pos[1] <= button_y2 + button_height:
                game = Tetris.load_game('savegame.pkl')
            if button_x <= mouse_pos[0] <= button_x + button_width and button_y3 <= mouse_pos[1] <= button_y3 + button_height:
                game.__init__(20, 10)


    if event.type == pygame.KEYUP:
        if event.key == pygame.K_DOWN:
            pressing_down = False

    screen.fill(WHITE)

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

    # Отрисовка кнопок
    mouse_pos = pygame.mouse.get_pos()
    hover_save = button_x <= mouse_pos[0] <= button_x + button_width and button_y1 <= mouse_pos[1] <= button_y1 + button_height
    hover_load = button_x <= mouse_pos[0] <= button_x + button_width and button_y2 <= mouse_pos[1] <= button_y2 + button_height
    hover_reset = button_x <= mouse_pos[0] <= button_x + button_width and button_y3 <= mouse_pos[1] <= button_y3 + button_height

    draw_button(screen, button_x, button_y1, button_width, button_height, "Сохранить игру", hover_save)
    draw_button(screen, button_x, button_y2, button_width, button_height, "Загрузить игру", hover_load)

    draw_button(screen, button_x, button_y3, button_width, button_height, "Рестарт", hover_reset)

    # Отрисовка счета и состояния игры
    font = pygame.font.SysFont('Calibri', 25, True, False)
    font1 = pygame.font.SysFont('Calibri', 65, True, False)
    text = font.render("Счет: " + str(game.score), True, BLACK)
    text_game_over = font1.render("Вы проиграли", True, (255, 125, 0))
    text_game_over1 = font1.render("Нажмите ESC", True, (255, 215, 0))

    screen.blit(text, [0, 0])
    if game.state == "gameover":
        screen.blit(text_game_over, [20, 200])
        screen.blit(text_game_over1, [25, 265])

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
