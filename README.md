
## 系统说明

基于 微软edge的在线语音合成服务，实现文字转语音

#### 项目介绍
该项目源自以前了解的edge-tts，edge-tts 是一个python库，用于将文本转换为语音，它依赖于 Microsoft Azure 的 Text-to-Speech 服务，可以轻松实现本地文字转语音，在所有的文字转语音的服务中，说它是"最好用的"也不为过，包含了众多“网红主播”的voice （晓晓、云扬、云希...）

项目主要采用了Flask + edge-tts 来实现了这个web服务。可以将文件保存到本地，也可以上传到腾讯云COS，项目能本地运行也可以通过Docker部署到应用服务器

接口使用

/api/v1/tts 套用火山引擎接口地址，详情参考 https://www.volcengine.com/docs/6561/79820

测试脚本 tts_http_demo.py

#### 涉及项目

- 搭配live2d数字人模型，配合音频生成实现开口说话 [live2dSpeek](https://github.com/lyz1810/live2dSpeek)

- 本项目是h5前端代码，需要调用后端音频生成接口，后端是用之前开源的项目 [edge-tts](https://github.com/lyz1810/edge-tts)
