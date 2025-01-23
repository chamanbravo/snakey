import os
import sys
import time
from dataclasses import dataclass
from enum import Enum, auto
from random import randint
from typing import Optional

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass
class Point:
    x: int
    y: int

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)


class Snake:
    DIRECTION_VECTORS = {
        Direction.UP: Point(-1, 0),
        Direction.DOWN: Point(1, 0),
        Direction.LEFT: Point(0, -1),
        Direction.RIGHT: Point(0, 1),
    }

    def __init__(self, body, direction):
        self.body = body
        self.direction = direction

    @property
    def head(self) -> Point:
        return self.body[-1]

    @property
    def tail(self) -> Point:
        return self.body[0]


class Apple:
    def __init__(self, position):
        self.position = position


class Game:
    CONTROLS = {
        "w": Direction.UP,
        "s": Direction.DOWN,
        "a": Direction.LEFT,
        "d": Direction.RIGHT,
    }

    def __init__(self, w: int, h: int):
        self.height = h
        self.width = w
        self.canvas = [[" " for _ in range(self.width)] for _ in range(self.height)]
        self.speed = 0.5
        self.score = 0
        self.game_over = False
        self.snake = Snake(
            [Point(x, y) for (x, y) in [(1, 3), (2, 3), (3, 3), (4, 3)]], Direction.DOWN
        )
        self.apple = Apple(Point(20, 20))

    def update_score(self):
        print("\033[1;4H" + f"Score: {self.score}")

    def move(self, new_direction: Optional[Direction] = None):
        if not new_direction:
            new_direction = self.snake.direction

        head = self.snake.head
        new_head = head + self.snake.DIRECTION_VECTORS[new_direction]

        self.validate_direction(new_head)
        self.snake.body.append(new_head)

        tail = self.snake.tail
        print(f"\033[{tail.x+1};{tail.y+1}H", end="")
        print(" ")

        self.snake.body.pop(0)
        self.snake.direction = new_direction

        for i in self.snake.body[:-1]:
            print(f"\033[{i.x + 1};{i.y + 1}H", end="")
            print(f"{GREEN}0{RESET}")

        print(f"\033[{new_head.x + 1};{new_head.y + 1}H", end="")
        print(f"{GREEN}X{RESET}")

    def get_movement(self, key: str):
        opposite_directions = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

        if (
            key.lower() not in ["w", "a", "s", "d"]
            or (
                (new_direction := self.CONTROLS[key.lower()])
                == opposite_directions[self.snake.direction]
            )
            or new_direction == self.snake.direction
        ):
            return

        self.move(new_direction)

    def validate_direction(self, new_head: Point):
        if (
            new_head.x <= 0
            or new_head.x >= self.height - 1
            or new_head.y <= 0
            or new_head.y >= self.width - 1
        ):
            self.game_over = True
            return

        if any(b.x == new_head.x and b.y == new_head.y for b in self.snake.body[:-1]):
            self.game_over = True
            return

        if new_head == self.apple.position:
            self.spawn_apple()
            self.snake.body.insert(
                0, Point(self.snake.tail.x + 1, self.snake.tail.y + 1)
            )
            self.speed = max(0.05, self.speed * 0.9)
            self.score += 1
            self.update_score()

    def spawn_apple(self):
        x = randint(1, 40)
        y = randint(1, 40)
        self.apple.position = Point(x, y)

        print(f"\033[{x+1};{y+1}H", end="")
        print(f"{RED}*{RESET}")

    def render(self):
        snake_head = self.snake.head
        apple = self.apple.position

        for row in range(self.height):
            for col in range(self.width):
                if row == 0 or row == self.height - 1:
                    self.canvas[row][col] = "─"
                elif col == 0 or col == self.width - 1:
                    self.canvas[row][col] = "│"
                if (Point(row, col)) in self.snake.body:
                    self.canvas[row][col] = f"{GREEN}0{RESET}"

        self.canvas[0][0] = "╭"
        self.canvas[0][self.width - 1] = "╮"
        self.canvas[self.height - 1][0] = "╰"
        self.canvas[self.height - 1][self.width - 1] = "╯"
        self.canvas[snake_head.x][snake_head.y] = f"{GREEN}X{RESET}"
        self.canvas[apple.x][apple.y] = f"{RED}*{RESET}"

        score_text = f"Score: {self.score}"
        for i, char in enumerate(score_text):
            self.canvas[0][i + 3] = char

        for row in self.canvas:
            print("".join(row), end="", flush=True)


def get_key():
    if os.name == "nt":
        if msvcrt.kbhit():
            key = msvcrt.getch().decode("utf-8").lower()
            return key
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if dr:
                key = sys.stdin.read(1).lower()
                return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None


if __name__ == "__main__":
    print("\033[?25l", end="")
    size = os.get_terminal_size()
    game = Game(size.columns, size.lines)
    game.render()
    last_update = time.time()

    try:
        while not game.game_over:
            if time.time() - last_update >= game.speed:
                game.move()
                last_update = time.time()

            key = get_key()
            if key and key == "q":
                break
            elif key in Game.CONTROLS:
                game.get_movement(key)

        print("Game Over!")
    finally:
        print("\033[?25h", end="")
