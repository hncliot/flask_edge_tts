import logging
import os
import re
import sys
import json
import base64
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_cors import CORS
from flask import send_from_directory
#from qcloud_cos import CosConfig, CosS3Client
from flask import jsonify
from flask import Response
from werkzeug.exceptions import BadRequest

#app = Flask(__name__, static_folder='tts')  # 指定静态文件夹
app = Flask(__name__, static_url_path='')
CORS(app)  # 这样设置允许所有来源的请求

##异常页面处理
@app.errorhandler(404)
def page_not_found(error):
     """这个handler可以catch住所有abort(404)以及找不到对应router的处理请求"""
     res = {"status": 404, "message": "404错误,找不到对应router"}
     return Response(json.dumps(res, ensure_ascii=False), mimetype='application/json')

@app.errorhandler(400)
def handle_bad_request(error):
     """An error occurred"""
     res = {"status": 400, "message": "An error occurred"}
     return Response(json.dumps(res, ensure_ascii=False), mimetype='application/json')


@app.errorhandler(405)
def error_405(error):
     """这个handler可以catch住所有abort(405)以及请求方式有误的请求"""
     res = {"status": 405, "message": "请求方式有误"}
     return Response(json.dumps(res, ensure_ascii=False), mimetype='application/json')

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({"error": "Invalid JSON format"}), 400

#上传到COS
def uploadCos(file_path,relativePath):
    # 腾讯云COSV5Python SDK, 目前可以支持Python2.6与Python2.7以及Python3.x
    # pip安装指南:pip install -U cos-python-sdk-v5
    # cos最新可用地域,参照https://www.qcloud.com/document/product/436/6224
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在CosConfig中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
    region = ''      # 替换为用户的 region，已创建桶归属的region可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    secret_id = ''     # 替换为用户的 SecretId，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
    secret_key = ''   # 替换为用户的 SecretKey，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
    bucket_name = ''

    # COS支持的所有region列表参见https://www.qcloud.com/document/product/436/6224
    token = None               # 如果使用永久密钥不需要填入token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见https://cloud.tencent.com/document/product/436/14048
    domain = None # domain可以不填，此时使用COS区域域名访问存储桶。domain也可以填写用户自定义域名，或者桶的全球加速域名
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Domain=domain)  # 获取配置对象
    client = CosS3Client(config)
    # 文件流 简单上传
    with open(f'./{relativePath}', 'rb') as fp:
        response = client.put_object(
            Bucket=bucket_name,
            Body=fp,
            Key=relativePath,
            StorageClass='STANDARD',
            ContentType='audio/mpeg'
        )
        print(response['ETag'])
    # 上传完成之后删除文件
    os.remove(file_path)  # 删除文件

    # 构建文件的访问 URL
    url = f"https://{bucket_name}.cos.{region}.myqcloud.com{relativePath}"
    print("文件访问路径:", url)
    return url

voiceMap = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "yunjian": "zh-CN-YunjianNeural",
    "yunxi": "zh-CN-YunxiNeural",
    "yunxia": "zh-CN-YunxiaNeural",
    "yunyang": "zh-CN-YunyangNeural",
    "xiaobei": "zh-CN-liaoning-XiaobeiNeural",
    "xiaoni": "zh-CN-shaanxi-XiaoniNeural",
    "hiugaai": "zh-HK-HiuGaaiNeural",
    "hiumaan": "zh-HK-HiuMaanNeural",
    "wanlung": "zh-HK-WanLungNeural",
    "hsiaochen": "zh-TW-HsiaoChenNeural",
    "hsioayu": "zh-TW-HsiaoYuNeural",
    "yunjhe": "zh-TW-YunJheNeural",
}


def getVoiceById(voiceId):
    return voiceMap.get(voiceId)


# 删除html标签
def remove_html(string):
    regex = re.compile(r'<[^>]+>')
    return regex.sub('', string)


