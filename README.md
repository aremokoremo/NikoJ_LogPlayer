# ニコニコ実況 過去ログ再生プレイヤー

## 概要
ニコニコ実況の過去ログをダウンロードして、デジタルテロッパで表示するスクリプトです。

### 説明ページ
http://d.hatena.ne.jp/aremokoremo/20160110/1452444565

### 参考動画
[![image](http://img.youtube.com/vi/SlJEGiAil20/0.jpg)](https://www.youtube.com/watch?v=SlJEGiAil20)


## 実行に必要な環境
- pythonがインストールされている事。(Ver 2.7.5で動作確認しました)
- スクリプトを実行するPCが、インターネット接続されている事
- デジタルテロッパが、スクリプトを実行するPCと同一のネットワーク内に存在する事。
- TVレコーダがデジタルテロッパ経由でテレビに接続されている事

## 使い方
コマンドラインからの実行となります

### 準備
- NikoJkLogPlayer.pyを、適当なところにコピーしてください
- コマンドラインツールを立ち上げ、NikoJkLogPlayer.pyのありかに移動してください

```
$ cd <NikoJkLogPlayer.pyのありか> 
```

### 起動
```
$ python NikoJkLogPlayer.py
```

### 各種設定
ニコニコ動画のアカウント、デジタルテロッパのIPアドレス設定が必要ですが、  
起動後、画面の説明に沿ってすすめれば完了します。

### 過去ログのダウンロード
ログ取得したいテレビ番組の情報（チャンネル、開始日時、終了日時の入力が必要ですが、  
画面の説明に沿って進めてください。

### デジタルテロッパでのコメント再生開始
ログ取得が完了すると、開始するかどうかを聞かれますので、  
画面の説明に沿って進めてください。

「開始」後、５秒後にコメント再生を実際に開始しますので、  
TVレコーダで録画した番組をこのタイミングに合わせて再生開始してください。


## 生成ファイル
利用後、設定内容、ダウンロードした過去ログのファイルが保存されます。


     ├── NikoJkLogPlayer.py
     ├── config
     │   ├── nico_account.txt
     │   └── teloppa_config.txt
     └── xml
         ├── jkX-yyyymmddhhmmss-yyyymmddhhmmss.xml
         ├── jkX-yyyymmddhhmmss-yyyymmddhhmmss.xml
         :
         └── jkX-yyyymmddhhmmss-yyyymmddhhmmss.xml


## 開発者向け
### デバッグ用起動
"-d" オプションをつけると、デバッグ用ログが大量に出ます
```
$ python NikoJkLogPlayer.py -d
```

## 更新履歴
### Ver.1.0 / 2013/01/05
- 初版


