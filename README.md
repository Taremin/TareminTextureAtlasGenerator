# Taremin Texture Atlas Generator

**このアドオンは現在開発最中のアルファ版です。**
**壮絶にバグってる可能性もありますので、もし不都合があったら報告していただけるとたすかります。**
**正式公開時は GitHub に移行します**

## なにこれ？

選択したオブジェクトの Texture Atlas を生成するアドオンです。 (Blender 2.80 以降必須)

生成された Texture Atlas を使用することでマテリアル数の削減を目的とします。

## インストール

zip ファイルをダウンロードして、「編集」「設定」「アドオン」「インストール」を選択し、ダウンロードした zip ファイルをインストールします。

## 使い方

1. Texture Atlas を生成したいオブジェクトを選択します。（複数可）
2. 3Dビューの Properties Shelf （デフォルトだとNキーで出る領域）で「ツール」タブを開く
3. Texture Atlas Generator の設定をする（後述）
4. Generate Texture を押して実行（しばらく時間がかかることがあります）

## 生成されるもの(基本)

- Texture Atlas （テクスチャ）
  - テクスチャ名は Output texture name で設定できます
- Texture Atlas 用の UVMap
  - 処理対象の各オブジェクトに追加されます
  - UVMap名は Output UVMap name で設定できます
- [元のマテリアル名] + ".atlas" という名前のマテリアル
  - 元のマテリアルのノードツリーからテクスチャ参照、UVMap参照を Texture Atlas のものに差し替えたもの

その他、後述の Texture Group に応じたテクスチャが生成されます。

## Texture Group, Texture Link

ノーマルマップやマスクテクスチャなど、元のテクスチャと同じUVMapを使用する、別のテクスチャを Texture Atlas に対応させるために使用します。

たとえば、"服" というテクスチャと "服ノーマルマップ" というノーマルマップ用のテクスチャがあるとします。
このとき、Texture Atlas を作ると "服" と "服ノーマルマップ" のUVの位置がずれてしまいます。
それを防ぐために、"服" と "服ノーマルマップ" というテクスチャは同じ UVMap だということを事前に設定することで、Texture Atlas と Texture Atlas に対応したノーマルマップ両方を生成することができます。

この場合、Texture Group に「＋」ボタンで項目を追加し、 Normal というグループ名にして、色を (0.5, 0.5, 1.0) にします。
そして Texture Link に「＋」ボタンで項目を追加し、左から「Normal」「服」「服ノーマルマップ」に設定します。
これで "Generate Texture" を実行すると2枚のテクスチャが生成されます。

## その他設定項目

- "Remove all UVMaps except atlas"
  - 生成した Texture Atlas 用の UVMap 以外を削除します
  - 既存の UVMap が残っていると Unity などで他の UVMap を参照してしまうことがあります
- "Replace face material with texture atlas"
  - 処理対象オブジェクトの面に割り当てられたマテリアルを、Texture Atlas 用のマテリアルに置き換えます
- "Remove material slots except active"
  - アクティブなマテリアルスロット以外を削除します
  - 事前に Texture Atlas 用のマテリアルを作成してアクティブにしておくことで処理後に余計なマテリアルが削除されます
- "Replace active material nodetree with texture atlas"
  - マテリアルスロットを削除するときにのみ現れる設定です
  - アクティブなマテリアルスロットの画像テクスチャノードの画像参照を Texture Atlas に置き換えます
- "Auto save atlas images"
  - 生成した Texture Atlas 画像を自動でファイルに保存します
  - "Output Directory" で出力先ディレクトリ(フォルダー)を指定できます

## 制限事項

- ミラーモディファイアなど、モディファイアには基本的に非対応
  - モディファイアをすべて適用したあとに使用するのを想定しています

## 更新履歴

- 0.0.3
  - 名前を "Texture Atlas Generator" から "Taremin Texture Atlas Generator" に変更
  - UI を日本語対応
  - Texture Atlas を自動でファイルに保存を追加
  - 画像テクスチャの置換においてUVマップの置換が行われていないことがあるのを修正
  - テクスチャグループ、テクスチャリンク、テクスチャスケール、各項目の上下移動を追加
  - パネルの位置を「ツール」から「Taremin」カテゴリに変更
- 0.0.2
  - テクスチャリンクにおいて画像のサイズが同じかどうかチェックするように修正
  - テクスチャ毎にスケールを指定できる機能の追加
  - テクスチャリンクのリンク先は Texture Atlas に含まないように修正
- 0.0.1
  - 初期実装


## ライセンス

[MITライセンス](./LICENSE)

## 連絡先

Twitter: [@Taremin_VR](https://twitter.com/Taremin_VR) までお気軽に連絡ください。
要望や不具合報告などは Issues か Twitter どちらでもお気軽にどうぞ。