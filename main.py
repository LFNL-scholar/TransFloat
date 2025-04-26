import os
import sys
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, 
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel,
                            QPushButton, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPoint, QPropertyAnimation, QEasingCurve, QRectF, QTimer
from PyQt6.QtGui import QColor, QPainter, QBrush, QPainterPath, QPen, QIcon, QLinearGradient

import dashscope
import pyaudio
from dashscope.audio.asr import TranslationRecognizerCallback, TranslationRecognizerRealtime, TranslationResult, TranscriptionResult
from ui.main_window import TranslatorWindow

class MacButton(QPushButton):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {color};
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)

class SwitchButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 6px;
                padding: 0 12px;
                font-family: -apple-system, 'SF Pro Text';
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """)

class BlurWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建渐变背景
        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, 15.0, 15.0)
        
        # 创建渐变色
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(40, 40, 45, 230))  # 深色起始色
        gradient.setColorAt(1, QColor(30, 30, 35, 230))  # 深色结束色
        
        # 主背景 - 深色毛玻璃效果
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)
        
        # 添加微妙的光泽边框
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

class SignalEmitter(QObject):
    text_signal = pyqtSignal(str)
    direction_changed = pyqtSignal()

class TranslationCallback(TranslationRecognizerCallback):
    def __init__(self, window):
        self.window = window
    
    def on_open(self) -> None:
        if self.window.switching:
            return
            
        try:
            print("初始化音频设备...")
            
            if not self.window.mic:
                self.window.mic = pyaudio.PyAudio()
            
            if not self.window.stream:
                self.window.stream = self.window.mic.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=3200,
                    start=False
                )
                
                if not self.window.switching:
                    self.window.stream.start_stream()
                    print("音频流已启动")
                    
        except Exception as e:
            print(f"初始化音频设备时出错: {str(e)}")
            if not self.window.switching:
                self.window.cleanup_resources()

    def on_close(self) -> None:
        print("翻译服务连接已关闭")
        if not self.window.switching:
            self.window.cleanup_resources()

    def on_error(self, message) -> None:
        print(f"翻译错误: {message}")
        if not self.window.switching:
            self.window.cleanup_resources()

    def on_event(
        self,
        request_id,
        transcription_result: TranscriptionResult,
        translation_result: TranslationResult,
        usage,
    ) -> None:
        if (translation_result is not None and 
            self.window.is_recording and 
            not self.window.switching):
            try:
                target_lang = 'en' if self.window.is_zh_to_en else 'zh'
                translation = translation_result.get_translation(target_lang)
                if translation and translation.text:
                    print(f"收到翻译结果: {translation.text}")
                    self.window.signal_emitter.text_signal.emit(translation.text)
            except Exception as e:
                print(f"处理翻译结果时出错: {str(e)}")

def init_dashscope_api_key():
    if 'DASHSCOPE_API_KEY' in os.environ:
        dashscope.api_key = os.environ['DASHSCOPE_API_KEY']
    else:
        dashscope.api_key = '<your api-key>'

def start_translation(window):
    print("开始建立翻译服务连接...")
    
    try:
        # 初始化API密钥
        init_dashscope_api_key()
        
        if window.switching:
            return
        
        # 创建回调对象
        callback = TranslationCallback(window)
        target_lang = ['en'] if window.is_zh_to_en else ['zh']
        
        # 创建新的翻译器实例
        window.translator = TranslationRecognizerRealtime(
            model='gummy-realtime-v1',
            format='pcm',
            sample_rate=16000,
            transcription_enabled=True,
            translation_enabled=True,
            translation_target_languages=target_lang,
            callback=callback,
        )
        
        if not window.switching:
            # 启动翻译服务
            window.translator.start()
            print(f"翻译服务已启动 (方向: {'中译英' if window.is_zh_to_en else '英译中'})")
        
        # 主循环：处理音频数据
        while window.is_recording and not window.switching:
            if window.stream and not window.switching:
                try:
                    data = window.stream.read(3200, exception_on_overflow=False)
                    if window.translator and not window.switching:
                        window.translator.send_audio_frame(data)
                except Exception as e:
                    print(f"处理音频数据时出错: {str(e)}")
                    break
            else:
                time.sleep(0.1)
        
        print("翻译循环结束，清理资源...")
        
    except Exception as e:
        print(f"翻译过程出错: {str(e)}")
    finally:
        # 确保资源被清理
        if not window.switching:
            window.cleanup_resources()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TranslatorWindow()
    window.show()
    sys.exit(app.exec()) 