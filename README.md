# Taremin Texture Atlas Generator

## なにこれ？

選択したオブジェクトの Texture Atlas を生成するアドオンです。 (Blender 2.80 以降必須)

生成された Texture Atlas を使用することでマテリアル数の削減を目的とします。

## インストール

zip ファイルをダウンロードして、「編集」「設定」「アドオン」「インストール」を選択し、ダウンロードした zip ファイルをインストールします。

## 使い方

1. Texture Atlas を生成したいオブジェクトを選択します。（複数可）
  - 複数のオブジェクトを選択した場合、すべてのオブジェクトのマテリアルから１つのテクスチャアトラスが生成されます
2. 3Dビューの Properties Shelf （デフォルトだとNキーで出る領域）で「ツール」タブを開く
3. Texture Atlas Generator の設定をする（後述）
4. Generate Texture を押して実行（しばらく時間がかかることがあります）

## 生成されるもの(基本)

- Texture Atlas （テクスチャ）
  - テクスチャ名は Output Texture Name で設定できます
- Texture Atlas 用の UVMap
  - 処理対象の各オブジェクトに追加されます
  - UVMap名は Output UVMap Name で設定できます
- Texture Atlas 表示用マテリアル
  - シンプルな表示確認用のマテリアルが対象オブジェクトに追加されます
  - マテリアル名は Output Material Name で設定できます。

その他、後述の Material Group, Texture Group に応じたテクスチャが生成されます。

## Material Group

基本的には選択したオブジェクトのマテリアルを１つにまとめますが、一部のマテリアルは別のマテリアルとしてまとめたい場合に利用できるのが Material Group です。
これは正規表現でマッチしたマテリアルを別のマテリアルにグループとしてまとめる機能です。

たとえば、正規表現を `\[([^\]]+)\]` マテリアル名を `AtlasMaterial.\1` とした場合、 `マテリアル[Metal]` というマテリアルは `AtlasMaterial.Metal` 、 `マテリアル[Cloth]` というマテリアルは `AtlasMaterial.Cloth` にまとめられます。
上記の例の通り、グループ名では後方参照が利用可能です。
マテリアル名と同様にテクスチャ名もグループごとに指定可能です。こちらも後方参照が利用可能です。

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
- "Auto save atlas images"
  - 生成した Texture Atlas 画像を自動でファイルに保存します
  - "Output Directory" で出力先ディレクトリ(フォルダー)を指定できます

## 制限事項

- ミラーモディファイアなど、モディファイアには基本的に非対応
  - モディファイアをすべて適用したあとに使用するのを想定しています

## ライセンス

[MITライセンス](./LICENSE)

## 連絡先

Twitter: [@Taremin_VR](https://twitter.com/Taremin_VR) までお気軽に連絡ください。
要望や不具合報告などは Issues か Twitter どちらでもお気軽にどうぞ。