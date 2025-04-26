import os
import dashscope

def init_dashscope_api_key():
    if 'DASHSCOPE_API_KEY' in os.environ:
        dashscope.api_key = os.environ['DASHSCOPE_API_KEY']
    else:
        dashscope.api_key = 'sk-a8b1fe19c885431c8a3769e18c02541e'

# 音频配置
AUDIO_FORMAT = 'pcm'
SAMPLE_RATE = 16000
CHUNK_SIZE = 3200
CHANNELS = 1

# 翻译模型配置
TRANSLATION_MODEL = 'gummy-realtime-v1' 