# 画像サイズエラー解決ガイド

## エラー内容

```
API Error: 400
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "messages.74.content.4.image.source.base64.data: At least one of the image dimensions exceed max allowed size for many-image requests: 2000 pixels"
  }
}
```

## エラーの意味

このエラーは、Claude APIに送信しようとした画像のサイズが制限を超えていることを示しています。

### Claude APIの画像サイズ制限

- **複数画像リクエスト（many-image requests）の場合**: 各画像の最大サイズは **2000ピクセル**
  - 幅と高さの両方が2000ピクセル以下である必要があります
  - どちらか一方でも2000ピクセルを超えているとエラーになります

- **単一画像リクエストの場合**: 最大サイズは **5000ピクセル**

## 解決方法

### 方法1: 画像をリサイズする（推奨）

画像を送信する前に、幅と高さの両方を2000ピクセル以下にリサイズします。

#### Pythonを使用する場合

```python
from PIL import Image
from utils.image_utils import process_image_for_claude_api

# 画像ファイルを読み込む
with open('image.jpg', 'rb') as f:
    image_bytes = f.read()

# リサイズとbase64エンコード
base64_string, mime_type = process_image_for_claude_api(image_bytes, max_dimension=2000)

# Claude APIに送信
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64_string
                }
            },
            {
                "type": "text",
                "text": "この画像を分析してください"
            }
        ]
    }]
)
```

#### オンラインツールを使用する場合

1. [TinyPNG](https://tinypng.com/) - PNG/JPEG圧縮
2. [Squoosh](https://squoosh.app/) - 画像圧縮とリサイズ
3. [ImageResizer](https://imageresizer.com/) - 画像リサイズ

### 方法2: 画像を分割する

大きな画像を複数の小さな画像に分割して、それぞれを個別に送信します。

### 方法3: 画像の数を減らす

複数の画像を送信している場合、画像の数を減らすか、重要な画像だけを選択します。

## 画像リサイズのベストプラクティス

1. **アスペクト比を保持**: 画像の縦横比を維持しながらリサイズします
2. **品質を考慮**: リサイズ時に品質が劣化しないように注意します
3. **ファイルサイズ**: リサイズ後もファイルサイズが大きすぎないようにします

## よくある質問

### Q: なぜ2000ピクセルの制限があるの？

A: Claude APIは複数の画像を処理する際に、計算リソースを効率的に使用するためにサイズ制限を設けています。

### Q: 単一画像の場合はどうなの？

A: 単一画像の場合は最大5000ピクセルまで送信可能です。ただし、複数の画像を含むリクエストの場合は2000ピクセルが上限です。

### Q: リサイズした画像の品質は？

A: `process_image_for_claude_api`関数は、高品質なリサンプリングアルゴリズム（LANCZOS）を使用しているため、品質の劣化は最小限です。

## 実装例

`utils/image_utils.py`に画像処理ユーティリティ関数を実装しています。これらの関数を使用することで、自動的に画像をリサイズできます。

```python
from utils.image_utils import process_image_for_claude_api

# 画像を処理
base64_string, mime_type = process_image_for_claude_api(image_bytes)
```

## 参考リンク

- [Claude API Documentation](https://docs.anthropic.com/claude/reference/messages_post)
- [Pillow (PIL) Documentation](https://pillow.readthedocs.io/)




