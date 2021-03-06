# PictureGathering

## 概要
ツイッターでfavした画像含みツイートから画像を収集し、
ローカルに保存するツイッタークローラ。  
主に自分のツイッターアカウントでfavしたツイートを対象とする。

## 特徴（できること）
- fav/retweetした画像含みツイートから画像を収集し、ローカルに保存する。  
- 収集した画像の情報をDBに蓄積する。  
- 収集した画像を一覧で見ることができるhtmlを出力する。  
- 各画像のオリジナル画像(:orig)とそのツイートへのリンクを付与する。  
- ローカルに何枚まで保存するかの制限設定あり。  
- image magickによる簡単な加工。  
- 処理完了時に通知ツイートを送る。
    - 前日以前の通知ツイートは自動的に削除されます。

※定期的な実行を前提としてますが機能としては同梱していないので「タスクのスケジュール」などOS標準の機能で定期実行してください。  
※windows 10でのみ動作確認をしております。  

## 前提として必要なもの
- ツイッターアカウントのAPIトークン
    - TwitterAPIを使用するためのAPIトークン
    - 詳しくはこちら(←あとでリンク貼る)
- 画像加工のためのimage magick
    - ローカル保存時にimage magickで縮小処理をかけています。
    - 詳しくはこちら(←あとでリンク貼る)

## 使い方
0. （Windowsを前提に説明します。linuxの人は適宜読み替えてね。）
1. このリポジトリをDL
    - 右上の「Clone or download」->「Download ZIP」からDLして解凍
1. config_example.iniの中身を自分用に編集してconfig.iniにリネーム。
    - ローカルの保存先パスを設定する。（必須）
    - ツイッターアカウントのAPIトークンを設定する（必須）。  
    - image magickをインストールしておく（任意）。  
1. PictureGathering.pyを実行する。
1. 出力されたPictureGathering.htmlを確認する。
1. ローカルの保存先パスに画像が保存されたことを確認する。


## Licence

[MIT](https://github.com/tcnksm/tool/blob/master/LICENCE)

## Author
[shift](https://twitter.com/_shift4869)
