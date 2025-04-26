import time
import threading
from dashscope.audio.asr import TranslationRecognizerRealtime
from utils.config import AUDIO_FORMAT, SAMPLE_RATE, TRANSLATION_MODEL, CHUNK_SIZE
from .callback import TranslationCallback

def init_translation_thread(window):
    """初始化翻译线程"""
    # 确保之前的线程已经结束
    if hasattr(window, 'translation_thread') and window.translation_thread and window.translation_thread.is_alive():
        window.is_recording = False
        time.sleep(0.5)
    
    # 创建新的翻译线程
    window.translation_thread = threading.Thread(
        target=start_translation,
        args=(window,),
        daemon=True
    )
    window.translation_thread.start()
    print("翻译线程已启动")

def start_translation(window):
    """启动翻译服务"""
    print("开始建立翻译服务连接...")
    
    try:
        # 等待之前的资源完全释放
        time.sleep(0.5)
        
        # 创建回调对象
        callback = TranslationCallback(window)
        target_lang = ['en'] if window.is_zh_to_en else ['zh']
        
        # 创建新的翻译器实例
        window.translator = TranslationRecognizerRealtime(
            model=TRANSLATION_MODEL,
            format=AUDIO_FORMAT,
            sample_rate=SAMPLE_RATE,
            transcription_enabled=True,
            translation_enabled=True,
            translation_target_languages=target_lang,
            callback=callback,
        )
        
        # 启动翻译服务
        window.translator.start()
        print(f"翻译服务已启动 (方向: {'中译英' if window.is_zh_to_en else '英译中'})")
        
        # 等待翻译服务完全启动
        time.sleep(0.5)
        
        # 主循环：处理音频数据
        error_count = 0
        while window.is_recording:
            if window.stream and window.stream.is_active():
                try:
                    data = window.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    if window.translator and window.is_recording:
                        window.translator.send_audio_frame(data)
                        error_count = 0
                except Exception as e:
                    print(f"处理音频数据时出错: {str(e)}")
                    error_count += 1
                    if error_count >= 3:
                        print("连续错误次数过多，重新初始化翻译...")
                        window.signal_emitter.direction_changed.emit()
                        break
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
        
        print("翻译循环结束")
        
    except Exception as e:
        print(f"翻译过程出错: {str(e)}")
    finally:
        # 标记翻译结束
        window.is_recording = False 