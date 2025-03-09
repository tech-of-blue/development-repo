import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import json
import os

class PomodoroTodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ポモドーロ & ToDoリスト")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
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
        
        # UIの作成
        self.create_ui()
    
    def create_ui(self):
        # メインフレームを左右に分割
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側：ポモドーロタイマー
        timer_frame = ttk.LabelFrame(main_frame, text="ポモドーロタイマー")
        timer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # タイマー表示
        self.timer_label = ttk.Label(timer_frame, text="25:00", font=("Arial", 48))
        self.timer_label.pack(pady=20)
        
        # 状態表示
        self.status_label = ttk.Label(timer_frame, text="準備完了", font=("Arial", 14))
        self.status_label.pack(pady=10)
        
        # タイマーコントロールボタン
        control_frame = ttk.Frame(timer_frame)
        control_frame.pack(pady=20)
        
        self.start_button = ttk.Button(control_frame, text="開始", command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="一時停止", command=self.pause_timer, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.reset_button = ttk.Button(control_frame, text="リセット", command=self.reset_timer)
        self.reset_button.grid(row=0, column=2, padx=5)
        
        # 右側：ToDoリスト
        todo_frame = ttk.LabelFrame(main_frame, text="ToDoリスト")
        todo_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 新規タスク入力
        input_frame = ttk.Frame(todo_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.task_entry = ttk.Entry(input_frame, width=40)
        self.task_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.task_entry.bind("<Return>", lambda event: self.add_task())
        
        add_button = ttk.Button(input_frame, text="追加", command=self.add_task)
        add_button.pack(side=tk.RIGHT, padx=5)
        
        # ToDoリスト表示
        todo_list_frame = ttk.Frame(todo_frame)
        todo_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(todo_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ToDoリストの表示
        self.todo_listbox = tk.Listbox(todo_list_frame, selectmode=tk.SINGLE, height=15)
        self.todo_listbox.pack(fill=tk.BOTH, expand=True)
        self.todo_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.todo_listbox.yview)
        
        # ToDoリストのボタン
        todo_button_frame = ttk.Frame(todo_frame)
        todo_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        complete_button = ttk.Button(todo_button_frame, text="完了", command=self.complete_task)
        complete_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(todo_button_frame, text="削除", command=self.delete_task)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # 初期ToDoリストの表示
        self.update_todo_listbox()
    
    # タイマー関連の関数
    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            
            if self.timer_thread is None or not self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self.run_timer)
                self.timer_thread.daemon = True
                self.timer_thread.start()
    
    def pause_timer(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
    
    def reset_timer(self):
        self.is_running = False
        self.is_break = False
        self.remaining_time = self.pomodoro_time
        self.update_timer_display()
        self.status_label.config(text="準備完了")
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
    
    def run_timer(self):
        while self.remaining_time > 0 and self.is_running:
            mins, secs = divmod(self.remaining_time, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            
            # GUIの更新はメインスレッドで行う
            self.root.after(0, lambda t=time_str: self.timer_label.config(text=t))
            
            time.sleep(1)
            self.remaining_time -= 1
        
        if self.remaining_time <= 0 and self.is_running:
            # タイマー終了時の処理
            if not self.is_break:
                # 作業終了、休憩開始
                self.root.after(0, lambda: self.status_label.config(text="休憩時間です！"))
                self.root.after(0, lambda: messagebox.showinfo("ポモドーロ", "作業時間が終了しました。休憩しましょう！"))
                self.is_break = True
                self.remaining_time = self.break_time
                self.root.after(0, self.update_timer_display)
                self.root.after(0, self.start_timer)
            else:
                # 休憩終了、次のポモドーロへ
                self.root.after(0, lambda: self.status_label.config(text="準備完了"))
                self.root.after(0, lambda: messagebox.showinfo("ポモドーロ", "休憩時間が終了しました。次の作業を始めましょう！"))
                self.is_break = False
                self.remaining_time = self.pomodoro_time
                self.root.after(0, self.update_timer_display)
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.pause_button.config(state=tk.DISABLED))
                self.is_running = False
    
    def update_timer_display(self):
        mins, secs = divmod(self.remaining_time, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        self.timer_label.config(text=time_str)
    
    # ToDoリスト関連の関数
    def add_task(self):
        task = self.task_entry.get().strip()
        if task:
            self.todo_list.append({"task": task, "completed": False})
            self.task_entry.delete(0, tk.END)
            self.update_todo_listbox()
            self.save_todos()
    
    def complete_task(self):
        selected = self.todo_listbox.curselection()
        if selected:
            index = selected[0]
            self.todo_list[index]["completed"] = not self.todo_list[index]["completed"]
            self.update_todo_listbox()
            self.save_todos()
    
    def delete_task(self):
        selected = self.todo_listbox.curselection()
        if selected:
            index = selected[0]
            del self.todo_list[index]
            self.update_todo_listbox()
            self.save_todos()
    
    def update_todo_listbox(self):
        self.todo_listbox.delete(0, tk.END)
        for item in self.todo_list:
            prefix = "✓ " if item["completed"] else "□ "
            self.todo_listbox.insert(tk.END, prefix + item["task"])
            
            # 完了したタスクは色を変える
            if item["completed"]:
                self.todo_listbox.itemconfig(tk.END, fg="gray")
    
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
    root = tk.Tk()
    app = PomodoroTodoApp(root)
    root.mainloop()