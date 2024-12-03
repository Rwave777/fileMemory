# fileMemory
## 概要
ファイルのパスを記憶するサービス

## 使い方
1. ファイルをドラック&ドロップする
2. ファイルのパスを記憶する
3. ファイルのパスを確認する


## 環境構築
```python
python -m venv venv
.\venv\Scripts\activate
```
### インストール
```python
pip install flet
pip install pyinstaller==5.13.2
```

### 実行
```python
flet run src -r
```

### パッケージビルド
```python
flet pack src/main.py --name filePathMemory --file-version 1.0.0.0
```

