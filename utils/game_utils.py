import pygame
import random
import time
import cv2 as cv
from Pinyin2Hanzi import DefaultDagParams
from Pinyin2Hanzi import dag
import string


'''class Pipa:
    def __init__(self, img, scale, pos):
        self.img = pygame.transform.scale(pygame.image.load(img), scale)
        self.pos = pos'''


class TextBox:
    def __init__(self, w, h, x, y, font=None, callback=None):
        """
        :param w:文本框宽度
        :param h:文本框高度
        :param x:文本框坐标
        :param y:文本框坐标
        :param font:文本框中使用的字体
        :param callback:在文本框按下回车键之后的回调函数
        """
        self.width = w
        self.height = h
        self.x = x
        self.y = y
        self.text = ""  # 文本框内容
        self.callback = callback
        # 创建背景surface
        self.__surface = pygame.Surface((w, h))
        # 如果font为None,那么效果可能不太好，建议传入font，更好调节
        if font is None:
            self.font = pygame.font.SysFont('microsoftyaheimicrosoftyaheiui', 16)
        else:
            self.font = font

        self.dagparams = DefaultDagParams()
        self.state = 0  # 0初始状态 1输入拼音状态
        self.page = 1  # 第几页
        self.limit = 5  # 显示几个汉字
        self.pinyin = ''
        self.word_list = []  # 候选词列表
        self.word_list_surf = None  # 候选词surface
        self.buffer_text = ''  # 联想缓冲区字符串

    def create_word_list_surf(self):
        """
        创建联想词surface
        """
        word_list = [str(index + 1) + '.' + word for index, word in enumerate(self.word_list)]
        text = " ".join(word_list)
        self.word_list_surf = self.font.render(text, True, (255, 255, 255))

    def draw(self, dest_surf):
        # 创建文字surf
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        # 绘制背景色
        dest_surf.blit(self.__surface, (self.x, self.y))
        # 绘制文字
        dest_surf.blit(text_surf, (self.x, self.y + (self.height - text_surf.get_height())),
                       (0, 0, self.width, self.height))
        # 绘制联想词
        if self.state == 1:
            dest_surf.blit(self.word_list_surf,
                           (self.x, self.y + (self.height - text_surf.get_height()) - 30),
                           (0, 0, self.width, self.height)
                           )

    def key_down(self, event):
        unicode = event.unicode
        key = event.key

        # 退位键
        if key == 8:
            self.text = self.text[:-1]
            if self.state == 1:
                self.buffer_text = self.buffer_text[:-1]
            return

        # 切换大小写键
        if key == 301:
            return

        # 回车键
        if key == 13:
            if self.callback:
                self.callback(self.text)
            return

        # print(key)
        # 空格输入中文
        if self.state == 1 and key == 32:
            self.state = 0
            self.text = self.text[:-len(self.buffer_text)] + self.word_list[0]
            self.word_list = []
            self.buffer_text = ''
            self.page = 1
            return

        # 翻页
        if self.state == 1 and key == 61:
            self.page += 1
            self.word_list = self.py2hz(self.buffer_text)
            if len(self.word_list) == 0:
                self.page -= 1
                self.word_list = self.py2hz(self.buffer_text)
            self.create_word_list_surf()
            return

        # 回退
        if self.state == 1 and key == 45:
            self.page -= 1
            if self.page < 1:
                self.page = 1
            self.word_list = self.py2hz(self.buffer_text)
            self.create_word_list_surf()
            return

        # 选字
        if self.state == 1 and key in (49, 50, 51, 52, 53):
            self.state = 0
            if len(self.word_list) <= key - 49:
                return
            self.text = self.text[:-len(self.buffer_text)] + self.word_list[key - 49]
            self.word_list = []
            self.buffer_text = ''
            self.page = 1
            return

        if unicode != "":
            char = unicode
        else:
            char = chr(key)

        if char in string.ascii_letters:
            self.buffer_text += char
            self.word_list = self.py2hz(self.buffer_text)
            self.create_word_list_surf()
            # print(self.buffer_text)
            self.state = 1
        self.text += char

    def safe_key_down(self, event):
        try:
            self.key_down(event)
        except:
            self.reset()

    def py2hz(self, pinyin):
        result = dag(self.dagparams, (pinyin,), path_num=self.limit * self.page)[
                 (self.page - 1) * self.limit:self.page * self.limit]
        data = [item.path[0] for item in result]
        return data

    def reset(self):
        # 异常的时候还原到初始状态
        self.state = 0  # 0初始状态 1输入拼音状态
        self.page = 1  # 第几页
        self.limit = 5  # 显示几个汉字
        self.pinyin = ''
        self.word_list = []  # 候选词列表
        self.word_list_surf = None  # 候选词surface
        self.buffer_text = ''  # 联想缓冲区字符串


