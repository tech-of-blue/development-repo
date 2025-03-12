import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QListWidget, QLineEdit,
    QLabel, QProgressBar, QMessageBox, QListWidgetItem, QStyleFactory
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QColor

class WindowsClockStylePomodoro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomodoro timer & ToDo List")
        self.setGeometry(100, 100, 400, 500)
        self.setStyle(QStyleFactory.create("Windows"))

        # メインウィジェットとレイアウト
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # ポモドーロタイマー部分
        self.setup_timer_ui()

        # ToDoリスト部分
        self.setup_todo_ui()

        # データの初期化
        self.todo_list = []
        self.load_todos()
        self.update_todo_listbox()

        # タイマー初期化
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.time_left = 25 * 60  # 25分（秒単位）
        self.is_break = False
        self.update_timer_display()

    def setup_timer_ui(self):
        timer_layout = QVBoxLayout()

        self.timer_label = QLabel("25:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Segoe UI", 36, QFont.Bold))  # Windows標準フォント
        timer_layout.addWidget(self.timer_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 25 * 60)
        self.progress_bar.setValue(25 * 60)
        timer_layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("開始")
        self.start_button.clicked.connect(self.start_timer)
        button_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("一時停止")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("リセット")
        self.reset_button.clicked.connect(self.reset_timer)
        button_layout.addWidget(self.reset_button)

        timer_layout.addLayout(button_layout)
        self.main_layout.addLayout(timer_layout)

    def setup_todo_ui(self):
        todo_layout = QVBoxLayout()
        todo_title = QLabel("ToDoリスト")
        todo_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        todo_layout.addWidget(todo_title)

        input_layout = QHBoxLayout()
        self.task_entry = QLineEdit()
        self.task_entry.setPlaceholderText("新しいタスクを入力...")
        self.task_entry.returnPressed.connect(self.add_task)
        input_layout.addWidget(self.task_entry)

        add_button = QPushButton("追加")
        add_button.clicked.connect(self.add_task)
        input_layout.addWidget(add_button)
        todo_layout.addLayout(input_layout)

        self.todo_listbox = QListWidget()
        self.todo_listbox.setAlternatingRowColors(True)
        todo_layout.addWidget(self.todo_listbox)

        task_buttons_layout = QHBoxLayout()
        complete_button = QPushButton("完了/未完了")
        complete_button.clicked.connect(self.complete_task)
        task_buttons_layout.addWidget(complete_button)

        delete_button = QPushButton("削除")
        delete_button.clicked.connect(self.delete_task)
        task_buttons_layout.addWidget(delete_button)
        todo_layout.addLayout(task_buttons_layout)

        self.main_layout.addLayout(todo_layout)

    def start_timer(self):
        self.timer.start(1000)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)

    def pause_timer(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    def reset_timer(self):
        self.timer.stop()
        self.time_left = 25 * 60 if not self.is_break else 5 * 60
        self.update_timer_display()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    def update_timer(self):
        self.time_left -= 1
        self.update_timer_display()

        if self.time_left <= 0:
            self.timer.stop()
            if not self.is_break:
                QMessageBox.information(self, "ポモドーロ完了", "作業時間が終了しました！休憩しましょう。")
                self.is_break = True
                self.time_left = 5 * 60
            else:
                QMessageBox.information(self, "休憩終了", "休憩時間が終了しました！作業を再開しましょう。")
                self.is_break = False
                self.time_left = 25 * 60
            self.update_timer_display()
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)

    def update_timer_display(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        max_value = 25 * 60 if not self.is_break else 5 * 60
        self.progress_bar.setRange(0, max_value)
        self.progress_bar.setValue(self.time_left)

    def add_task(self):
        task = self.task_entry.text().strip()
        if task:
            self.todo_list.append({"task": task, "completed": False})
            self.task_entry.clear()
            self.update_todo_listbox()
            self.save_todos()

    def complete_task(self):
        selected = self.todo_listbox.currentRow()
        if selected >= 0:
            self.todo_list[selected]["completed"] = not self.todo_list[selected]["completed"]
            self.update_todo_listbox()
            self.save_todos()

    def delete_task(self):
        selected = self.todo_listbox.currentRow()
        if selected >= 0:
            del self.todo_list[selected]
            self.update_todo_listbox()
            self.save_todos()

    def update_todo_listbox(self):
        self.todo_listbox.clear()
        for item in self.todo_list:
            prefix = "✓ " if item["completed"] else "□ "
            list_item = QListWidgetItem(prefix + item["task"])
            if item["completed"]:
                list_item.setForeground(QColor("gray"))
            self.todo_listbox.addItem(list_item)

    def save_todos(self):
        with open("todos.json", "w", encoding="utf-8") as f:
            json.dump(self.todo_list, f, ensure_ascii=False)
    
    def load_todos(self):
        try:
            if os.path.exists("todos.json"):
                with open("todos.json", "r", encoding="utf-8") as f:
                    self.todo_list = json.load(f)
        except Exception as e:
            print(f"ToDoリストの読み込みエラー: {e}")
            self.todo_list = []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindowsClockStylePomodoro()
    window.show()
    sys.exit(app.exec())