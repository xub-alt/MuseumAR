import datetime
import time
from sys import exit
import random
import os
import cv2 as cv
import pygame
from pygame.locals import *
from utils.game_utils import *
from multiprocessing import Process, Queue, Lock
import socket  # 导入 socket 模块，使用socket将摄像头传输到服务器，再从服务器接收
import numpy as np
import json


# 场景
def game(info_q):
    pygame.init()
    pygame.mixer.init()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    # video cap setting

    music_play = False
    music_flag = False
    music_pipa = False
    music_pipa_load = False
    music_jieshuo = False
    music_jieshuo_load = False

    cap = cv.VideoCapture(0)
    SCREEN_SIZE = (2560, 1600)
    print(SCREEN_SIZE)
    # relative images
    mouse_image_filename = 'lib/lib_img/mouse.png'
    mouse_down_image_filename = 'lib/lib_img/mouse_press.png'

    # font
    font = pygame.font.Font("lib/fonts/fangzheng.TTF", 54)
    font_intro = pygame.font.Font("lib/fonts/fangzheng.TTF", 40)
    font_button = pygame.font.Font("lib/fonts/fangzheng.TTF", 40)
    font_danmu = pygame.font.Font("lib/fonts/fangzheng.TTF", 30)
    MYRED = (191, 13, 35)
    MYWHITE = (255, 255, 255)

    # button
    button_path = 'lib/lib_img/button.png'
    button_press_path = 'lib/lib_img/button_press.png'
    BUTTON_SIZE = (150, 60)
    button_text = ['开  始', '继  续', '取  消', '退  出', '返  回']
    text_press_color = (230, 185, 126)
    text_not_press_color = (125, 85, 4)
    button_text_sep = (BUTTON_SIZE[0]//6, BUTTON_SIZE[1]//6)

    # page
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    pygame.display.set_caption('博物馆奇妙之旅')

    # background = pygame.image.load(background_image_filename).convert()
    mouse = pygame.image.load(mouse_image_filename).convert_alpha()
    mouse = pygame.transform.scale(mouse, (40, 40))
    mouse.set_alpha(200)
    mouse_down_image = pygame.image.load(mouse_down_image_filename).convert_alpha()
    mouse_down_image = pygame.transform.scale(mouse_down_image, (40, 40))
    mouse_down_image.set_alpha(200)

    # local time show setting
    time_img_list = [pygame.image.load('lib/lib_num/num{}.png'.format(i)).convert_alpha() for i in range(10)]
    time_img_list.append(pygame.image.load('lib/lib_num/num_.png').convert_alpha())
    time_x, time_y = SCREEN_SIZE[0] // 100, SCREEN_SIZE[1] // 18
    space = SCREEN_SIZE[0] // 50
    time_img_loc = [[time_x + i * space, time_y] for i in range(8)]
    TIME_IMG_SIZE = SCREEN_SIZE[1] // 20  # y

    # text roll
    TIME_SPACE = 0.1  # s
    TEXTS_IN_ROW = 15  # n texts in a row

    # person_1 intro
    p1_img = pygame.image.load('lib/lib_img/person1.png').convert_alpha()
    p1_cute_img = pygame.image.load('lib/lib_img/person1_cute.png').convert_alpha()
    p1_img = pygame.transform.scale(p1_img, (300, 600))
    p1_cute_img = pygame.transform.scale(p1_cute_img, (300, 600))
    p1_cute_img.set_alpha(230)
    p1_img.set_alpha(230)

    p1_x_start_ori = 300
    p1_x_start = p1_x_start_ori
    p1_x_end = 800
    p1_y = 1000
    p1_foot = p1_x_end - p1_x_start
    P1_MOVE_FREQ = 20  # n次后移动到目标位置
    intro_start_flag = False

    # talk box
    talk_box = pygame.image.load('lib/lib_img/talk.png').convert_alpha()
    talk_box = pygame.transform.scale(talk_box, (talk_box.get_width() // 3, talk_box.get_height() // 3))
    talk_box.set_alpha(170)
    tb_x = (SCREEN_SIZE[0]-talk_box.get_width()) // 2
    tb_y_ori, tb_y_end = SCREEN_SIZE[1], SCREEN_SIZE[1] - talk_box.get_height()
    tb_y = tb_y_ori
    tb_foot = tb_y_end - tb_y
    TB_MOVE_FREQ = 20  # n次后移动到目标位置

    # flower
    flowers_path = 'lib/lib_img/flowers/'
    flower_items = []
    for item in os.listdir(flowers_path):
        img = pygame.image.load(flowers_path + item).convert_alpha()
        # img = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
        img.set_alpha(255)
        flower_items.append(img)

    FLOWER_SPACE_TIME = 0.5
    TIMES_RANGE = (100, 200)
    POS_START_RANGE = (-400, 1600)
    POS_END_RANGE = (-400, 1600)
    # ROTATE_RANGE = (0, 180)
    # flowers = [[flower1, pos_at, end_pos, times], [flower2, pos_at, end_pos, times], ...]
    flowers = []

    # TEXT
    # intro text
    with open('lib/lib_text/intro.txt', 'r') as file:
        intro_text_all = file.read()
    intro_text_pos = [SCREEN_SIZE[0]//2.2, tb_y_end+SCREEN_SIZE[1]//30]
    intro_text_sep = [0, 80]
    intro_text_start_flag = False
    intro_text_flag = 0
    intro_end_flag = False

    # select hall text
    select_hall_text_all = "选择一些你感兴趣的展馆吧！我将为你推荐游览路线。"
    select_hall_text_pos = intro_text_pos
    select_hall_text_sep = intro_text_sep
    select_hall_text_start_flag = False
    select_hall_text_flag = 0
    select_hall_end_flag = False
    select_hall_keep_flag = False

    # quit text in talk box
    quit_talk = font_intro.render("那就下次再见啦！", True, text_press_color)
    quit_talk_pos = intro_text_pos

    # horizon
    horizon_path = 'lib/lib_img/horizon_2.png'
    horizon = pygame.image.load(horizon_path).convert_alpha()
    horizon = pygame.transform.scale(horizon, (int(horizon.get_width() * 0.8), int(horizon.get_height() * 0.8)))
    # horizon_mask = cv.imread('lib/lib_img/horizon_mask.png')
    # horizon_mask = cv.transpose(horizon_mask)

    # 博物馆地图
    with open('lib/lib_text/halls', 'r') as file:
        halls_list = file.read().split('\n')
    print('Halls:', halls_list)
    map_bg = pygame.image.load('lib/lib_img/map_bg.jpg').convert_alpha()
    map_bg = pygame.transform.scale(map_bg, (int(SCREEN_SIZE[0]*0.8), int(SCREEN_SIZE[1]*0.8)))
    map_bg.set_alpha(200)
    map_bg_pos = [(SCREEN_SIZE[0]-map_bg.get_width())//2,
                  (SCREEN_SIZE[1]-map_bg.get_height())//2, ]

    map = pygame.image.load('lib/lib_img/halls_s1.png').convert_alpha()
    map = pygame.transform.scale(map, (1000, 1000))
    map2 = pygame.image.load('lib/lib_img/halls_s2.png').convert_alpha()
    map2 = pygame.transform.scale(map2, (1000, 1000))
    map_pos = [map_bg_pos[0]*1.1, map_bg_pos[1]*2.5]
    map_flag = False

    map_text = font.render("请选择导览路线", True, MYRED)
    map_text_pos = ((SCREEN_SIZE[0]-map_text.get_width())//2, map_bg_pos[1]+SCREEN_SIZE[1]//20)

    # 用于推荐的路线类
    img = pygame.image.load('lib/lib_img/select.png').convert_alpha()
    img = pygame.transform.scale(img, (100, 100))
    route1 = RouteOBJ("路线一", pos=(int(SCREEN_SIZE[0]*0.54), int(SCREEN_SIZE[1]*0.25)), img=img,
                      font=font, color=MYRED, scale=(int(SCREEN_SIZE[0]*0.87), int(SCREEN_SIZE[1]*0.5)), )
    route2 = RouteOBJ("路线二", pos=(int(SCREEN_SIZE[0]*0.54), int(SCREEN_SIZE[1]*0.55)), img=img,
                      font=font, color=MYRED, scale=(int(SCREEN_SIZE[0]*0.87), int(SCREEN_SIZE[1]*0.8)), )
    route1.mouse_press = True
    route_switch_flag = False  # 对应触发了路线一、二切换的flag

    text_box = TextBox(1000, 500, 1000, 500, font=font)
    text_box_flag = False

    # 素纱襌衣与互动
    sushadanyi = SuShaDanYi('lib/lib_img/sushadanyi_1.jpeg',
                            'lib/lib_img/sushadanyi_2.png',
                            (2300, 1100), font, text_press_color)
    keep2_button = Button('继   续', button_path, button_press_path, BUTTON_SIZE,
                          (SCREEN_SIZE[0]//1.8, SCREEN_SIZE[1]-BUTTON_SIZE[1]-30),
                          font_button, text_not_press_color, text_press_color)

    quit2_button = Button('退   出', button_path, button_press_path, BUTTON_SIZE,
                          (keep2_button.pos[0]+int(BUTTON_SIZE[0]*1.1), keep2_button.pos[1]),
                          font_button, text_not_press_color, text_press_color)
    hu_dong = Hudong('lib/lib_img/hudong1.png')

    state = State()  # 目标检测状态类
    hand = Hand('lib/lib_img/hand.png', 'lib/lib_img/hand.png', (SCREEN_SIZE[0] / 1280, SCREEN_SIZE[1] / 960))  # 创建手类

    # 弹幕滚动
    danmu_list = DanMuList(SCREEN_SIZE[0]//2-700, SCREEN_SIZE[0]//2+700, SCREEN_SIZE[1]//2-500, SCREEN_SIZE[1]//2+500)
    with open('lib/lib_text/danmu', 'r') as file:
        text = file.read().split('\n')
    for i in text:
        danmu_list.add(i, font_danmu, MYWHITE)
    danmu_button = ImgButton('lib/lib_img/danmu-2.png', 'lib/lib_img/danmu-3.png', (200, 170),
                             (SCREEN_SIZE[0]-210, SCREEN_SIZE[1]//2))
    collect_button = ImgButton('lib/lib_img/collect.png', 'lib/lib_img/collect_press.png', (200, 200),
                               (SCREEN_SIZE[0]-210, SCREEN_SIZE[1]//2+300))
    danmu_flag = False

    # flower button
    flower_button = ImgButton('lib/lib_img/123.png', 'lib/lib_img/123-2.png', (200, 200),
                              (SCREEN_SIZE[0]-210, SCREEN_SIZE[1]//2-300))

    # jietu button
    jietu_button = ImgButton('lib/lib_img/jietu.png', 'lib/lib_img/jietu.png', (200, 200),
                             (SCREEN_SIZE[0]-210, SCREEN_SIZE[1]//2-600))
    jietu_button.press_space = 2  # 每次截图间隔2s
    jietu_img = None
    jietu_flag = False
    jietu_time = 0
    jietu_path = 'screenshots/'
    share = pygame.image.load('lib/lib_img/share.jpeg')
    share_pos = (int(SCREEN_SIZE[0]-share.get_width())//2, SCREEN_SIZE[1]-400)

    # painting
    paint = pygame.image.load('lib/lib_img/paint.jpeg')
    rate = SCREEN_SIZE[0]*0.9/paint.get_width()
    paint_scale = (int(paint.get_width()*rate), int(paint.get_height()*rate))
    paint = pygame.transform.scale(paint, paint_scale)
    paint_pos = (int(SCREEN_SIZE[0]*0.05), int(SCREEN_SIZE[1]*0.35))
    butterfly = Butterfly('lib/lib_img/butterfly.png', (200, 200), (1000, 600),
                          font, MYRED, 'lib/lib_img/red_arrow.png')
    paint_flag = False

    # start button text init
    start_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
    start_button_pos = (SCREEN_SIZE[0]//1.8, SCREEN_SIZE[1]-BUTTON_SIZE[1]-30)
    start_button_lock = False
    start_button_press = False
    start_text = font_button.render(button_text[0], True, text_not_press_color)
    start_text_pos = (start_button_pos[0]+button_text_sep[0], start_button_pos[1]+button_text_sep[1])
    select_hall_list = []  # 用户选中的展馆会被添加进这个list

    # return back button text init
    back_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
    back_button_pos = (start_button_pos[0]-BUTTON_SIZE[0]*1.1, start_button_pos[1])
    back_button_lock = False
    back_button_press = False
    back_text = font_button.render(button_text[4], True, text_not_press_color)
    back_text_pos = (back_button_pos[0]+button_text_sep[0], back_button_pos[1]+button_text_sep[1])

    # keep button text init
    keep_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
    keep_button_pos = start_button_pos
    keep_button_lock = False
    keep_button_press = False
    keep_text = font_button.render(button_text[1], True, text_not_press_color)
    keep_text_pos = start_text_pos

    # quit button text init
    quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
    quit_button_pos = (start_button_pos[0]+BUTTON_SIZE[0]*1.1, start_button_pos[1])
    quit_button_lock = False
    quit_button_press = False
    quit_text = font_button.render(button_text[3], True, text_not_press_color)
    quit_text_pos = (quit_button_pos[0]+button_text_sep[0], quit_button_pos[1]+button_text_sep[1])

    # exhibitions (button)
    ex_path = 'lib/lib_img/exhibitions_new/'
    EX_SCALE = (600, 300)
    EX_EACH_ROW = 3  # 每行最多显示3个
    ex_pos = [SCREEN_SIZE[0]//2-EX_SCALE[0]*1.6, 300]  # 基础位置
    ex_sep = [EX_SCALE[0] * 1.1, EX_SCALE[1] * 1.2]  # x轴上间隔30，y轴上间隔50
    exhibitions, ex_pos_list = exhibition_setting(ex_path, EX_SCALE, EX_EACH_ROW, ex_pos, ex_sep)

    SELECT_IMG_SCALE = (50, 50)
    select_img = pygame.image.load('lib/lib_img/select.png').convert_alpha()
    select_img = pygame.transform.scale(select_img, SELECT_IMG_SCALE)
    select_flag_list = [False for i in range(len(exhibitions))]
    re_select_flag = False

    # start visit
    start_visit_text = "让我们一起开始这段快乐之旅吧！"
    start_visit_flag = False
    start_visit_end_flag = False
    start_text_index = 0

    # relative flag
    mouse_down = 0
    Fullscreen = False
    t0 = time.time()  # for text intro
    t1 = t0  # for text select hall
    select_hall_start_flag = False  # 展馆选择页面
    show_local_time_flag = True
    mouse_up = False  # 表示完成了一次鼠标单击
    click = 0
    click_hall = 0  # 展馆选择（点击flag）
    person_in_select = True

    # flower flag
    flower_start_lock = False
    f0 = 0

    # quit flags
    QUIT_FLAG = False
    FINAL_QUIT = False
    QUIT_TIME = 1.0  # wait second
    q0 = t0
    time_keep = 0
    frame_blur = None

    # screen flag
    screen_1_flag = True
    screen_2_flag = False
    screen_3_flag = False
    screen_4_flag = False

    screen_5_flag = False   # screen_5 is for real time AR

    route1.halls = [[1], [2, 3]]
    route2.halls = [[5, 6], [4]]
    result = None
    frame = None
    # background = pygame.image.load('lib/lib_img/bg_.png').convert()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                QUIT_FLAG = True

            if event.type == MOUSEMOTION:
                # if in start button
                if in_button(event.pos, start_button_pos, BUTTON_SIZE):
                    start_button_press = True
                else:
                    start_button_press = False
                if in_button(event.pos, back_button_pos, BUTTON_SIZE):
                    back_button_press = True
                else:
                    back_button_press = False
                if in_button(event.pos, keep_button_pos, BUTTON_SIZE):
                    keep_button_press = True
                else:
                    keep_button_press = False
                if in_button(event.pos, quit_button_pos, BUTTON_SIZE):
                    quit_button_press = True
                else:
                    quit_button_press = False

                if in_area(event.pos, route1.pos, route1.scale):
                    route1.mouse = True
                else:
                    route1.mouse = False
                if in_area(event.pos, route2.pos, route2.scale):
                    route2.mouse = True
                else:
                    route2.mouse = False

            if event.type == MOUSEBUTTONDOWN:
                mouse_down = 1
                mouse_up = False

                if in_area(event.pos, route1.pos, route1.scale):
                    route1.mouse_press = True
                    route2.mouse_press = False   # 互斥
                if in_area(event.pos, route2.pos, route2.scale):
                    route2.mouse_press = True
                    route1.mouse_press = False

            if event.type == MOUSEBUTTONUP:
                mouse_down = 0
                mouse_up = True
                click += 1

            if event.type == KEYDOWN:
                if text_box_flag:
                    text_box.safe_key_down(event)
                if event.key == K_f:
                    Fullscreen = not Fullscreen
                    if Fullscreen:
                        screen = pygame.display.set_mode(SCREEN_SIZE, FULLSCREEN, 32)
                    else:
                        screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)

                if event.key == K_ESCAPE:
                    QUIT_FLAG = True

                if event.key == K_SPACE:
                    intro_start_flag = True

                if event.key == K_0:  # flower start
                    flower_start_lock = not flower_start_lock
                if event.key == K_t:
                    show_local_time_flag = not show_local_time_flag
                if event.key == K_SPACE:
                    hu_dong.activation_flag = True
                if event.key == K_h:
                    hand.hand_flag = not hand.hand_flag
                if event.key == K_9:
                    danmu_button.show_flag = not danmu_button.show_flag
                if event.key == K_p:
                    paint_flag = not paint_flag
                    music_jieshuo = not music_jieshuo
                    if music_jieshuo:
                        music_play = True
                        music_flag = False
                    else:
                        music_play = False
                if event.key == K_m:
                    music_pipa = not music_pipa
                    if music_pipa:
                        music_play = True
                        music_flag = False
                    else:
                        music_play = False

        # get capture
        ret, frame = cap.read()
        frame = cv.flip(frame, 1)
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        frame = cv.transpose(frame)

        if frame is not None:
            background = pygame.surfarray.make_surface(frame)
            background = pygame.transform.scale(background, SCREEN_SIZE)
            screen.blit(background, (0, 0))
        else:
            screen.fill((0, 0, 0))
        # blit background

        if flower_start_lock:
            if time.time() - f0 >= FLOWER_SPACE_TIME:  # init and create new flowers
                flowers.append(flower_create(flower_items, POS_START_RANGE,
                                             POS_END_RANGE, SCREEN_SIZE, TIMES_RANGE))
                f0 = time.time()

            for i in range(len(flowers)):
                if not flowers[i]:
                    # 花瓣到达预定位置，不再显示
                    continue
                screen.blit(flowers[i][0], flowers[i][1])
                flowers[i] = flower_fly(flowers[i])
        else:
            flowers = []

        if FINAL_QUIT and time.time() - q0 >= QUIT_TIME:
            exit()

        if QUIT_FLAG:  # ready to kill the program
            screen.blit(talk_box, (tb_x, tb_y_end))
            screen.blit(p1_img, (p1_x_end, p1_y))
            screen.blit(quit_talk, quit_talk_pos)
            if not FINAL_QUIT:
                q0 = time.time()
                FINAL_QUIT = True

        else:
            # object detection
            if not info_q.empty():
                result = info_q.get()
            if result is not None:
                state.update_state(result, time.time())
                if state.state[0]:
                    sushadanyi.flag = True
                else:
                    sushadanyi.flag = False
                if state.state[3]:
                    if not intro_start_flag:
                        intro_start_flag = True
                    hand.xyxy2pos(state.xyxy[3])
                    hand.show_hand = True
                    hu_dong.activation_flag = True
                else:
                    hu_dong.activation_flag = False
                    hand.show_hand = False
                if state.state[2]:
                    danmu_button.show_flag = True

            # ------------ 场景一：接待 -------------
            if screen_1_flag:
                if not intro_start_flag:
                    text = font.render('请举起手打个招呼，开启这段旅程吧！', True, MYRED)
                    screen.blit(text, (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2))
                # person 1 and talk box come up
                if intro_start_flag:
                    screen.blit(talk_box, (tb_x, tb_y))
                    screen.blit(p1_cute_img, (p1_x_start, p1_y))
                    if tb_y > tb_y_end:
                        tb_y += tb_foot // TB_MOVE_FREQ
                    else:
                        tb_y_end = tb_y

                    if p1_x_start < p1_x_end:
                        p1_x_start += p1_foot / P1_MOVE_FREQ
                    else:
                        intro_text_start_flag = True

                # text roll intro_text
                if intro_text_start_flag:
                    # 获取随着时间间隔，相对应的文本
                    intro_text, intro_end_flag = text_get(intro_text_all, intro_text_flag)
                    # 一个字一个字显示文本
                    text_show(screen, intro_text, TEXTS_IN_ROW, font_intro, intro_text_pos, intro_text_sep)
                    if time.time() - t0 >= TIME_SPACE and not intro_end_flag:
                        intro_text_flag += 1
                        t0 = time.time()
                    else:
                        start_button_lock = True
                        quit_button_lock = True

                # buttons
                if start_button_lock:
                    screen.blit(start_button, start_button_pos)
                    screen.blit(start_text, start_text_pos)

                    if start_button_press:
                        start_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        start_text = font_button.render(button_text[0], True, text_press_color)
                        if mouse_down:
                            select_hall_start_flag = True
                            screen_2_flag = True
                            screen_1_flag = False
                    else:
                        start_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        start_text = font_button.render(button_text[0], True, text_not_press_color)

                if quit_button_lock:
                    screen.blit(quit_button, quit_button_pos)
                    screen.blit(quit_text, quit_text_pos)

                    if quit_button_press:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        quit_text = font_button.render(button_text[3], True, text_press_color)
                        if mouse_down:
                            QUIT_FLAG = True
                    else:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        quit_text = font_button.render(button_text[3], True, text_not_press_color)

            # 场景二：选择要游览的展馆
            elif screen_2_flag:
                # 开始选择场景
                if select_hall_start_flag:
                    intro_text_start_flag = False
                    start_button_lock = False

                    select_hall_text_start_flag = True

                    screen.blit(talk_box, (tb_x, tb_y_end))
                    screen.blit(p1_img, (p1_x_end, p1_y))

                if select_hall_text_start_flag:
                    # 获取随着时间间隔，相对应的文本
                    select_hall_text, select_hall_end_flag = text_get(select_hall_text_all, select_hall_text_flag)
                    # 一个字一个字显示文本
                    text_show(screen, select_hall_text,
                              TEXTS_IN_ROW, font_intro, select_hall_text_pos, select_hall_text_sep)
                    if time.time() - t1 >= TIME_SPACE and not select_hall_end_flag:
                        select_hall_text_flag += 1
                        t1 = time.time()

                if select_hall_end_flag:  # 文字加载完成，展示可选择的展馆
                    keep_button_lock = True
                    quit_button_lock = True
                    person_in_select = False

                    for i in range(len(exhibitions)):
                        screen.blit(exhibitions[i], ex_pos_list[i])
                        if select_flag_list[i]:  # 如果该图片被选中，则打个勾
                            screen.blit(select_img, (ex_pos_list[i][0] + EX_SCALE[0] - SELECT_IMG_SCALE[0],
                                                     ex_pos_list[i][1] + EX_SCALE[1] - SELECT_IMG_SCALE[1]))

                    if mouse_down and click > click_hall:  # 如果鼠标点击，更新展馆选中信息
                        for i in range(len(ex_pos_list)):
                            if in_button(pygame.mouse.get_pos(), ex_pos_list[i], EX_SCALE):
                                select_flag_list[i] = not select_flag_list[i]
                        click_hall = click

                if re_select_flag:  # 重新选择
                    select_hall_text_start_flag = False
                    select_hall_start_flag = False

                    screen.blit(talk_box, (tb_x, tb_y_end))
                    screen.blit(p1_img, (p1_x_end, p1_y))
                    text = font_intro.render("请至少选择一个展区哦！", True, text_press_color)
                    screen.blit(text, intro_text_pos)

                if keep_button_lock:
                    screen.blit(keep_button, keep_button_pos)
                    screen.blit(keep_text, keep_text_pos)

                    if keep_button_press:
                        keep_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        keep_text = font_button.render(button_text[1], True, text_press_color)
                        if mouse_down:
                            if True in select_flag_list:  # 如果选中了至少一个展区
                                screen_3_flag = True
                                screen_2_flag = False
                                keep_button_press = False
                                back_button_lock = True
                                time_keep = time.time()
                            else:
                                re_select_flag = True

                    else:
                        keep_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        keep_text = font_button.render(button_text[1], True, text_not_press_color)

                if quit_button_lock:
                    screen.blit(quit_button, quit_button_pos)
                    screen.blit(quit_text, quit_text_pos)

                    if quit_button_press:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        quit_text = font_button.render(button_text[3], True, text_press_color)
                        if mouse_down:
                            QUIT_FLAG = True
                    else:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        quit_text = font_button.render(button_text[3], True, text_not_press_color)

            elif screen_3_flag:
                # 将前场景的flag置为False
                re_select_flag = False
                select_hall_end_flag = False
                select_hall_text_start_flag = False
                select_hall_start_flag = False

                screen.blit(map_bg, map_bg_pos)
                screen.blit(map_text, map_text_pos)
                route1.draw_route_obj(screen, halls_list, font_intro, text_not_press_color)
                route2.draw_route_obj(screen, halls_list, font_intro, text_not_press_color)

                if route1.mouse_press:
                    route1.draw_select(screen)
                    screen.blit(map, map_pos)
                    route1.draw_rect(screen, MYRED)
                elif route2.mouse_press:
                    route2.draw_rect(screen, MYRED)
                    route2.draw_select(screen)
                    screen.blit(map2, map_pos)

                screen.blit(route1.name_obj, route1.pos)
                screen.blit(route2.name_obj, route2.pos)
                if route1.mouse:
                    route1.draw_rect(screen, MYRED)
                    screen.blit(map, map_pos)
                if route2.mouse:
                    route2.draw_rect(screen, MYRED)
                    screen.blit(map2, map_pos)

                if time.time() - time_keep > 0.2:  # 防止误触，0.2秒后出现keep button
                    keep_button_lock = True

                if back_button_lock:
                    screen.blit(back_button, back_button_pos)
                    screen.blit(back_text, back_text_pos)
                    if back_button_press:
                        back_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        back_text = font_button.render(button_text[4], True, text_press_color)
                        if mouse_down:
                            screen_3_flag = False
                            screen_2_flag = True
                            select_hall_start_flag = True
                    else:
                        back_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        back_text = font_button.render(button_text[4], True, text_not_press_color)

                if keep_button_lock:
                    screen.blit(keep_button, keep_button_pos)
                    screen.blit(keep_text, keep_text_pos)

                    if keep_button_press:
                        keep_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        keep_text = font_button.render(button_text[1], True, text_press_color)
                        if mouse_down:
                            if True in select_flag_list:  # 如果选中了至少一个展区
                                screen_3_flag = False
                                screen_4_flag = True
                                tb_y = tb_y_ori
                                p1_x_start = p1_x_start_ori
                    else:
                        keep_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        keep_text = font_button.render(button_text[1], True, text_not_press_color)

                if quit_button_lock:
                    screen.blit(quit_button, quit_button_pos)
                    screen.blit(quit_text, quit_text_pos)

                    if quit_button_press:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        quit_text = font_button.render(button_text[3], True, text_press_color)
                        if mouse_down:
                            QUIT_FLAG = True
                    else:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        quit_text = font_button.render(button_text[3], True, text_not_press_color)

            elif screen_4_flag:
                screen.blit(talk_box, (tb_x, tb_y))
                screen.blit(p1_cute_img, (p1_x_start, p1_y))
                if tb_y > tb_y_end:
                    tb_y += tb_foot // TB_MOVE_FREQ
                else:
                    tb_y_end = tb_y
                if p1_x_start < p1_x_end:
                    p1_x_start += p1_foot / P1_MOVE_FREQ
                else:
                    start_visit_flag = True
                    start_button_lock = True

                if start_visit_flag:
                    # 获取随着时间间隔，相对应的文本
                    text, start_visit_end_flag = text_get(start_visit_text, start_text_index)
                    # 一个字一个字显示文本
                    text_show(screen, text, TEXTS_IN_ROW, font_intro, intro_text_pos, intro_text_sep)
                    if time.time() - t0 >= TIME_SPACE and not start_visit_end_flag:
                        start_text_index += 1
                        t0 = time.time()

                if start_button_lock:
                    screen.blit(start_button, start_button_pos)
                    screen.blit(start_text, start_text_pos)
                    if start_button_press:
                        start_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        start_text = font_button.render(button_text[0], True, text_press_color)
                        if mouse_down:
                            screen_4_flag = False
                            screen_5_flag = True
                    else:
                        start_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        start_text = font_button.render(button_text[0], True, text_not_press_color)

                if quit_button_lock:
                    screen.blit(quit_button, quit_button_pos)
                    screen.blit(quit_text, quit_text_pos)

                    if quit_button_press:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, True)
                        quit_text = font_button.render(button_text[3], True, text_press_color)
                        if mouse_down:
                            QUIT_FLAG = True
                    else:
                        quit_button = button_state(BUTTON_SIZE, button_path, button_press_path, False)
                        quit_text = font_button.render(button_text[3], True, text_not_press_color)

            elif screen_5_flag:

                if paint_flag:
                    screen.blit(paint, paint_pos)
                    if hand.pos is not None:
                        butterfly.update_follow(hand.pos)
                    else:
                        butterfly.reset()
                    butterfly.show(screen)

                elif sushadanyi.flag:
                    screen.blit(hu_dong.img, (1700, 1000))

                    if time.time() - hu_dong.time > hu_dong.time_space:
                        hu_dong.update_show_img((1700, 1000))
                        hu_dong.time = time.time()

                    if hu_dong.activation_flag:
                        screen_5_flag = False
                        sushadanyi.ask = True
                        sushadanyi.reset_alpha()

            elif sushadanyi.ask:
                screen.blit(sushadanyi.img1,
                            ((SCREEN_SIZE[0]-sushadanyi.img1.get_width())//2,
                             (SCREEN_SIZE[1]-sushadanyi.img1.get_height())//2))

                if time.time()-sushadanyi.time > sushadanyi.time_space:
                    sushadanyi.img1 = sushadanyi.show_up(sushadanyi.img1)
                    sushadanyi.time = time.time()

                keep2_button.show(screen)
                if keep2_button.in_button(pygame.mouse.get_pos()):
                    keep2_button.flag = True
                    if mouse_down:
                        sushadanyi.ask = False
                        sushadanyi.choose = True
                        sushadanyi.reset_alpha()
                        t0 = time.time()
                else:
                    keep2_button.flag = False

                quit2_button.show(screen)
                if quit2_button.in_button(pygame.mouse.get_pos()):
                    quit2_button.flag = True
                    if mouse_down:
                        QUIT_FLAG = True
                else:
                    quit2_button.flag = False

            elif sushadanyi.choose:
                text_pos = (SCREEN_SIZE[0]//2, int(SCREEN_SIZE[1]*0.37))
                screen.blit(sushadanyi.img2,
                            ((SCREEN_SIZE[0] - sushadanyi.img2.get_width()) // 2,
                             (SCREEN_SIZE[1] - sushadanyi.img2.get_height()) // 2))
                sushadanyi.determine(screen, pygame.mouse.get_pos(),
                                     MYRED, text_pos, mouse_down)

                if time.time() - sushadanyi.time > sushadanyi.time_space:
                    sushadanyi.img2 = sushadanyi.show_up(sushadanyi.img2)
                    sushadanyi.time = time.time()

                if time.time() - t0 > 0.5:
                    keep2_button.show(screen)
                    if keep2_button.in_button(pygame.mouse.get_pos()):
                        keep2_button.flag = True
                        if mouse_down:
                            sushadanyi.reset()
                            screen_5_flag = True
                    else:
                        keep2_button.flag = False

                    quit2_button.show(screen)
                    if quit2_button.in_button(pygame.mouse.get_pos()):
                        quit2_button.flag = True
                        if mouse_down:
                            QUIT_FLAG = True
                    else:
                        quit2_button.flag = False

        # show local time
        if show_local_time_flag:
            week_day = get_week_day(datetime.datetime.now())
            now_date = datetime.datetime.now().strftime('%Y年%m月%d日')[2:] + ' ' + week_day
            date_obj = font.render(now_date, True, text_not_press_color)
            screen.blit(date_obj, (40, 10))

            now_time = datetime.datetime.now().strftime('%H %M %S')
            for i in range(len(now_time)):
                if now_time[i] != ' ':
                    num = int(now_time[i])
                    time_img = time_img_list[num]
                    time_w = int(time_img.get_width() / (time_img.get_height() / TIME_IMG_SIZE))
                    time_h = TIME_IMG_SIZE
                    time_img = pygame.transform.scale(time_img, (time_w, time_h))
                    screen.blit(time_img, (time_img_loc[i][0] + space - time_w, time_img_loc[i][1]))
                else:
                    time_img = time_img_list[-1]
                    time_w = int(time_img.get_width() * 0.7 / (time_img.get_height() / TIME_IMG_SIZE))
                    time_h = int(TIME_IMG_SIZE * 0.7)
                    time_img = pygame.transform.scale(time_img, (time_w, time_h))
                    screen.blit(time_img,
                                (time_img_loc[i][0] + space * 0.5, time_img_loc[i][1] + TIME_IMG_SIZE * 0.17))

        if danmu_button.show_flag:
            danmu_button.show(screen)
            if danmu_button.in_button(pygame.mouse.get_pos()) and mouse_down and \
                time.time()-danmu_button.time > danmu_button.press_space:
                danmu_button.press_flag = not danmu_button.press_flag
                danmu_button.time = time.time()
            if danmu_button.press_flag:
                danmu_flag = True
            else:
                danmu_flag = False
        else:
            danmu_flag = False
            danmu_button.press_flag = False

        if collect_button.show_flag:
            collect_button.show(screen)
            if collect_button.in_button(pygame.mouse.get_pos()) and mouse_down and \
                    time.time()-collect_button.time > collect_button.press_space:
                collect_button.press_flag = not collect_button.press_flag
                collect_button.time = time.time()

        if text_box_flag:
            text_box.draw(screen)

        if danmu_flag:
            danmu_list.show(screen)

        flower_button.show(screen)
        if flower_button.in_button(pygame.mouse.get_pos()) and mouse_down and \
                time.time() - flower_button.time > flower_button.press_space:
            flower_button.press_flag = not flower_button.press_flag
            flower_start_lock = not flower_start_lock
            flower_button.time = time.time()

        jietu_button.show(screen)
        if jietu_button.in_button(pygame.mouse.get_pos()) and mouse_down and \
                time.time()-jietu_button.time > jietu_button.press_space:
            now_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            path = jietu_path+now_time+'.png'
            pygame.image.save(screen, path)
            jietu_img = pygame.transform.scale(pygame.image.load(path),
                                               (int(SCREEN_SIZE[0]*0.7), int(SCREEN_SIZE[1]*0.7)))
            jietu_flag = True
            jietu_time = time.time()
            jietu_button.time = time.time()

        if jietu_flag:
            if time.time()-jietu_time < jietu_button.press_space:
                screen.blit(jietu_img, (int(SCREEN_SIZE[0]*0.15), int(SCREEN_SIZE[1]*0.05)))
                screen.blit(share, share_pos)
            else:
                jietu_flag = False

        # play music
        if music_pipa:
            if not music_pipa_load:
                pygame.mixer.music.load('lib/lib_music/pipa.wav')
            music_pipa_load = True
            music_jieshuo_load = False

        elif music_jieshuo:
            if not music_jieshuo_load:
                pygame.mixer.music.load('lib/lib_music/paint_jieshuo.wav')
            music_jieshuo_load = True
            music_pipa_load = False

        if music_play:
            if not music_flag:
                pygame.mixer.music.play()
                music_flag = True
        else:
            pygame.mixer.music.stop()

        # blit mouse
        x_mouse, y_mouse = pygame.mouse.get_pos()
        if mouse_down:
            x_mouse -= mouse_down_image.get_width() / 2
            y_mouse -= mouse_down_image.get_height() / 2
            screen.blit(mouse_down_image, (x_mouse, y_mouse))
        else:
            x_mouse -= mouse.get_width() / 2
            y_mouse -= mouse.get_height() / 2
            screen.blit(mouse, (x_mouse, y_mouse))

        if hand.show_hand and hand.pos is not None:
            hand.update_hand(screen)

        screen.blit(horizon, ((SCREEN_SIZE[0] - horizon.get_width()) // 2, 0))
        pygame.display.update()


def send_img_process(info_q):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = ('127.0.0.1', 8000)  # 要连接的服务器IP地址和端口号
    # addr = ('192.168.43.227', 8000)
    sock.connect(addr)

    cap = cv.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        frame = cv.flip(frame, 1)
        imgencode = cv.imencode('.jpg', frame)[1]
        data = np.array(imgencode)
        # 将numpy矩阵转换成字符形式，以便在网络中传输
        byte_data = data.tobytes()
        head = str.encode(str(len(byte_data)).ljust(16))
        result = send2server(head, byte_data, sock)
        pred_result = json.loads(result)
        if not info_q.empty():
            _ = info_q.get()
        info_q.put(pred_result)


def send2server(head, byte_data, sock):
    sock.send(head)
    sock.send(byte_data)
    # 读取服务器返回值
    receive = sock.recv(512)
    if len(receive):
        return receive.decode('utf-8')
    else:
        return 0


if __name__ == "__main__":
    info_queue = Queue(maxsize=1)
    process = [Process(target=game, args=(info_queue, )),
               Process(target=send_img_process, args=(info_queue, ))]

    [p.start() for p in process]
    [p.join() for p in process]
