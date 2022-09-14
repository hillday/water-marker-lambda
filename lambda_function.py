import json
import cv2
import numpy as np
import boto3
from cv2 import IMREAD_UNCHANGED


# 根据宽度和高度分割为九宫格
# 以左上角和右下角坐标表示一个宫格[(x1,y1),(x2,y2)],当每一个宫格的宽和高为w,h时
# 每一个宫格可以表示为(col * w, row * h),(col * w + w, r * h + h)，col表示列，row表示行，从0开始
'''
@w 图像宽度
@h 图像高度
'''
def divide_nine_grids(w, h):
    grid_w = int(w / 3)
    grid_h = int(h / 3)
    
    print((grid_w,grid_h))
    
    box_list = []
    
    for i in range(0,3):
        for j in range(0,3):
            box = (j * grid_w,i * grid_h, (j + 1) * grid_w, (i + 1) * grid_h)
            box_list.append(box)
    
    return box_list

def to_even(v):
    ev = v
    if (v % 2) != 0:
        ev = v + 1
    return ev
        

# 根据宫格和水印图像大小，水印根据短边缩放比例计算水印大小和位置
'''
@box 九宫格中的某一个
@water_img_w 水印图像宽度
@water_img_h 水印图像高度
@scale 根据box短边缩放的比例
@margin_right_bottom 距离box右下角的比例
'''
def cal_pos_watermark_by_box(box,water_img_w,water_img_h, scale = 1.0, margin_right_bottom = 0.1):
    (x0,y0,x1,y1) = box
    box_w = x1 - x0
    box_h = y1 - y0
    
    new_water_img_w = 0 # 新水印图像宽度
    new_water_img_h = 0 # 新水印图像高度
    
    lm = 0.7
    # 横屏，短边为高
    if box_w > box_h :
        new_water_img_h = int(box_h * scale)
        new_water_img_w = int((water_img_w/(water_img_h * 1.0)) * new_water_img_h)
        
        if new_water_img_w > box_w * lm:
            new_water_img_w = int(box_w * lm)
            new_water_img_h = int((water_img_h/(water_img_w * 1.0)) * new_water_img_w)
        
        margin_val = int(box_h * margin_right_bottom)
    # 竖屏，短边为宽
    else:
        new_water_img_w = int(box_w * scale)
        new_water_img_h = int((water_img_h/(water_img_w * 1.0)) * new_water_img_w)
        
        if new_water_img_h > box_h * lm:
            new_water_img_h = int(box_h * lm)
            new_water_img_w = int((water_img_w/(water_img_h * 1.0)) * new_water_img_h)
        
        margin_val = int(box_w * margin_right_bottom)
    
    new_water_img_w = new_water_img_w
    new_water_img_h = new_water_img_h
    # 水印图像右下角坐标
    p_x1 = x1 - margin_val
    # 调整y,使其视觉上看起来边距一致
    adjust_my = int(margin_val * 0.1) + 1
    p_y1 = y1 - margin_val + adjust_my
    
    # 水印图像右上角坐标
    p_x0 = p_x1 - new_water_img_w
    p_y0 = p_y1 - new_water_img_h
    
    return (p_x0, p_y0, new_water_img_w, new_water_img_h)
    
def test_result(boxs,vw,vh,px,py,w,h):
    img = np.zeros((vh, vw, 3), np.uint8)
    # 浅灰色背景
    img.fill(10)
    
    # 绘制一个红色矩形
    ptLeftTop = (px, py)
    ptRightBottom = (px+w, py+h)
    point_color = (0, 0, 255) # BGR
    thickness = 1
    lineType = 8
    # cv2.rectangle(img, ptLeftTop, ptRightBottom, point_color, thickness, lineType)
    
    # 绘制九宫格
    point_color = (0, 255, 0) # BGR
    thickness = 2
    lineType = 8
    
    (x0s,y0s,x0e,y0e) = boxs[1]
    (x1s,y1s,x1e,y1e) = boxs[6]
    
    ptStart = (x0s,y0s)
    ptEnd = (x1e,y1e)
    
    cv2.line(img, ptStart, ptEnd, point_color, thickness, lineType)

    (x0s,y0s,x0e,y0e) = boxs[2]
    (x1s,y1s,x1e,y1e) = boxs[7]
    
    ptStart = (x0s,y0s)
    ptEnd = (x1e,y1e)
    
    cv2.line(img, ptStart, ptEnd, point_color, thickness, lineType)

    (x0s,y0s,x0e,y0e) = boxs[3]
    (x1s,y1s,x1e,y1e) = boxs[2]
    
    ptStart = (x0s,y0s)
    ptEnd = (x1e,y1e)
    
    cv2.line(img, ptStart, ptEnd, point_color, thickness, lineType)

    (x0s,y0s,x0e,y0e) = boxs[6]
    (x1s,y1s,x1e,y1e) = boxs[5]
    
    ptStart = (x0s,y0s)
    ptEnd = (x1e,y1e)
    
    cv2.line(img, ptStart, ptEnd, point_color, thickness, lineType)
    
    BUCKET = 'xxxxx'
    client = boto3.client('s3')
    
    client.download_file(BUCKET,'water/xxx.png', '/tmp/xxx.png')
    watermark = cv2.imread("/tmp/xxx.png")
    wm_dim = (w,h)
    resized_wm = cv2.resize(watermark, wm_dim, interpolation=cv2.INTER_AREA)
    
    roi = img[py:py+h, px:px + w]
    result = cv2.addWeighted(roi, 1, resized_wm, 0.6, 0)
    img[py:py+h, px:px + w] = result

    cv2.imwrite('/tmp/test_water360_642.png', img)
    
    
   
    client.upload_file('/tmp/test_water360_642.png', BUCKET, 'water/test_water360_642.png')
    
    

def lambda_handler(event, context):
    vw = 360
    vh = 642
    box_list = divide_nine_grids(vw,vh)
    
    (px,py,w,h) = cal_pos_watermark_by_box(box_list[8],320,88,0.7,0.06)
    
    print(px,py,w,h)
    test_result(box_list,vw,vh,px,py,w,h)
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
