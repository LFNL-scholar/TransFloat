import time
import pyaudio
from dashscope.audio.asr import TranslationRecognizerCallback, TranscriptionResult, TranslationResult
from utils.config import SAMPLE_RATE, CHUNK_SIZE, CHANNELS

class TranslationCallback(TranslationRecognizerCallback):
    def __init__(self, window):
        self.window = window
        self.connection_attempts = 0
        self.max_attempts = 3
    
    def on_open(self) -> None:
        try:
            print("初始化音频设备...")
            
            # 创建新的音频设备
            if not self.window.mic:
                self.window.mic = pyaudio.PyAudio()
                time.sleep(0.2)  # 等待设备初始化
            
            # 创建新的音频流
            if not self.window.stream:
                self.window.stream = self.window.mic.open(
                    format=pyaudio.paInt16,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE,
                    start=False
                )
                
                time.sleep(0.2)  # 等待流初始化
                self.window.stream.start_stream()
                print("音频流已启动")
                
        except Exception as e:
            print(f"初始化音频设备时出错: {str(e)}")
            self.connection_attempts += 1
            if self.connection_attempts < self.max_attempts:
                print(f"尝试重新连接... ({self.connection_attempts}/{self.max_attempts})")
                time.sleep(1)
                self.on_open()
            else:
                self.window.cleanup_resources()

    def on_close(self) -> None:
        print("翻译服务连接已关闭")
        if self.window.is_recording:  # 只有在正常录音状态下才重新启动
            self.window.restart_translation()

    def on_error(self, message) -> None:
        print(f"翻译错误: {message}")
        self.connection_attempts += 1
        if self.connection_attempts < self.max_attempts and self.window.is_recording:
            print(f"尝试重新连接... ({self.connection_attempts}/{self.max_attempts})")
            time.sleep(1)
            self.window.restart_translation()
        else:
            self.window.cleanup_resources()

    def on_event(
        self,
        request_id,
        transcription_result: TranscriptionResult,
        translation_result: TranslationResult,
        usage,
    ) -> None:
        if translation_result is not None and self.window.is_recording:
            try:
                target_lang = 'en' if self.window.is_zh_to_en else 'zh'
                translation = translation_result.get_translation(target_lang)
                if translation and translation.text:
                    print(f"收到翻译结果: {translation.text}")
                    self.window.signal_emitter.text_signal.emit(translation.text)
                    self.connection_attempts = 0  # 重置连接尝试次数
            except Exception as e:
                print(f"处理翻译结果时出错: {str(e)}")
                self.on_error(str(e)) 