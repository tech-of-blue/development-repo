# このコードは現在動きません。


import PySimpleGUI as sg
import time
import threading
import json
import os

class PomodoroTodoApp:
    def __init__(self):
        # タイマー変数
        self.pomodoro_time = 25 * 60  # 25分（秒単位）
        self.break_time = 5 * 60      # 5分（秒単位）
        self.is_running = False
        self.is_break = False
        self.remaining_time = self.pomodoro_time
        self.timer_thread = None
        
        # ToDoリスト変数
        self.todo_list = []
        self.load_todos()
        
        # テーマ設定
        sg.theme('LightBlue2')
        
        # レイアウトの作成
        self.create_layout()
        
    def create_layout(self):
        # 左側：ポモドーロタイマー
        timer_frame = [
            [sg.Text('25:00', font=('Arial', 48), key='-TIMER-', justification='center')],
            [sg.Text('準備完了', font=('Arial', 14), key='-STATUS-', justification='center')],
            [sg.ProgressBar(max_value=self.pomodoro_time, orientation='h', size=(30, 20), key='-PROGRESS-')],
            [sg.Button('開始', key='-START-'), sg.Button('リセット', key='-RESET-')]
        ]
        
        # 右側：ToDoリスト
        todo_frame = [
            [sg.Text('ToDoリスト', font=('Arial', 16))],
            [sg.InputText(key='-TASK-', size=(30, 1)), sg.Button('追加', key='-ADD-')],
            [sg.Listbox(values=[], size=(40, 10), key='-TODO-LIST-', enable_events=True)],
            [sg.Button('完了/未完了', key='-COMPLETE-'), sg.Button('削除', key='-DELETE-')]
        ]
        
        # メインレイアウト
        layout = [
            [sg.Column(timer_frame), sg.VSeparator(), sg.Column(todo_frame)]
        ]
        
        # ウィンドウの作成
        self.window = sg.Window('ポモドーロ & ToDoリスト', layout, finalize=True)
        
        # ToDoリストの初期表示
        self.update_todo_listbox()
        
    def run(self):
        while True:
            event, values = self.window.read()
            
            if event == sg.WINDOW_CLOSED:
                break
            
            # タイマー関連のイベント
            if event == '-START-':
                self.toggle_timer()
            elif event == '-RESET-':
                self.reset_timer()
            
            # ToDoリスト関連のイベント
            elif event == '-ADD-':
                self.add_task(values['-TASK-'])
            elif event == '-COMPLETE-':
                self.complete_task(values['-TODO-LIST-'])
            elif event == '-DELETE-':
                self.delete_task(values['-TODO-LIST-'])
        
        self.window.close()
    
    def toggle_timer(self):
        if self.is_running:
            # タイマー停止
            self.is_running = False
            self.window['-START-'].update('開始')
            self.window['-STATUS-'].update('一時停止中')
        else:
            # タイマー開始
            self.is_running = True
            self.window['-START-'].update('停止')
            
            status_text = '作業中' if not self.is_break else '休憩中'
            self.window['-STATUS-'].update(status_text)
            
            # タイマースレッドが実行中でなければ開始
            if self.timer_thread is None or not self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
                self.timer_thread.start()
    
    def reset_timer(self):
        self.is_running = False
        self.is_break = False
        self.remaining_time = self.pomodoro_time
        self.window['-START-'].update('開始')
        self.window['-STATUS-'].update('準備完了')
        
        # タイマー表示の更新
        mins, secs = divmod(self.remaining_time, 60)
        self.window['-TIMER-'].update(f"{mins:02d}:{secs:02d}")
        self.window['-PROGRESS-'].update(current_count=self.remaining_time, max=self.pomodoro_time)
    
    def run_timer(self):
        while self.is_running and self.remaining_time > 0:
            # 1秒待機
            time.sleep(1)
            
            # 残り時間を減らす
            self.remaining_time -= 1
            
            # 表示を更新
            mins, secs = divmod(self.remaining_time, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            
            # GUIスレッドからの更新
            if self.is_running:  # 停止されていないことを確認
                self.window['-TIMER-'].update(time_str)
                self.window['-PROGRESS-'].update(
                    current_count=self.remaining_time,
                    max=self.pomodoro_time if not self.is_break else self.break_time
                )
        
        # タイマー終了時の処理
        if self.is_running and self.remaining_time <= 0:
            self.is_running = False
            self.window['-START-'].update('開始')
            
            # 作業と休憩を切り替え
            if not self.is_break:
                # 作業終了、休憩開始
                self.is_break = True
                self.remaining_time = self.break_time
                self.window['-STATUS-'].update('休憩時間です！')
                sg.popup_notify('作業時間が終了しました！', '休憩しましょう')
            else:
                # 休憩終了、作業開始
                self.is_break = False
                self.remaining_time = self.pomodoro_time
                self.window['-STATUS-'].update('準備完了')
                sg.popup_notify('休憩時間が終了しました！', '次の作業を始めましょう')
            
            # タイマー表示の更新
            mins, secs = divmod(self.remaining_time, 60)
            self.window['-TIMER-'].update(f"{mins:02d}:{secs:02d}")
            self.window['-PROGRESS-'].update(
                current_count=self.remaining_time,
                max=self.pomodoro_time if not self.is_break else self.break_time
            )
    
    def add_task(self, task_text):
        task = task_text.strip()
        if task:
            self.todo_list.append({"task": task, "completed": False})
            self.window['-TASK-'].update('')
            self.update_todo_listbox()
            self.save_todos()
    
    def complete_task(self, selected_items):
        if selected_items and len(selected_items) > 0:
            selected_text = selected_items[0]
            # テキストから元のインデックスを見つける
            for i, item in enumerate(self.todo_list):
                display_text = ("✓ " if item["completed"] else "□ ") + item["task"]
                if display_text == selected_text:
                    self.todo_list[i]["completed"] = not self.todo_list[i]["completed"]
                    self.update_todo_listbox()
                    self.save_todos()
                    break
    
    def delete_task(self, selected_items):
        if selected_items and len(selected_items) > 0:
            selected_text = selected_items[0]
            # テキストから元のインデックスを見つける
            for i, item in enumerate(self.todo_list):
                display_text = ("✓ " if item["completed"] else "□ ") + item["task"]
                if display_text == selected_text:
                    del self.todo_list[i]
                    self.update_todo_listbox()
                    self.save_todos()
                    break
    
    def update_todo_listbox(self):
        todo_display = []
        for item in self.todo_list:
            prefix = "✓ " if item["completed"] else "□ "
            todo_display.append(prefix + item["task"])
        self.window['-TODO-LIST-'].update(values=todo_display)
    
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

# メイン実行部分
if __name__ == "__main__":
    app = PomodoroTodoApp()
    app.run()


