import sys
import json
import os
import datetime
import locale
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QListWidget, QLineEdit, QComboBox,
    QLabel, QMessageBox, QListWidgetItem, QAbstractItemView,
    QSizePolicy
)
from PySide6.QtCore import QTimer, Qt, QSize, QEvent
from PySide6.QtGui import QFont
from qt_material import apply_stylesheet

TASKS_FILE = "todos.json"

class TodoItemWidget(QWidget):
    def __init__(self, parent=None, task_data=None, main_window=None, index=0):
        super().__init__(parent)
        self.task_data = task_data
        self.main_window = main_window
        self.index = index
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        
        task_widget = QWidget()
        layout = QHBoxLayout(task_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.check_label = QLabel("□" if not task_data["completed"] else "✓")
        self.check_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.check_label.setCursor(Qt.PointingHandCursor)
        self.check_label.mousePressEvent = self.toggle_completed
        self.check_label.setStyleSheet("color: #000000; min-width: 16px; max-width: 16px; font-size: 16px; font-weight: bold; background-color: transparent; padding-right: 0px;")
        layout.addWidget(self.check_label)
        
        self.number_label = QLabel(f"{index + 1}.")
        self.number_label.setObjectName("number_label")
        self.number_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.number_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.number_label.setMinimumWidth(12)
        layout.addWidget(self.number_label)
        
        self.start_combo = QComboBox()
        self.start_combo.setObjectName("time_combo")
        self.start_combo.setMinimumWidth(50)
        self.start_combo.setMaximumWidth(50)
        self.start_combo.setStyleSheet("QComboBox QScrollBar { width: 0px; height: 0px; } QComboBox::drop-down { width: 0px; }")
        for hour in range(7, 21):
            self.start_combo.addItem(f"{hour:02d}:00")
            self.start_combo.addItem(f"{hour:02d}:30")
        current_start = task_data.get("start_time", "")
        index = self.start_combo.findText(current_start)
        if index >= 0:
            self.start_combo.setCurrentIndex(index)
        
        self.end_combo = QComboBox()
        self.end_combo.setObjectName("time_combo")
        self.end_combo.setMinimumWidth(50)
        self.end_combo.setMaximumWidth(50)
        self.end_combo.setStyleSheet("QComboBox QScrollBar { width: 0px; height: 0px; } QComboBox::drop-down { width: 0px; }")
        for hour in range(7, 21):
            self.end_combo.addItem(f"{hour:02d}:30")
            if hour < 21:
                self.end_combo.addItem(f"{hour+1:02d}:00")
        current_end = task_data.get("end_time", "")
        index = self.end_combo.findText(current_end)
        if index >= 0:
            self.end_combo.setCurrentIndex(index)
        
        self.task_label = QLabel(task_data['task'])
        self.task_label.setObjectName("task_label")
        self.task_label.setCursor(Qt.PointingHandCursor)
        self.task_label.mouseDoubleClickEvent = self.handle_double_click
        self.task_label.setMinimumWidth(150)
        self.task_label.setWordWrap(True)
        
        self.task_edit = QLineEdit(task_data['task'])
        self.task_edit.setObjectName("task_edit")
        self.task_edit.setVisible(False)
        self.task_edit.returnPressed.connect(self.finish_editing)
        self.task_edit.installEventFilter(self)
        self.task_edit.setMinimumWidth(150)
        self.editing_mode = False
        
        self.task_label.setStyleSheet("color: #707070; font-size: 12px;" if task_data["completed"] else "color: #000000; font-weight: bold; font-size: 12px;")
        
        self.start_combo.currentTextChanged.connect(self.update_time)
        self.end_combo.currentTextChanged.connect(self.update_time)
        
        time_separator = QLabel("～")
        
        layout.addWidget(self.start_combo)
        layout.addWidget(time_separator)
        layout.addWidget(self.end_combo)
        layout.addWidget(self.task_label)
        layout.addWidget(self.task_edit)
        layout.addStretch()
        
        main_layout.addWidget(task_widget)
        
        self.button_widget = QWidget()
        self.button_widget.setObjectName("button_container")
        self.button_widget.setFixedHeight(24)
        button_layout = QHBoxLayout(self.button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)
        
        button_layout.addStretch()
        
        self.add_button = QPushButton("+")
        self.add_button.setObjectName("item_control_button")
        self.add_button.setFixedSize(20, 20)
        self.add_button.clicked.connect(self.add_task_below)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("-")
        self.remove_button.setObjectName("item_control_button")
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.clicked.connect(self.remove_this_task)
        button_layout.addWidget(self.remove_button)
        
        button_layout.addStretch()
        
        main_layout.addWidget(self.button_widget)
        
        self.add_button.setVisible(False)
        self.remove_button.setVisible(False)
        
        self.setMouseTracking(True)
        task_widget.setMouseTracking(True)
        self.button_widget.setMouseTracking(True)
        
        self.enterEvent = self.on_enter
        self.leaveEvent = self.on_leave

    def on_enter(self, event):
        self.add_button.setVisible(True)
        self.remove_button.setVisible(True)
    
    def on_leave(self, event):
        self.add_button.setVisible(False)
        self.remove_button.setVisible(False)

    def update_time(self):
        self.task_data["start_time"] = self.start_combo.currentText()
        self.task_data["end_time"] = self.end_combo.currentText()
        self.main_window.save_todos()
    
    def toggle_completed(self, event):
        self.task_data["completed"] = not self.task_data["completed"]
        self.check_label.setText("✓" if self.task_data["completed"] else "□")
        self.task_label.setStyleSheet("color: #707070; font-size: 12px;" if self.task_data["completed"] else "color: #000000; font-weight: bold; font-size: 12px;")
        self.main_window.save_todos()

    def handle_double_click(self, event):
        if not self.task_data["completed"]:
            self.editing_mode = True
            self.task_label.setVisible(False)
            self.task_edit.setText(self.task_data["task"])
            self.task_edit.setVisible(True)
            self.task_edit.setFocus()
            self.task_edit.selectAll()

    def finish_editing(self):
        if self.editing_mode:
            self.editing_mode = False
            new_text = self.task_edit.text().strip()
            if new_text:
                self.task_data["task"] = new_text
                self.task_label.setText(new_text)
            
            self.task_label.setVisible(True)
            self.task_edit.setVisible(False)
            
            self.task_label.setStyleSheet("color: #707070; font-size: 12px;" if self.task_data["completed"] else "color: #000000; font-weight: bold; font-size: 12px;")
            
            self.main_window.save_todos()

    def add_task_below(self):
        new_task = {
            "task": "新しいタスク",
            "completed": False,
            "start_time": "09:00",
            "end_time": "10:00"
        }
        current_index = self.main_window.todo_list.index(self.task_data)
        self.main_window.todo_list.insert(current_index + 1, new_task)
        self.main_window.update_todo_listbox()
        self.main_window.save_todos()
    
    def remove_this_task(self):
        self.main_window.todo_list.remove(self.task_data)
        self.main_window.update_todo_listbox()
        self.main_window.save_todos()

    def update_number(self, new_index):
        self.index = new_index
        self.number_label.setText(f"{new_index + 1}.")

    def eventFilter(self, obj, event):
        if obj == self.task_edit and event.type() == QEvent.FocusOut:
            self.finish_editing()
            return True
        return super().eventFilter(obj, event)

class WindowsClockStylePomodoro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomodoro timer & ToDo List")
        self.setMinimumSize(400, 500)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        
        main_widget = QWidget()
        main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(main_widget)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.time_left = 25 * 60
        self.is_break = False
        self.todo_list = []
        
        self.setup_timer_ui()
        self.setup_todo_ui()
        self.load_todos()
        self.update_todo_listbox()

        self.setCentralWidget(main_widget)
        
        self.resizeEvent = self.on_resize

    def on_resize(self, event):
        self.update_todo_listbox()
        super().resizeEvent(event)

    def setup_timer_ui(self):
        timer_layout = QVBoxLayout()

        self.date_time_label = QLabel()
        self.date_time_label.setObjectName("date_time_label")
        self.date_time_label.setAlignment(Qt.AlignLeft)
        self.date_time_label.setFont(QFont("Segoe UI", 16))
        self.date_time_label.setMinimumHeight(30)
        self.update_date_time()
        
        self.date_time_timer = QTimer(self)
        self.date_time_timer.timeout.connect(self.update_date_time)
        self.date_time_timer.start(1000)
        
        timer_layout.addWidget(self.date_time_label)
        
        # タイマー表示を中央に配置
        self.timer_label = QLabel("50:00")
        self.timer_label.setObjectName("timer_label")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Segoe UI", 36, QFont.Bold))
        timer_layout.addWidget(self.timer_label)

        # コントロールボタンを横並びに配置するレイアウト
        control_layout = QHBoxLayout()
        
        self.start_pause_button = QPushButton("▶")
        self.start_pause_button.setObjectName("timer_control_button")
        self.start_pause_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.start_pause_button.setFixedSize(36, 36)
        self.start_pause_button.setStyleSheet("""
            #timer_control_button {
                border-radius: 18px;
                background-color: transparent;
                color: #757575;
                font-size: 16px;
                border: none;
                padding: 0px;
            }
            #timer_control_button:hover {
                color: #616161;
            }
            #timer_control_button:pressed {
                color: #424242;
            }
        """)
        self.start_pause_button.clicked.connect(self.toggle_timer)
        
        self.reset_button = QPushButton("⟳")
        self.reset_button.setObjectName("reset_button")
        self.reset_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.reset_button.setFixedSize(36, 36)
        self.reset_button.setStyleSheet("""
            #reset_button {
                border-radius: 18px;
                background-color: transparent;
                color: #757575;
                font-size: 18px;
                border: none;
                padding: 0px;
            }
            #reset_button:hover {
                color: #616161;
            }
            #reset_button:pressed {
                color: #424242;
            }
        """)
        self.reset_button.clicked.connect(self.reset_timer)
        
        # ボタンをレイアウトに追加
        control_layout.addStretch(1)
        control_layout.addWidget(self.start_pause_button)
        control_layout.addSpacing(20)  # ボタン間のスペース
        control_layout.addWidget(self.reset_button)
        control_layout.addStretch(1)
        control_layout.setAlignment(Qt.AlignCenter)
        
        timer_layout.addLayout(control_layout)
        timer_layout.setSpacing(10)
        
        time_settings_layout = QHBoxLayout()
        
        work_time_label = QLabel("作業時間：")
        self.work_time_combo = QComboBox()
        for i in range(5, 65, 5):
            self.work_time_combo.addItem(f"{i}分", i)
        self.work_time_combo.setCurrentIndex(4)
        self.work_time_combo.currentIndexChanged.connect(self.update_work_time)
        
        break_time_label = QLabel("休憩時間：")
        self.break_time_combo = QComboBox()
        for i in range(5, 35, 5):
            self.break_time_combo.addItem(f"{i}分", i)
        self.break_time_combo.setCurrentIndex(0)
        self.break_time_combo.currentIndexChanged.connect(self.update_break_time)
        
        time_settings_container = QHBoxLayout()
        time_settings_container.addWidget(work_time_label)
        time_settings_container.addWidget(self.work_time_combo)
        time_settings_container.addSpacing(20)
        time_settings_container.addWidget(break_time_label)
        time_settings_container.addWidget(self.break_time_combo)
        time_settings_container.addStretch(1)
        
        time_settings_layout.addLayout(time_settings_container)
        timer_layout.addLayout(time_settings_layout)
        
        self.main_layout.addLayout(timer_layout)

    def setup_todo_ui(self):
        todo_layout = QVBoxLayout()
        todo_title = QLabel("ToDoリスト")
        todo_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        todo_title.setAlignment(Qt.AlignLeft)
        todo_layout.addWidget(todo_title)

        self.todo_listbox = QListWidget()
        self.todo_listbox.setAlternatingRowColors(True)
        self.todo_listbox.setDragDropMode(QAbstractItemView.InternalMove)
        self.todo_listbox.setTextElideMode(Qt.ElideRight)
        self.todo_listbox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.todo_listbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        todo_layout.addWidget(self.todo_listbox)

        self.empty_list_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_list_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_label = QLabel("ToDoリストが空です")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)
        
        add_first_button = QPushButton("最初のタスクを追加")
        add_first_button.clicked.connect(self.add_first_task)
        empty_layout.addWidget(add_first_button)
        
        todo_layout.addWidget(self.empty_list_widget)
        self.empty_list_widget.setVisible(False)

        self.main_layout.addLayout(todo_layout)

    def toggle_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.start_pause_button.setText("▶")
        else:
            self.timer.start(1000)
            self.start_pause_button.setText("⏸")

    def start_timer(self):
        self.timer.start(1000)
        self.start_pause_button.setText("⏸")

    def pause_timer(self):
        self.timer.stop()
        self.start_pause_button.setText("▶")

    def reset_timer(self):
        self.timer.stop()
        self.time_left = self.work_time_combo.currentData() * 60 if not self.is_break else self.break_time_combo.currentData() * 60
        self.update_timer_display()
        self.start_pause_button.setText("▶")

    def update_timer(self):
        self.time_left -= 1
        self.update_timer_display()

        if self.time_left <= 0:
            self.timer.stop()
            if not self.is_break:
                QMessageBox.information(self, "作業終了", "作業時間が終了しました！休憩しましょう。")
                self.is_break = True
                self.time_left = self.break_time_combo.currentData() * 60
            else:
                QMessageBox.information(self, "休憩終了", "休憩時間が終了しました！作業を再開しましょう。")
                self.is_break = False
                self.time_left = self.work_time_combo.currentData() * 60
            self.update_timer_display()
            self.start_pause_button.setText("▶")

    def update_timer_display(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def add_first_task(self):
        task_data = {
            "task": "新しいタスク",
            "completed": False,
            "start_time": "09:00",
            "end_time": "10:00"
        }
        self.todo_list.append(task_data)
        self.update_todo_listbox()
        self.save_todos()

    def update_todo_listbox(self):
        self.todo_listbox.clear()
        
        if not self.todo_list:
            self.empty_list_widget.setVisible(True)
            self.todo_listbox.setVisible(False)
            return
        else:
            self.empty_list_widget.setVisible(False)
            self.todo_listbox.setVisible(True)
        
        for index, task_data in enumerate(self.todo_list):
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(self.todo_listbox.viewport().width(), 60))
            self.todo_listbox.addItem(list_item)
            item_widget = TodoItemWidget(self.todo_listbox, task_data, self, index)
            self.todo_listbox.setItemWidget(list_item, item_widget)
        
        self.todo_listbox.model().rowsMoved.connect(self.on_rows_moved)

    def on_rows_moved(self, parent, start, end, destination, row):
        self.update_todo_list_order()
        self.update_item_numbers()
        self.save_todos()
    
    def update_todo_list_order(self):
        new_order = []
        for i in range(self.todo_listbox.count()):
            item = self.todo_listbox.item(i)
            widget = self.todo_listbox.itemWidget(item)
            new_order.append(widget.task_data)
        
        self.todo_list = new_order
    
    def update_item_numbers(self):
        for i in range(self.todo_listbox.count()):
            item = self.todo_listbox.item(i)
            widget = self.todo_listbox.itemWidget(item)
            widget.update_number(i)

    def save_todos(self):
        file_path = os.path.join(os.path.dirname(__file__), TASKS_FILE)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.todo_list, f, ensure_ascii=False, indent=4)
    
    def load_todos(self):
        try:
            file_path = os.path.join(os.path.dirname(__file__), TASKS_FILE)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.todo_list = json.load(f)
        except Exception as e:
            print(f"ToDoリストの読み込みエラー: {e}")
            self.todo_list = []

    def update_work_time(self):
        if not self.timer.isActive() and not self.is_break:
            work_time = self.work_time_combo.currentData()
            self.time_left = work_time * 60
            self.update_timer_display()

    def update_break_time(self):
        if not self.timer.isActive() and self.is_break:
            break_time = self.break_time_combo.currentData()
            self.time_left = break_time * 60
            self.update_timer_display()

    def update_date_time(self):
        current_datetime = datetime.datetime.now()
        weekday_ja = ["月", "火", "水", "木", "金", "土", "日"][current_datetime.weekday()]
        try:
            if sys.platform.startswith('win'):
                locale.setlocale(locale.LC_TIME, 'Japanese_Japan')
            else:
                locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')
            date_str = current_datetime.strftime("%Y年%m月%d日（%a）%H:%M")
            self.date_time_label.setText(date_str)
        except Exception as e:
            print(f"ロケール設定エラー: {e}")
            date_str = f"{current_datetime.year}年{current_datetime.month}月{current_datetime.day}日（{weekday_ja}）{current_datetime.hour:02d}:{current_datetime.minute:02d}"
            self.date_time_label.setText(date_str)

    def closeEvent(self, event):
        self.save_todos()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    apply_stylesheet(app, theme='light_blue_500.xml')
    
    extra = {
        'accent_color': '#757575',
        'primary_color': '#757575',
        'secondary_color': '#9E9E9E',
        'disabled_color': '#BDBDBD',
        'font_family': 'Segoe UI'
    }
    apply_stylesheet(app, theme='light_blue_500.xml', extra=extra)
    
    app.setStyleSheet(app.styleSheet() + """
        QMainWindow, QWidget {
            background-color: #F5F5F5;
        }
        QLabel#timer_label {
            font-size: 48px;
            font-weight: bold;
            color: #424242;
        }
        QPushButton {
            background-color: #757575;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #616161;
        }
        QPushButton:pressed {
            background-color: #EEEEEE;
            color: #212121;
        }
        QPushButton#timer_control_button {
            background-color: #757575;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 6px 0px;
            font-weight: bold;
            min-height: 30px;
        }
        QPushButton#timer_control_button:hover {
            background-color: #616161;
        }
        QPushButton#timer_control_button:pressed {
            background-color: #EEEEEE;
            color: #212121;
        }
        QPushButton#item_control_button {
            background-color: #757575;
            color: white;
            border: none;
            border-radius: 0px;
            min-width: 20px;
            max-width: 20px;
            min-height: 20px;
            max-height: 20px;
            font-size: 16px;
            font-weight: bold;
            padding: 0px 0px 3px 0px;
            margin: 0px 2px;
            line-height: 16px;
            text-align: center;
        }
        QPushButton#item_control_button:hover {
            background-color: #616161;
        }
        QPushButton#item_control_button:pressed {
            background-color: #424242;
        }
        QListWidget::item:selected {
            background-color: #E0E0E0;
            color: #000000;
        }
        QListWidget::item:hover {
            background-color: #F5F5F5;
        }
        QComboBox {
            color: #000000;
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid #757575;
            selection-background-color: #9E9E9E;
            selection-color: #000000;
        }
        QLabel#number_label {
            color: #424242;
            font-size: 11px;
            font-weight: bold;
            min-width: 12px;
            max-width: 12px;
            padding-right: 0px;
            padding-left: 0px;
            margin-left: 0px;
        }
        QComboBox#time_combo {
            color: #000000;
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid #757575;
            border-radius: 3px;
            padding: 1px 2px;
            font-size: 10px;
            min-width: 50px;
            max-width: 50px;
            text-align: center;
        }
        QComboBox#time_combo QAbstractItemView {
            background-color: white;
            color: #000000;
            selection-background-color: #9E9E9E;
            selection-color: #000000;
            border: 1px solid #757575;
            font-size: 10px;
            padding: 4px;
            min-width: 50px;
        }
        QComboBox QAbstractScrollArea {
            border: none;
        }
        QComboBox QScrollBar {
            width: 0px;
            height: 0px;
            background: transparent;
        }
        QComboBox#time_combo::drop-down {
            width: 0px;
            border: none;
        }
        QComboBox#time_combo::down-arrow {
            width: 0px;
            height: 0px;
        }
        QWidget#button_container {
            background-color: transparent;
            min-height: 24px;
            max-height: 24px;
        }
        QScrollBar:vertical {
            background: #F5F5F5;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #9E9E9E;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background: #F5F5F5;
            height: 10px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #9E9E9E;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        *:focus {
            outline: 1px solid #757575;
        }
        /* タスク編集用のスタイル */
        #task_edit {
            background-color: white;
            border: 1px solid #757575;
            color: #000000;
            padding: 4px;
            min-width: 150px;
            min-height: 24px;
            font-size: 13px;
            selection-background-color: #9E9E9E;
            selection-color: #000000;
        }
        /* 日付時刻ラベルのスタイル - フォントサイズだけ大きく */
        QLabel#date_time_label {
            color: #000000;
            font-weight: normal;  /* 太字を解除 */
            font-size: 12px;  /* フォントサイズを大きく */
            padding: 2px 0px;  /* 上下のパディングを追加 */
        }
    """)
    
    window = WindowsClockStylePomodoro()
    window.show()
    sys.exit(app.exec())
    
