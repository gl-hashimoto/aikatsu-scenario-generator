"""
プロンプトライブラリ
外部ファイルからプロンプトを読み込み、動的に置換する
"""
import os


class PromptLibrary:
    def __init__(self, base_dir=None):
        """
        Args:
            base_dir: プロンプトファイルのベースディレクトリ
        """
        if base_dir is None:
            # デフォルトはこのファイルの親ディレクトリ/prompts
            current_dir = os.path.dirname(os.path.dirname(__file__))
            base_dir = os.path.join(current_dir, 'prompts')

        self.base_dir = base_dir
        self.cache = {}

    def load(self, category, prompt_name, use_cache=True):
        """
        プロンプトファイルを読み込み

        Args:
            category: カテゴリ名（analysis, theme_generation など）
            prompt_name: プロンプトファイル名（拡張子なし）
            use_cache: キャッシュを使用するか（デフォルト: True）

        Returns:
            str: プロンプトの内容
        """
        cache_key = f"{category}/{prompt_name}"

        # キャッシュチェック
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]

        # ファイル読み込み
        file_path = os.path.join(self.base_dir, category, f"{prompt_name}.txt")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # キャッシュに保存
            self.cache[cache_key] = content
            return content

        except FileNotFoundError:
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {file_path}")

    def format(self, category, prompt_name, **kwargs):
        """
        プロンプトを読み込み、プレースホルダーを置換

        Args:
            category: カテゴリ名
            prompt_name: プロンプトファイル名
            **kwargs: 置換する変数

        Returns:
            str: 置換済みのプロンプト
        """
        template = self.load(category, prompt_name)
        return template.format(**kwargs)

    def clear_cache(self):
        """キャッシュをクリア"""
        self.cache = {}