class Butterfly:
    def __init__(self, path, scale, pos_start, font, color, arrow):
        self.img = pygame.image.load(path)
        self.scale = scale
        self.img = pygame.transform.scale(self.img, scale)
        self.pos_start = pos_start
        self.pos = pos_start

        self.follow_flag = False
        self.text = font.render("请触碰我！", True, color)
        self.text_pos = (pos_start[0]+200, pos_start[1]-250)

        self.arrow = pygame.transform.scale(pygame.image.load(arrow), (200, 200))
        self.arrow_pos = (pos_start[0]+100, pos_start[1]-200)

    def reset(self):
        self.pos = self.pos_start
        self.follow_flag = False

    def update_follow(self, hand_pos):
        if not self.follow_flag and in_button(hand_pos, self.pos_start, self.scale):
            self.follow_flag = True
        if self.follow_flag:
            self.pos = (hand_pos[0]+100, hand_pos[1]-100)

    def show(self, screen):
        screen.blit(self.img, self.pos)
        if not self.follow_flag:
            screen.blit(self.arrow, self.arrow_pos)
            screen.blit(self.text, self.text_pos)


class DanMuList:
    def __init__(self, left, right, high, bottom):
        self.list = []
        self.pos = []
        self.x_move = []  # x移动速度

        self.left = left
        self.right = right
        self.high = high
        self.bottom = bottom

    def add(self, text, font, color):
        danmu = DanMu(text, font, color)
        rate = random.uniform(1, 2)
        danmu.item = pygame.transform.scale(danmu.item, (int(danmu.item.get_width()*rate),
                                            int(danmu.item.get_height()*rate)))
        self.list.append(danmu.item)
        x = self.right
        y = random.randrange(self.high, self.bottom)
        self.pos.append([x, y])
        x_move = random.randrange(10, 20)
        self.x_move.append(-x_move)

    def move(self):
        if len(self.pos):
            for i in range(len(self.pos)):
                self.pos[i][0] += self.x_move[i]
                if self.pos[i][0]+self.list[i].get_width()//2 < self.left:
                    self.pos[i][0] = self.right

    def show(self, screen):
        self.move()
        if len(self.list):
            for i in range(len(self.list)):
                screen.blit(self.list[i], self.pos[i])


class DanMu:
    def __init__(self, text, font, color):
        self.text = text
        self.font = font
        self.color = color
        self.item = self.create()

    def create(self):
        return self.font.render(self.text, True, self.color)


