# 水印位置动态计算

根据输入的视频长、宽、水印图像的长、宽和缩放比例进行动态水印图像大小及位置计算。计算原理为首先把图像分割为九宫格，把水印放到最后一个宫格中，根据宫格大小、宫格坐标进行对水印位置和大小的计算。
## 目录

- [水印位置动态计算](#水印位置动态计算)
  - [目录](#目录)
          - [配置要求](#配置要求)
          - [安装步骤](#安装步骤)
    - [文件目录说明](#文件目录说明)
    - [效果](#效果)
    - [使用到的框架](#使用到的框架)
    - [版本控制](#版本控制)
    - [作者](#作者)

###### 配置要求

1. Lambda Python 3.7.0
2. OpenCV Python 3.7

###### 安装步骤
```sh
git clone https://github.com/hillday/water-marker-lambda.git
```

### 文件目录说明

```
aws_emr_presto_custom_autoscalling 
├── README.md
├── /images/
├── lambda_function.rb # lambda 函数
├── cv2-python37.zip # lambda 依赖层
```
把函数代码复制到aws lambda 函数中，然后添加层。

### 效果
水印宽为`320`,高为`88`。红色框表示水印大小、位置。
1. 当输入视频宽为`960`,高为`720`时
   ![](./images/test_water960_720.png)
2. 当输入视频宽为`960`,高为`544`时
   ![](./images/test_water960_544.png)
3. 当输入视频宽为`544`,高为`968`时
  ![](./images/test_water544_968.png)



### 使用到的框架

- [opencv-python](https://pypi.org/project/opencv-python/)

### 版本控制

该项目使用Git进行版本管理。您可以在repository参看当前可用版本。

### 作者

qchunhai

