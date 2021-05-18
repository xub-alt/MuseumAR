import socket  # 导入 socket 模块
import cv2 as cv
import numpy as np
import time
import torch
from utils.models.experimental import attempt_load
from yolo_utils.general import non_max_suppression, scale_coords
from yolo_utils.datasets import letterbox
import json
from multiprocessing import Process, Queue, Lock

device = 'cpu'
conf_thres = 0.25
iou_thres = 0.45
classes = None
agnostic_nms = False
image_size = 640
model_path = '/Users/xutianshuo/code/museum.pt'


def img_preprocess(np_img, stride):
    img0 = np_img
    img = letterbox(np_img, image_size, stride)[0]
    img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
    img = np.ascontiguousarray(img)
    torch_img = torch.from_numpy(img).to(device)
    torch_img = torch_img.float()
    torch_img /= 255.0
    if torch_img.ndimension() == 3:
        torch_img = torch_img.unsqueeze(0)
    return torch_img, img0


def recvall(sock, count):
    buf = b''  # buf是一个byte类型
    while count:
        # 接受TCP套接字的数据。数据以字符串形式返回，count指定要接收的最大数据量.
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def server():
    # IP地址'0.0.0.0'为等待客户端连接
    model = attempt_load(model_path, map_location=device)
    names = model.module.names if hasattr(model, 'module') else model.names  # get class names
    stride = int(model.stride.max())

    address = ('0.0.0.0', 8000)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 将套接字绑定到地址, 在AF_INET下,以元组（host,port）的形式表示地址.
    s.bind(address)
    # 开始监听TCP传入连接。参数指定在拒绝连接之前，操作系统可以挂起的最大连接数量。该值至少为1，大部分应用程序设为5就可以了。
    s.listen(1)
    conn, addr = s.accept()
    print('connect from:' + str(addr))

    while True:
        try:
            result = []

            length = recvall(conn, 16)  # 获得图片文件的长度,16代表获取长度
            stringData = recvall(conn, int(length))  # 根据获得的文件长度，获取图片文件
            data = np.frombuffer(stringData, np.uint8)  # 将获取到的字符流数据转换成1维数组
            decimg = cv.imdecode(data, cv.IMREAD_COLOR)  # 将数组解码成图像

            img, img0 = img_preprocess(decimg, stride)
            pred = model(img)[0]
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes=classes, agnostic=agnostic_nms)
            for i, det in enumerate(pred):  # detections per image
                if len(det):
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
                    for *xyxy, conf, cls in reversed(det):
                        # json 不能处理tensor，接收端会报错，必须.item()
                        result.append([names[int(cls)], [xyxy[i].item() for i in range(4)]])
            print(result)
            conn.send(json.dumps(result).encode('utf-8'))

        except TypeError:
            continue


if __name__ == "__main__":
    server()
