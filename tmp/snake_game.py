import pygame
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Game constants
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE
FPS = 5

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.length = 3
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.body = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = Direction.RIGHT
        self.grow_pending = 0

    def move(self):
        head_x, head_y = self.body[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)

        self.body.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1
            self.length += 1
        else:
            self.body.pop()

    def change_direction(self, new_direction):
        # Prevent moving in opposite direction
        dx, dy = self.direction.value
        new_dx, new_dy = new_direction.value
        if (dx + new_dx, dy + new_dy) != (0, 0):
            self.direction = new_direction

    def grow(self):
        self.grow_pending += 1

    def check_collision(self):
        head_x, head_y = self.body[0]

        # Check wall collision
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            return True

        # Check self collision
        if self.body[0] in self.body[1:]:
            return True

        return False

    def draw(self, surface):
        for i, (x, y) in enumerate(self.body):
            color = GREEN if i == 0 else BLUE
            pygame.draw.rect(surface, color, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE - 2, GRID_SIZE - 2))

class Food:
    def __init__(self):
        self.position = self.generate_position()

    def generate_position(self, snake_body=None):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if snake_body is None or (x, y) not in snake_body:
                return (x, y)

    def respawn(self, snake_body):
        self.position = self.generate_position(snake_body)

    def draw(self, surface):
        x, y = self.position
        # Try a system emoji-supporting font
        try:
            big_font = pygame.font.SysFont("Segoe UI Emoji", GRID_SIZE)
        except:
            big_font = pygame.font.Font(None, GRID_SIZE)  # fallback
        
        apple = big_font.render("🍎", True, (255, 0, 0))
        rect = apple.get_rect(center=(x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2))
        surface.blit(apple, rect)        

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Snake Game')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.reset()

    def reset(self):
        self.snake = Snake()
        self.food = Food()
        self.score = 0
        self.game_over = False

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.reset()
                else:
                    if event.key == pygame.K_UP:
                        self.snake.change_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction(Direction.DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction(Direction.RIGHT)

        return True

    def update(self):
        if not self.game_over:
            self.snake.move()

            # Check if snake ate food
            if self.snake.body[0] == self.food.position:
                self.snake.grow()
                self.score += 10
                self.food.respawn(self.snake.body)

            # Check collision
            if self.snake.check_collision():
                self.game_over = True

    def draw_grid(self):
        grid_color = (40, 40, 40)  # A subtle dark gray
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, grid_color, (0, y), (WINDOW_WIDTH, y))

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_grid()  # Draw the grid first

        if not self.game_over:
            self.snake.draw(self.screen)
            self.food.draw(self.screen)

            # Draw score
            score_text = self.font.render(f'Score: {self.score}', True, WHITE)
            self.screen.blit(score_text, (10, 10))
        else:
            # Draw game over screen
            game_over_text = self.font.render('Game Over!', True, WHITE)
            score_text = self.font.render(f'Final Score: {self.score}', True, WHITE)
            restart_text = self.font.render('Press SPACE to restart', True, WHITE)

            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
            score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))

            self.screen.blit(game_over_text, text_rect)
            self.screen.blit(score_text, score_rect)
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