class RouteOBJ:   # screen3 中的路线类
    def __init__(self, name, pos, font, color, img, halls=[], scale=(300, 300)):
        self.name = name
        self.name_obj = get_text_obj(name, font, color)
        self.pos = pos
        self.halls = halls
        self.scale = scale
        self.max_row = 3  # 每行最大展厅排布量

        self.mouse = False   # 鼠标滑过
        self.mouse_press = False  # 鼠标按下
        self.rect = [pos[0]-10, pos[1]-10]  # rect pos

        self.select_img = img    # 选中后的√
        self.select_img_pos = [pos[0]+int(self.name_obj.get_width()*1.2), pos[1]]

        self.layer2_text_start = None
        self.layer3_text_start = None
        self.layer2_text_end = None
        self.layer3_text_end = None

    def draw_select(self, screen):
        screen.blit(self.select_img, self.select_img_pos)

    def draw_rect(self, screen, color):
        pygame.draw.rect(screen, color, (self.rect,
            (self.scale[0]-self.rect[0], self.scale[1]-self.rect[1])), 5)

    def draw_route_obj(self, screen, halls, font, color):
        layer2, layer3 = self.halls  # 第2、3层的展厅
        layer2_pos = [self.pos[0]+30, self.pos[1]+100]

        self.layer2_text_start = font.render("二层入口", True, color)
        self.layer3_text_start = font.render("三层入口", True, color)
        self.layer2_text_end = font.render("二层出口", True, color)
        self.layer3_text_end = font.render("三层出口", True, color)
        arrow = font.render(" -> ", True, color)

        if len(layer2) > 0:
            screen.blit(self.layer2_text_start, layer2_pos)
            layer2_pos[0] += int(self.layer2_text_start.get_width()*1.1)
            for i in layer2:
                screen.blit(arrow, layer2_pos)
                text = font.render(halls[i-1], True, color)
                screen.blit(text, (layer2_pos[0]+arrow.get_width()+10, layer2_pos[1]))
                layer2_pos[1] += int(text.get_height()*1.1)
            screen.blit(arrow, layer2_pos)
            screen.blit(self.layer2_text_end, (layer2_pos[0]+arrow.get_width()+10, layer2_pos[1]))

        layer3_pos = [self.pos[0]+30, layer2_pos[1]+70]
        if len(layer3) > 0:
            screen.blit(self.layer3_text_start, layer3_pos)
            layer3_pos[0] += int(self.layer3_text_start.get_width() * 1.1)
            for i in layer3:
                screen.blit(arrow, layer3_pos)
                text = font.render(halls[i - 1], True, color)
                screen.blit(text, (layer3_pos[0] + arrow.get_width() + 10, layer3_pos[1]))
                layer3_pos[1] += int(text.get_height() * 1.1)
            screen.blit(arrow, layer3_pos)
            screen.blit(self.layer3_text_end, (layer3_pos[0] + arrow.get_width() + 10, layer3_pos[1]))

    def update_img(self, img):
        self.select_img = img


# hand pose互动
class Hudong:
    def __init__(self, img_path):
        self.img1 = None
        self.img2 = None
        self.rotation = -45
        self.scale = (200, 200)
        self.create_img_rotate(img_path)

        self.rotate_flag = True   # if True, show img1, else show img2
        self.time = 0   # 计时器
        self.time_space = 0.5  # 每0.5秒切换
        self.position = (0, 0)
        self.img = self.img2

        self.activation_flag = False  # 识别到了互动确认手势

    def create_img_rotate(self, path):
        self.img1 = pygame.image.load(path).convert_alpha()
        self.img1 = pygame.transform.scale(self.img1, self.scale)
        self.img2 = pygame.transform.rotate(self.img1, self.rotation)

    def update_show_img(self, position):
        self.position = position
        if self.rotate_flag:
            self.img = self.img1
            self.rotate_flag = False
        else:
            self.img = self.img2
            self.rotate_flag = True


