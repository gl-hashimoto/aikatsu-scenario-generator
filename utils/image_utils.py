"""
画像処理ユーティリティ
Claude APIに送信する前に画像をリサイズする機能を提供
"""
from PIL import Image
import base64
import io
from typing import Tuple, Optional


def resize_image_for_api(
    image_bytes: bytes,
    max_dimension: int = 2000,
    quality: int = 85
) -> bytes:
    """
    画像をClaude APIの制限に合わせてリサイズする
    
    Args:
        image_bytes: 画像のバイトデータ
        max_dimension: 最大サイズ（幅または高さの最大値、デフォルト: 2000px）
        quality: JPEG品質（デフォルト: 85）
    
    Returns:
        リサイズされた画像のバイトデータ
    """
    try:
        # 画像を開く
        image = Image.open(io.BytesIO(image_bytes))
        
        # 元のサイズを取得
        width, height = image.size
        
        # リサイズが必要かチェック
        if width <= max_dimension and height <= max_dimension:
            # リサイズ不要
            return image_bytes
        
        # アスペクト比を保ちながらリサイズ
        if width > height:
            # 横長
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            # 縦長または正方形
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        # リサイズ実行
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # バイトデータに変換
        output = io.BytesIO()
        
        # フォーマットを保持（JPEGまたはPNG）
        if image.format == 'PNG':
            resized_image.save(output, format='PNG', optimize=True)
        else:
            # デフォルトはJPEG
            # RGBモードに変換（RGBAの場合）
            if resized_image.mode in ('RGBA', 'LA', 'P'):
                # 白背景を作成
                rgb_image = Image.new('RGB', resized_image.size, (255, 255, 255))
                if resized_image.mode == 'P':
                    resized_image = resized_image.convert('RGBA')
                rgb_image.paste(resized_image, mask=resized_image.split()[-1] if resized_image.mode == 'RGBA' else None)
                resized_image = rgb_image
            resized_image.save(output, format='JPEG', quality=quality, optimize=True)
        
        output.seek(0)
        return output.read()
        
    except Exception as e:
        # エラーが発生した場合は元の画像を返す
        print(f"画像リサイズエラー: {e}")
        return image_bytes


def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    画像バイトデータをbase64エンコードする
    
    Args:
        image_bytes: 画像のバイトデータ
    
    Returns:
        base64エンコードされた文字列
    """
    return base64.b64encode(image_bytes).decode('utf-8')


def get_image_mime_type(image_bytes: bytes) -> str:
    """
    画像のMIMEタイプを取得する
    
    Args:
        image_bytes: 画像のバイトデータ
    
    Returns:
        MIMEタイプ（例: 'image/jpeg', 'image/png'）
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        format_to_mime = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'WEBP': 'image/webp'
        }
        return format_to_mime.get(image.format, 'image/jpeg')
    except Exception:
        return 'image/jpeg'


def process_image_for_claude_api(
    image_bytes: bytes,
    max_dimension: int = 2000,
    quality: int = 85
) -> Tuple[str, str]:
    """
    画像をClaude API用に処理する（リサイズ + base64エンコード）
    
    Args:
        image_bytes: 画像のバイトデータ
        max_dimension: 最大サイズ（デフォルト: 2000px）
        quality: JPEG品質（デフォルト: 85）
    
    Returns:
        (base64エンコードされた文字列, MIMEタイプ)のタプル
    """
    # リサイズ
    resized_bytes = resize_image_for_api(image_bytes, max_dimension, quality)
    
    # base64エンコード
    base64_string = encode_image_to_base64(resized_bytes)
    
    # MIMEタイプ取得
    mime_type = get_image_mime_type(resized_bytes)
    
    return base64_string, mime_type




