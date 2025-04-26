import time
import threading
from PyQt6.QtWidgets import (QMainWindow, QTextEdit, QVBoxLayout, QHBoxLayout, 
                          QWidget, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPoint, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QColor

from .components import MacButton, SwitchButton, BlurWindow
from utils.config import init_dashscope_api_key

class SignalEmitter(QObject):
    text_signal = pyqtSignal(str)
    direction_changed = pyqtSignal()

class TranslatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.signal_emitter = SignalEmitter()
        self.is_zh_to_en = True
        self.is_recording = True
        self.translator = None
        self.mic = None
        self.stream = None
        self.switch_lock = False
        self.last_switch_time = 0
        self.switching = False
        self.translation_thread = None
        
        self.init_ui()
        init_dashscope_api_key()
        self.init_translation()
        
    def init_ui(self):
        self.setWindowTitle('实时语音翻译')
        self.setGeometry(100, 100, 800, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        main_widget = BlurWindow()
        self.setCentralWidget(main_widget)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        main_widget.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)
        
        # 标题栏
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        control_buttons = QWidget()
        control_layout = QHBoxLayout(control_buttons)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)
        
        close_btn = MacButton("#FF5F57")
        minimize_btn = MacButton("#FEBC2E")
        maximize_btn = MacButton("#28C840")
        
        close_btn.clicked.connect(self.close)
        minimize_btn.clicked.connect(self.showMinimized)
        
        control_layout.addWidget(close_btn)
        control_layout.addWidget(minimize_btn)
        control_layout.addWidget(maximize_btn)
        control_layout.addStretch()
        
        title_label = QLabel('实时语音翻译')
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: -apple-system, 'SF Pro Display';
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        title_bar_layout.addWidget(control_buttons)
        title_bar_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        title_bar_layout.addStretch()
        
        layout.addWidget(title_bar)
        
        # 翻译方向切换
        direction_widget = QWidget()
        direction_layout = QHBoxLayout(direction_widget)
        direction_layout.setContentsMargins(0, 0, 0, 0)
        
        self.direction_label = QLabel('当前方向：中文 → 英文')
        self.direction_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-family: -apple-system, 'SF Pro Text';
                font-size: 13px;
            }
        """)
        
        switch_btn = SwitchButton('切换方向')
        switch_btn.clicked.connect(self.switch_direction)
        
        direction_layout.addWidget(self.direction_label)
        direction_layout.addStretch()
        direction_layout.addWidget(switch_btn)
        
        layout.addWidget(direction_widget)
        
        # 状态指示器
        self.status_label = QLabel('正在识别...')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #28C840;
                font-family: -apple-system, 'SF Pro Text';
                font-size: 12px;
                font-weight: 500;
                padding: 4px 8px;
                background: rgba(40, 200, 64, 0.15);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 文本显示区域
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-family: -apple-system, 'SF Pro Text';
                font-size: 15px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                outline: none;
            }
        """)
        layout.addWidget(self.text_area)
        
        # 底部信息
        info_label = QLabel('Powered by LFNL TECH')
        info_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-family: -apple-system, 'SF Pro Text';
                font-size: 11px;
            }
        """)
        layout.addWidget(info_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.signal_emitter.text_signal.connect(self.update_text)
        self.signal_emitter.direction_changed.connect(self.restart_translation)
        
        self.old_pos = None
    
    def switch_direction(self):
        if self.switching:
            return
            
        current_time = time.time()
        if self.switch_lock or (current_time - self.last_switch_time) < 2:
            return
        
        self.switching = True
        self.switch_lock = True
        self.last_switch_time = current_time
        
        try:
            # 停止当前翻译
            self.is_recording = False
            self.cleanup_resources()
            
            # 更新UI
            self.is_zh_to_en = not self.is_zh_to_en
            direction_text = '中文 → 英文' if self.is_zh_to_en else '英文 → 中文'
            self.direction_label.setText(f'当前方向：{direction_text}')
            self.text_area.clear()
            
            self.status_label.setText('正在切换...')
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #FEBC2E;
                    font-family: -apple-system, 'SF Pro Text';
                    font-size: 12px;
                    font-weight: 500;
                    padding: 4px 8px;
                    background: rgba(254, 188, 46, 0.15);
                    border-radius: 4px;
                }
            """)
            
            # 延迟启动新的翻译
            QTimer.singleShot(1500, self._delayed_direction_change)
            
        except Exception as e:
            print(f"切换出错: {str(e)}")
            self.switching = False
            self.switch_lock = False
    
    def _delayed_direction_change(self):
        try:
            # 重新初始化翻译
            self.is_recording = True
            self.init_translation()
            
            # 更新状态显示
            self.status_label.setText('正在识别...')
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #28C840;
                    font-family: -apple-system, 'SF Pro Text';
                    font-size: 12px;
                    font-weight: 500;
                    padding: 4px 8px;
                    background: rgba(40, 200, 64, 0.15);
                    border-radius: 4px;
                }
            """)
        except Exception as e:
            print(f"切换方向时出错: {str(e)}")
        finally:
            self.switching = False
            self.switch_lock = False
    
    def restart_translation(self):
        self.is_recording = False
        self.cleanup_resources()
        time.sleep(1.0)
        self.is_recording = True
        self.init_translation()
    
    def cleanup_resources(self):
        print("开始清理资源...")
        
        # 停止录音
        self.is_recording = False
        
        # 清理翻译器
        if self.translator:
            try:
                print("停止翻译器...")
                self.translator.stop()
                time.sleep(0.3)  # 给翻译器更多时间完成停止操作
            except Exception as e:
                print(f"停止翻译器时出错: {str(e)}")
            finally:
                self.translator = None
        
        # 清理音频流
        if self.stream:
            try:
                print("关闭音频流...")
                if self.stream.is_active():
                    self.stream.stop_stream()
                time.sleep(0.2)
                self.stream.close()
            except Exception as e:
                print(f"关闭音频流时出错: {str(e)}")
            finally:
                self.stream = None
        
        # 清理音频设备
        if self.mic:
            try:
                print("终止音频设备...")
                self.mic.terminate()
                time.sleep(0.2)
            except Exception as e:
                print(f"终止音频设备时出错: {str(e)}")
            finally:
                self.mic = None
        
        # 强制进行垃圾回收
        import gc
        gc.collect()
        
        print("资源清理完成")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self.old_pos = None
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
    
    def init_translation(self):
        print("开始初始化翻译...")
        from translation.translator import init_translation_thread
        init_translation_thread(self)
    
    def update_text(self, text):
        current_text = self.text_area.toPlainText()
        if current_text != text:
            self.text_area.setText(text)
            
            effect = QGraphicsDropShadowEffect()
            effect.setColor(QColor(255, 255, 255, 0))
            self.text_area.setGraphicsEffect(effect)
            
            animation = QPropertyAnimation(effect, b"color")
            animation.setDuration(200)
            animation.setStartValue(QColor(255, 255, 255, 0))
            animation.setEndValue(QColor(255, 255, 255, 15))
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
    
    def closeEvent(self, event):
        self.is_recording = False
        self.cleanup_resources()
        event.accept()