class Hand:
    def __init__(self, path1, path2, rate):
        self.hand = pygame.image.load(path1)
        self.hand = pygame.transform.scale(self.hand, (100, 100))
        self.stone = pygame.image.load(path2)
        self.stone = pygame.transform.scale(self.stone, (100, 100))

        self.pos = None
        self.scale = None
        self.hand_flag = True
        self.show_hand = True

        self.rate = rate

    def update_hand(self, screen):
        if self.hand_flag:
            img = self.hand
        else:
            img = self.stone
        screen.blit(img, self.pos)

    def xyxy2pos(self, xyxy):
        x1, y1, x2, y2 = xyxy
        self.pos = (int((x2+x1)*self.rate[0])//2, int((y2+y1)*self.rate[1])//2)
        self.scale = (x2-x1, y2-y1)


class State:
    def __init__(self):
        self.name = ['cloth', 'sword', 'bottle', 'hand', 'stone']
        self.quant = len(self.name)  # 一共有几个状态量
        self.state = [False for i in range(self.quant)]

        self.xyxy = [[None] for i in range(self.quant)]
        self.time_space = 2  # 检测到为True后持续的秒数
        self.times = [0 for i in range(self.quant)]

    def update_state(self, state, now_time):
        for i in range(self.quant):
            if now_time - self.times[i] > self.time_space:
                self.state[i] = False
                self.xyxy[i] = [None]
                self.times[i] = 0

        if len(state):
            for s in state:
                for i in range(self.quant):
                    if s[0] == self.name[i]:  # 匹配
                        self.state[i] = True
                        self.xyxy[i] = s[1]
                        self.times[i] = now_time


class SuShaDanYi:
    def __init__(self, path1, path2, scale, text_font, text_color):
        self.img1 = pygame.image.load(path1)
        self.img1 = pygame.transform.scale(self.img1, scale)
        self.img1.set_alpha(200)
        self.img2 = pygame.image.load(path2)
        self.img2 = pygame.transform.scale(self.img2, scale)
        self.img2.set_alpha(200)
        self.font = text_font
        self.color = text_color

        self.alpha = 30
        self.time = 0
        self.time_space = 0.05

        # 选项(in choose)
        self.option_scale = (270, 280)
        x, x_sep, y = 1052, 430, 740
        self.option_pos = [(x, y), (x+x_sep, y), (x+x_sep*2, y)]  # 选项的位置
        self.option_show = [False, False, False]
        self.option = [False, True, False]  # 选项的正确与错误
        # text
        self.success = text_font.render("恭喜你答对了！积分 + 1！", True, text_color)
        self.success_flag = False
        self.fail = text_font.render("很抱歉你答错了。请再次选择", True, text_color)
        self.fail_flag = False

        # flags
        self.flag = False  # 互动flag
        self.ask = False  # 启动flag，触发了此flag，启动问答
        self.choose = False  # 第二页，选择合适的衣服

    def reset(self):
        self.alpha = 30
        self.time = 0
        self.time_space = 0.05

        # 选项(in choose)
        self.option_scale = (270, 280)
        x, x_sep, y = 1052, 430, 740
        self.option_pos = [(x, y), (x + x_sep, y), (x + x_sep * 2, y)]  # 选项的位置
        self.option_show = [False, False, False]
        self.option = [False, True, False]  # 选项的正确与错误
        # text
        self.success = self.font.render("恭喜你答对了！积分 + 1！", True, self.color)
        self.success_flag = False
        self.fail = self.font.render("很抱歉你答错了。请再次选择", True, self.color)
        self.fail_flag = False

        # flags
        self.flag = False  # 互动flag
        self.ask = False  # 启动flag，触发了此flag，启动问答
        self.choose = False  # 第二页，选择合适的衣服

    def reset_alpha(self):
        self.alpha = 30
        self.time = 0
        self.img1.set_alpha(self.alpha)
        self.img2.set_alpha(self.alpha)

    def show_up(self, img):
        if self.alpha == 255:
            return img
        else:
            if self.alpha < 245:
                self.alpha += 20
            else:
                self.alpha = 255
            img.set_alpha(self.alpha)
            return img

    def determine(self, screen, pos_at, rect_color, text_pos, mouse_down=False):
        if self.success_flag:
            screen.blit(self.success, text_pos)
        elif self.fail_flag:
            screen.blit(self.fail, text_pos)

        for option in range(len(self.option_pos)):
            pos_start = (self.option_pos[option][0], self.option_pos[option][1])
            pos_end = (self.option_pos[option][0]+self.option_scale[0],
                       self.option_pos[option][1]+self.option_scale[1])
            if self.option_show[option]:
                pygame.draw.rect(screen, rect_color, (pos_start, self.option_scale), 7)

            if in_area(pos_at, pos_start, pos_end):
                pygame.draw.rect(screen, rect_color, (pos_start, self.option_scale), 7)
                if mouse_down:
                    # 重置其他option show的flag
                    for i in range(len(self.option_show)):
                        self.option_show[i] = False

                    self.option_show[option] = True
                    if self.option[option]:
                        self.success_flag = True
                        self.fail_flag = False
                    else:
                        self.success_flag = False
                        self.fail_flag = True


class Sword:
    def __init__(self, path, basic_scale):
        self.sword = pygame.image.load(path)
        self.sword = pygame.transform.scale(self.sword, basic_scale)

    def update_sword(self, screen, pos_at, scale):
        self.sword = pygame.transform.scale(self.sword, scale)
        screen.blit(self.sword, scale)


class Button:
    def __init__(self, text, bg, bg_press, bg_scale, pos, text_font, text_color, text_color_press):
        self.bg = pygame.image.load(bg)
        self.bg_press = pygame.image.load(bg_press)
        self.bg = pygame.transform.scale(self.bg, bg_scale)
        self.bg_press = pygame.transform.scale(self.bg_press, bg_scale)
        self.scale = bg_scale

        self.text = text_font.render(text, True, text_color)
        self.text = pygame.transform.scale(self.text, (int(bg_scale[0]*0.8), int(bg_scale[1]*0.8)))
        self.text_press = text_font.render(text, True, text_color_press)
        self.text_press = pygame.transform.scale(self.text_press, (int(bg_scale[0] * 0.8), int(bg_scale[1] * 0.8)))

        self.pos = pos
        self.text_pos = (int(pos[0]+bg_scale[0]*0.1), int(pos[1]+bg_scale[1]*0.1))

        self.show_flag = True
        self.flag = False
        self.press_flag = False

    def show(self, screen):
        if self.show_flag:
            if self.flag or self.press_flag:
                screen.blit(self.bg_press, self.pos)
                screen.blit(self.text, self.text_pos)
            else:
                screen.blit(self.bg, self.pos)
                screen.blit(self.text_press, self.text_pos)

    def in_button(self, pos_at):
        if self.pos[0] <= pos_at[0] <= self.pos[0]+self.scale[0] and \
                self.pos[1] <= pos_at[1] <= self.pos[1] + self.scale[1]:
            return True
        else:
            return False


class ImgButton:
    def __init__(self, bg, bg_press, bg_scale, pos):
        self.bg = pygame.image.load(bg)
        self.bg_press = pygame.image.load(bg_press)
        self.bg = pygame.transform.scale(self.bg, bg_scale)
        self.bg_press = pygame.transform.scale(self.bg_press, bg_scale)
        self.scale = bg_scale

        self.pos = pos

        self.time = 0
        self.press_space = 0.7  # second

        self.show_flag = True
        self.flag = False
        self.press_flag = False

    def show(self, screen):
        if self.show_flag:
            if self.flag or self.press_flag:
                screen.blit(self.bg_press, self.pos)
            else:
                screen.blit(self.bg, self.pos)

    def in_button(self, pos_at):
        if self.pos[0] <= pos_at[0] <= self.pos[0]+self.scale[0] and \
                self.pos[1] <= pos_at[1] <= self.pos[1] + self.scale[1]:
            return True
        else:
            return False


def get_week_day(date):
    week_day_dict = {
        0: '星期一',
        1: '星期二',
        2: '星期三',
        3: '星期四',
        4: '星期五',
        5: '星期六',
        6: '星期日',
    }
    day = date.weekday()
    return week_day_dict[day]


def text_get(text, text_flag=0):
    if len(text) > text_flag:
        end_flag = False
    else:
        end_flag = True
    return text[:text_flag], end_flag


def in_area(at, pos_start, pos_end):
    if pos_start[0] <= at[0] <= pos_end[0] and pos_start[1] <= at[1] <= pos_end[1]:
        return True
    else:
        return False


def in_button(pos, button_at, button_size):
    x1, y1 = button_at
    x2, y2 = x1+button_size[0], y1+button_size[1]
    if x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2:
        return True
    else:
        return False


def button_state(button_size, not_press_path, pressed_path, press_state):
    if press_state:
        button = pygame.image.load(pressed_path).convert_alpha()
    else:
        button = pygame.image.load(not_press_path).convert_alpha()
    button = pygame.transform.scale(button, button_size)
    button.set_alpha(255)
    return button


def flower_create(flower_items, pos_start_range, pos_end_range, screen_size, times_range):
    img = flower_items[random.randrange(0, len(flower_items))]
    pos_start = random.randrange(pos_start_range[0], pos_start_range[1])
    pos_end = random.randrange(pos_end_range[0], pos_end_range[1])
    if pos_start >= 0:  # pos_start >= 0 时，认为在x轴上，不然在y轴上
        pos_start = [pos_start, 0]
    else:
        pos_start = [0, -pos_start]
    if pos_end >= 0:
        pos_end = [screen_size[0]-pos_end, screen_size[1]]
    else:
        pos_end = [screen_size[0], screen_size[1]+pos_end]
    times = random.randrange(times_range[0], times_range[1])
    distance = (pos_end[0]-pos_start[0], pos_end[1]-pos_start[1])
    movement = (distance[0]//times+1, distance[1]//times+1)
    # rotate = random.randrange(rotate_range[0], rotate_range[1])
    return [img, pos_start, pos_end, movement]


def flower_fly(flower):
    img, pos_at, end_pos, movement = flower
    # img = pygame.transform.rotate(img, rotate)
    if pos_at[0] >= end_pos[0] or pos_at[1] >= end_pos[1]:
        return 0
    pos_at[0] += movement[0]
    pos_at[1] += movement[1]
    return [img, pos_at, end_pos, movement]


def exhibition_setting(path, scale, max_row, pos, sep):
    exhibitions = []
    '''for i in os.listdir(path):
        if i == '.DS_Store':
            continue'''
    for i in range(1, 7):
        img = pygame.image.load(path+'{}.jpg'.format(i)).convert()
        img = pygame.transform.scale(img, scale)
        exhibitions.append(img)
    ex_pos_list = []
    for i in range(len(exhibitions)):
        y = i // max_row
        x = i - y * max_row
        ex_pos_list.append([pos[0] + x * sep[0], pos[1] + y * sep[1]])
    return exhibitions, ex_pos_list


def r_recommendation(route):
    return 0


def get_rt_detect(frame_q, result_q, client, addr):
    while True:
        time.sleep(1)
    '''while True:
        if frame_q.empty():
            time.sleep(0.1)
        else:
            result = frame_q.get()
            result_q.put(result)'''


def get_text_obj(text, font, color):
    obj = font.render(text, True, color)
    return obj


def update_blur(frame_q, blur_q):
    while True:
        if frame_q.empty():
            time.sleep(0.1)
        else:
            print('blur calculating')
            frame_blur = cv.blur(frame_q.get(), (25, 25), 0)
            blur_q.put(frame_blur)


def route_recommendation(route_q, rec_q):
    while True:
        if route_q.empty():
            time.sleep(0.1)
        else:
            route = route_q.get()
            route = r_recommendation(route)
            rec_q.put(route)


# 一个字一个字显示文本
def text_show(screen, text, text_in_row, font_, pos, sep, color=(230, 185, 126, 200)):
    # 参数分别为：文本，每行允许最大字符数，字体样式，初试位置，每新的一行的间隔，颜色
    for i in range((len(text) // text_in_row) + 1):
        text_obj = font_.render(text[i * text_in_row:(i + 1) * text_in_row], True, color)
        screen.blit(text_obj, (pos[0] + sep[0] * i, pos[1] + sep[1] * i))


if __name__ == '__main__':
    scale = random.uniform(1, 2)
    print(scale)
