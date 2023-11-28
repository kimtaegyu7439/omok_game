import pygame, sys
from pygame.locals import *
from rule import *

bg_color = (128, 128, 128)
black = (0, 0, 0)
blue = (0, 50, 255)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 200, 0)

window_width = 800
window_height = 500
board_width = 500
grid_size = 30

fps = 60
fps_clock = pygame.time.Clock()


def main():
    pygame.init()
    surface = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Omok game")
    surface.fill(bg_color)

    omok = Omok(surface)
    menu = Menu(surface)
    sound = pygame.mixer.Sound("오목의 달인 배경음악.mp3")
    sound.play(-1)
    while True:
        run_game(surface, omok, menu)
        menu.is_continue(omok)


def run_game(surface, omok, menu):
    omok.init_game()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                menu.terminate()
            elif event.type == MOUSEBUTTONUP:
                if not omok.check_board(event.pos):
                    if menu.check_rect(event.pos, omok):
                        omok.init_game()

        if omok.is_gameover:
            return

        pygame.display.update()
        fps_clock.tick(fps)


class Omok(object):
    def __init__(self, surface): # 한번 실행되었을때 이후 초기화가 필요하지 않은 변수들
        self.board = [[0 for i in range(board_size)] for j in range(board_size)]
        self.menu = Menu(surface)
        self.rule = Rule(self.board)
        self.surface = surface
        self.pixel_coords = []
        self.set_coords()
        self.set_image_font()
        self.is_show = True

    def init_game(self): # 매 게임마다 초기화가 필요한 변수와 함수들을 모아놓은 함수
        self.turn = black_stone # 현재 누구의 turn인지 표시(검은돌 먼저)
        self.draw_board() # 게임이 끝나고 보드를 다시 그리는 함수
        self.menu.show_msg(empty) # 게임이 끝난 결과를 지워주기 위한 함수
        self.init_board() # 보드에 저장된 데이터를 초기화 하는 함수
        self.coords = [] # 취소, 재실행할 수 있도록 좌표저장
        self.redos = []
        self.id = 1 # 몇수가 두어졌는지 기록하는 변수
        self.is_gameover = False # 게임 종료여부 저장할 변수
        self.is_forbidden = False # 바둑돌 위 숫자 제거여부 확인 변수

    def set_image_font(self): # 이미지 폰트 생성 함수
        black_img = pygame.image.load('image/black.png')
        white_img = pygame.image.load('image/white.png')
        last_w_img = pygame.image.load('image/white_a.png')
        last_b_img = pygame.image.load('image/black_a.png')
        self.last_w_img = pygame.transform.scale(last_w_img, (grid_size, grid_size)) # 흰돌이 가장 최근에 놓인 위치를 표시하는 사진
        self.last_b_img = pygame.transform.scale(last_b_img, (grid_size, grid_size)) # 검은돌이 가장 최근에 놓인 위치를 표시하는 사진
        self.board_img = pygame.image.load('image/board.png')
        self.forbidden_img = pygame.image.load('image/forbidden.png') # 금수표시 이미지
        self.font = pygame.font.Font("freesansbold.ttf", 14)
        self.black_img = pygame.transform.scale(black_img, (grid_size, grid_size))
        self.white_img = pygame.transform.scale(white_img, (grid_size, grid_size))

    def init_board(self): # 보드를 0으로 초기화
        for y in range(board_size):
            for x in range(board_size):
                self.board[y][x] = 0

    def draw_board(self): # 보드의 이미지를 표시
        self.surface.blit(self.board_img, (0, 0))

    def draw_image(self, img_index, x, y): # 바둑돌을 그리는 함수
        img = [self.black_img, self.white_img, self.last_b_img, self.last_w_img, self.forbidden_img]
        self.surface.blit(img[img_index], (x, y))

    def show_number(self, x, y, stone, number): # 바둑돌의 번호를 보여주는 함수
        colors = [white, black, red, red]
        color = colors[stone]
        self.menu.make_text(self.font, str(number), color, None, y + 15, x + 15, 1)

    def hide_numbers(self): # 바둑돌 위의 번호를 지워주는 함수
        for i in range(len(self.coords)): # 전체 바둑돌 위에 이미지를 다시 그려줌
            x, y = self.coords[i]
            self.draw_image(i % 2, x, y)
        if self.coords: # 마지막 바둑돌을 표시하기 위해 index + 2
            x, y = self.coords[-1]
            self.draw_image(i % 2 + 2, x, y)

    def show_numbers(self):
        for i in range(len(self.coords)): # 바둑돌 숫자 표시
            x, y = self.coords[i]
            self.show_number(x, y, i % 2, i + 1)
        if self.coords:
            x, y = self.coords[-1] # 마지막 바둑돌은 빨간색으로 숫자표시 index + 2
            self.draw_image(i % 2, x, y)
            self.show_number(x, y, i % 2 + 2, i + 1)

    def check_forbidden(self):
        if self.turn == black_stone:
            coords = self.rule.get_forbidden_points(self.turn)
            while coords:
                x, y = coords.pop()
                x, y = x * grid_size + 25, y * grid_size + 25
                self.draw_image(4, x, y)
            self.is_forbidden = True

    def draw_stone(self, coord, stone, increase):
        if self.is_forbidden:
            self.draw_board()
        x, y = self.get_point(coord) # 좌표를 픽셀좌표로 바꿔서 반환해줌
        self.board[y][x] = stone
        self.hide_numbers()
        if self.is_show: # 숫자를 보여주는 형태로 그림
            self.show_numbers()
        self.id += increase # 몇수가 놓여졌는지 체크
        self.turn = 3 - self.turn
        self.check_forbidden()

    def undo(self):
        if not self.coords: # 좌표가 없는 경우 삭제 불가이므로 return
            return
        self.draw_board() # 보드를 다시 그림
        coord = self.coords.pop() # 좌표중 하나를 삭제
        self.redos.append(coord) # redo를 위해 삭제된 좌표를 redos list에 추가
        self.draw_stone(coord, empty, -1) # 좌표가 하나 감소했기 때문에 increase에 -1을 넣어줌

    def undo_all(self): # 모든 좌표를 지우는 함수
        if not self.coords: # 좌표가 없다면 return반환
            return
        self.id = 1
        self.turn = black_stone
        while self.coords: # 좌표가 없어질 때까지 반복하며 삭제 좌표 redo list에 넣어줌
            coord = self.coords.pop()
            self.redos.append(coord)
        self.init_board() # 좌표를 다시 그려줌
        self.draw_board()

    def redo(self):
        if not self.redos: # 삭제된 좌표가 없을 경우 return
            return
        coord = self.redos.pop() # 좌표 삭제 후
        self.coords.append(coord) # 좌표를 추가
        self.draw_stone(coord, self.turn, 1) # 삭제한 좌표의 돌을 그려넣음

    def set_coords(self): # 픽셀의 좌표를 구하는 함수
        for y in range(board_size):
            for x in range(board_size):
                self.pixel_coords.append((x * grid_size + 25, y * grid_size + 25))

    def get_coord(self, pos): # 마우스 포인터를 찾는 코드
        for coord in self.pixel_coords:
            x, y = coord
            rect = pygame.Rect(x, y, grid_size, grid_size)
            if rect.collidepoint(pos):
                return coord
        return None

    def get_point(self, coord): # 이 함수는 픽셀 좌표를 board list에 사용될 순서 좌표로 바꿔서 return
        x, y = coord
        x = (x - 25) // grid_size
        y = (y - 25) // grid_size
        return x, y

    def check_board(self, pos): # 마우스 클릭이 된 부분을 확인하는 함수
        coord = self.get_coord(pos)
        if not coord: # 보드가 아니라면 False 반환
            return False
        x, y = self.get_point(coord)
        if self.board[y][x] != empty: # 비어있는 부분이 아니라면  True반환
            print("occupied")
            return True

        if self.turn == black_stone: # 검은 돌 차례
            if self.rule.forbidden_point(x, y, self.turn): # 해당 좌표가 금수라면 True반환
                print("forbidden point")
                return True

        self.coords.append(coord) # 모든 부분에 해당 x이므로 좌표를 추가한 뒤 바둑돌을 놓음
        self.draw_stone(coord, self.turn, 1)
        if self.check_gameover(coord, 3 - self.turn): #게임이 끝났다면 게임끝
            self.is_gameover = True
        if len(self.redos): # 게임이 끝났다면 redos list를 비워줘야함
            self.redos = []
        return True

    def check_gameover(self, coord, stone): # 게임이 끝났는지 확인하는 함수
        x, y = self.get_point(coord)
        if self.id > board_size * board_size: # 바둑돌이 모든 곳에 채워져 있을 경우
            self.show_winner_msg(stone)
            return True
        elif self.rule.is_gameover(x, y, stone): # rule class로 게임 끝 확인
            self.show_winner_msg(stone)
            return True
        return False

    def show_winner_msg(self, stone): # 이긴 것을 보여주는 함수
        for i in range(3):
            self.menu.show_msg(stone)
            pygame.display.update()
            pygame.time.delay(200)
            self.menu.show_msg(empty)
            pygame.display.update()
            pygame.time.delay(200)
        self.menu.show_msg(stone)


