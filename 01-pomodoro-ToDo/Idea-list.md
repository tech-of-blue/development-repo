# PyQtやtkinter以外のデスクトップアプリ向けGUIフレームワーク

## 1. Kivy
- クロスプラットフォームのPythonフレームワークで、モバイルアプリにも対応
- pip install kivy

## 2. PySide2/PySide6 (Qt for Python)
- QtのPython公式バインディング。PyQt5と互換性があり、LGPLライセンス
- pip install PySide6

## 3. wxPython
- ネイティブルック＆フィールを持つクロスプラットフォームGUIツールキット
- pip install wxPython

## 4. Dear PyGui
- 高速でシンプルなPython GUIフレームワーク
- pip install dearpygui

## 5. Flexx
- PythonとJavaScriptを使用したGUIフレームワーク
- pip install flexx

## 6. PySimpleGUI
- tkinter、Qt、WxPython、Remiをラップした簡単に使えるGUIフレームワーク
- pip install PySimpleGUI

## 7. Toga (BeeWare)
- ネイティブUIを持つクロスプラットフォームPythonアプリケーション開発ツール
- pip install toga

## 8. Eel
- ElectronライクなPython/JavaScriptライブラリ
- pip install eel




# PySimpleGUIを使ったポモドーロタイマー＆ToDoアプリの実装例

PySimpleGUIは、複雑なGUIフレームワークをシンプルなインターフェースでラップしたライブラリです。以下に、PySimpleGUIを使用したポモドーロタイマーとToDoリストを組み合わせたアプリケーションの実装例を示します。

## 主な機能

- 25分の作業時間と5分の休憩時間を自動で切り替えるポモドーロタイマー
- タスクの追加、完了/未完了の切り替え、削除ができるToDoリスト
- タスクの永続化（JSONファイルに保存）

## 実装のポイント

- シンプルで直感的なユーザーインターフェース
- スレッドを使用したタイマー処理
- JSONを使用したデータの永続化

