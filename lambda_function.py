import json
import subprocess
import shlex
import boto3


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
    p_y1 = y1 - margin_val
    
    # 水印图像右上角坐标
    p_x0 = p_x1 - new_water_img_w
    p_y0 = p_y1 - new_water_img_h
    
    return (p_x0, p_y0, new_water_img_w, new_water_img_h)


# 根据源分辨率和输出分辨率计算输出的高度
'''
@src_w 源视频宽
@src_h 源视频高
@out_w 输出视频宽
@return 输出视频高
'''
def get_output_video_height(src_w,src_h,out_w):
    return int((src_h/src_w) * out_w)

# 根据输出分辨按比例缩放水印，上传到S3
'''
@mark_s3_bucket 源水印图像存储桶
@s3_image 源水印图像prefix
@s3_mark_save_prefix 输出resize水印图像的路径
@w 输出水印图像的宽
@return 输出水印图像的S3地址
'''
def resize_mark_image(mark_s3_bucket, s3_image,s3_mark_save_prefix,w):
    client = boto3.client('s3')
    client.download_file(mark_s3_bucket, s3_image, '/tmp/mark_image.png')

    local_resize_name = f'mark_image_{w}.png'
    local_mk_file = "/tmp/" + local_resize_name
    ffmpeg_cmd = "/opt/bin/ffmpeg -i " + "/tmp/mark_image.png" + " -vf scale=" + str(w) + ":-1 " + local_mk_file
    print(ffmpeg_cmd)
    command1 = shlex.split(ffmpeg_cmd)
    p1 = subprocess.run(command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    s3_mark_resize_image = s3_mark_save_prefix + local_resize_name
    client.upload_file(local_mk_file, mark_s3_bucket, s3_mark_resize_image)

    s3_mark_resize_image_path = f's3://{mark_s3_bucket}/{s3_mark_resize_image}'
    return s3_mark_resize_image_path

# 根据不同的输出分辨率设置水印图像的位置和地址
'''
@src_w 源视频宽度
@src_h 源视频高度
@out_w 输出的分辨率宽
@mcv_template 转码模版
'''
def set_watermaker_with_resolution(src_w,src_h,out_w,mcv_template):
    out_h = get_output_video_height(src_w,src_h,out_w)
    box_list = divide_nine_grids(out_w, out_h)
    mark_w = 320 # 水印图像宽度
    mark_h = 88 # 水印图像高度
    mark_scale = 0.7 # 水印相对于宫格的缩放比例
    mark_margin_right_bottom = 0.06 # 水印和右下角边距
    mark_s3_bucket = 'xxx' # 水印所在所在存储桶
    mark_s3_image = 'water/xxxx-mark.png' # 水印prefix
    s3_mark_save_prefix = 'water/marks/' # 水印resize 后的路径
    
    (px,py,w,h) = cal_pos_watermark_by_box(box_list[8],mark_w,mark_h,mark_scale,mark_margin_right_bottom)
    resize_mark_image_url = resize_mark_image(mark_s3_bucket,mark_s3_image,s3_mark_save_prefix, w)
    outputs = mcv_template['Settings']['OutputGroups'][0]['Outputs']

    for index in range(len(outputs)):
        if outputs[index]['VideoDescription']['Width'] == out_w:
            insertable_image = outputs[index]['VideoDescription']['VideoPreprocessors']['ImageInserter']['InsertableImages'][0]
            insertable_image['ImageInserterInput'] = resize_mark_image_url
            insertable_image['ImageX'] = px
            insertable_image['ImageY'] = py

# 加载MediaConvert模版
def load_mediaconvert_json_template():
    with open('./template.json','r',encoding='utf8')as fp:
        json_template = json.load(fp)
    
    return json_template

def lambda_handler(event, context):
    src_w = 544
    src_h = 968
    
    mcv_template = load_mediaconvert_json_template()

    set_watermaker_with_resolution(src_w,src_h,360,mcv_template)
    set_watermaker_with_resolution(src_w,src_h,480,mcv_template)
    set_watermaker_with_resolution(src_w,src_h,720,mcv_template)
    
    client = boto3.client('mediaconvert')
    endpoints = client.describe_endpoints()
    
    mediaconvert_client = boto3.client('mediaconvert', endpoint_url=endpoints['Endpoints'][0]['Url'])
    
    #print(mcv_template)
    # Create Convert Job
    # 根据模板进行转码
    response = mediaconvert_client.create_job(**mcv_template)
    print(response)
    # test_result(box_list,vw,vh,px,py,w,h)
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