class Menu(object):
    def __init__(self, surface):
        self.font = pygame.font.Font('freesansbold.ttf', 20)
        self.surface = surface
        self.draw_menu()

    def draw_menu(self):
        top, left = window_height - 30, window_width - 200
        self.new_rect = self.make_text(self.font, 'New Game', blue, None, top - 30, left)
        self.quit_rect = self.make_text(self.font, 'Quit Game', blue, None, top, left)
        self.show_rect = self.make_text(self.font, 'Hide Number  ', blue, None, top - 60, left)
        self.undo_rect = self.make_text(self.font, 'Undo', blue, None, top - 150, left)
        self.uall_rect = self.make_text(self.font, 'Undo All', blue, None, top - 120, left)
        self.redo_rect = self.make_text(self.font, 'Redo', blue, None, top - 90, left)

    def show_msg(self, msg_id):
        msg = {
            empty: '                                    ',
            black_stone: 'Black win!!!',
            white_stone: 'White win!!!',
            tie: 'Tie',
        }
        center_x = window_width - (window_width - board_width) // 2
        self.make_text(self.font, msg[msg_id], black, bg_color, 30, center_x, 1)

    def make_text(self, font, text, color, bgcolor, top, left, position=0):
        surf = font.render(text, False, color, bgcolor)
        rect = surf.get_rect()
        if position:
            rect.center = (left, top)
        else:
            rect.topleft = (left, top)
        self.surface.blit(surf, rect)
        return rect

    def show_hide(self, omok):
        top, left = window_height - 90, window_width - 200
        if omok.is_show:
            self.make_text(self.font, 'Show Number', blue, bg_color, top, left)
            omok.hide_numbers()
            omok.is_show = False
        else:
            self.make_text(self.font, 'Hide Number  ', blue, bg_color, top, left)
            omok.show_numbers()
            omok.is_show = True

    def check_rect(self, pos, omok):
        if self.new_rect.collidepoint(pos):
            return True
        elif self.show_rect.collidepoint(pos):
            self.show_hide(omok)
        elif self.undo_rect.collidepoint(pos):
            omok.undo()
        elif self.uall_rect.collidepoint(pos):
            omok.undo_all()
        elif self.redo_rect.collidepoint(pos):
            omok.redo()
        elif self.quit_rect.collidepoint(pos):
            self.terminate()
        return False

    def terminate(self):
        pygame.quit()
        sys.exit()

    def is_continue(self, omok):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.terminate()
                elif event.type == MOUSEBUTTONUP:
                    if (self.check_rect(event.pos, omok)):
                        return
            pygame.display.update()
            fps_clock.tick(fps)


if __name__ == '__main__':
    main()