def createAudio(text, file_name, voiceId):
    new_text = remove_html(text)
    print(f"Text without html tags: {new_text} {voiceId}")
    voice = getVoiceById(voiceId)
    if not voice:
        return "error params"

    pwdPath = os.getcwd()
    #本地路径
    filePath = pwdPath + "/static/" + file_name
    #相对路径
    relativePath = "/static/" + file_name
    dirPath = os.path.dirname(filePath)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    if not os.path.exists(filePath):
        # 用open创建文件 兼容mac
        open(filePath, 'a').close()

    script = 'edge-tts --voice ' + voice + ' --text "' + new_text + '" --write-media ' + filePath
    print("语音合成命令: ",script)
    os.system(script)
    #这里可以选择上传云存储和本地使用
    # 上传到腾讯云COS云存储-返回云存储地址
#     url = uploadCos(filePath, relativePath)

    # 音频保存到本地-直接返回音频地址
    url = f'http://127.0.0.1:12020/{relativePath}'
    return url

# 文本合成语音后转成base64
def createAudio_post(text, file_name, voiceId):
    new_text = remove_html(text)
    print(f"Text without html tags: {new_text} {voiceId}")
    voice = getVoiceById(voiceId)
    if not voice:
        return "error params"
    pwdPath = os.getcwd()
    #本地路径
    filePath = pwdPath + "/static/" + file_name
    #相对路径
    relativePath = "/static/" + file_name
    dirPath = os.path.dirname(filePath)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    if not os.path.exists(filePath):
        # 用open创建文件 兼容mac
        open(filePath, 'a').close()

    script = 'edge-tts --voice ' + voice + ' --text "' + new_text + '" --write-media ' + filePath
    print("语音合成命令: ",script)
    os.system(script)
    # 转换文件
    with open(filePath, 'rb') as file:
        file_content = file.read()
    # 将文件内容转换为Base64编码
    base64_encoded = base64.b64encode(file_content)

    # 输出或使用Base64编码的内容
    return base64_encoded.decode('utf-8')

def getParameter(paramName):
    if request.args.__contains__(paramName):
        return request.args[paramName]
    return ""

@app.route('/dealAudio',methods=['POST','GET'])
def dealAudio():
    text = getParameter('text')
    file_name = getParameter('file_name')
    voice = getParameter('voice')
    return createAudio(text, file_name, voice)

# 添加一个路由来处理静态文件的请求
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def index():
    #return 'welcome to my tts!'
    return redirect('/index.html')

'''
{'app': {'appid': '7563220333', 'token': 'access_token', 'cluster': 'volcano_tts'},
'user': {'uid': '388808087185088'}, 'audio': {'voice_type': 'BV001_streaming', 'encoding': 'mp3', 'speed_ratio': 1.0,
'volume_ratio': 1.0, 'pitch_ratio': 1.0}, 'request': {'reqid': 'bdbe6aca-40b0-41ab-8c0b-39580379036f',
'text': '字节跳动语音合成', 'text_type': 'plain', 'operation': 'query', 'with_frontend': 1, 'frontend_type': 'unitTson'}}
'''
# base64接口
@app.route('/api/v1/tts', methods=['GET', 'POST'])
def index_chognzhi():
    try:
        if request.method == 'POST':           
            data = json.loads(request.get_data())
            print(data)
            ttstext = data["request"]["text"]
            voicesd = "xiaoxiao"
            file_name = "test.mp3"
            print("/api/v1/tts >>>",ttstext, file_name, voicesd)
            out = createAudio_post(ttstext, file_name, voicesd)
            #print("结果>>>",out)
            #dirpath = os.path.join(app.root_path,'static')
            #return send_from_directory(dirpath,file_name,as_attachment=True)
            data = {"reqid": "reqid","code": 3000,"operation": "query","message": "Success","sequence": -1,"data": "base64 encoded binary data","addition": ""}
            data['data'] = out
            return json.dumps(data,ensure_ascii=False)
        else:
            res = {"status": 200, "message": "ok"}
            return Response(json.dumps(res, ensure_ascii=False), mimetype='application/json')            
    except Exception as e:
        print("[***]",str(e))
        return render_template('error.html'), 500

if __name__ == "__main__":
    app.run(port=12020,host="0.0.0.0",debug=True)
