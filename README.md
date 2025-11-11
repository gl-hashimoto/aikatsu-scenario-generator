# 🎬 愛カツ シナリオ生成AI

WEBメディア「愛カツ」向けの漫画記事シナリオを自動生成するAIツールです。

## ✨ 主な機能

### 🔬 記事分析＆ネタ展開
ヒット記事を多角的に分析し、新しいテーマのアイデアを自動生成します。

**特徴:**
- **3段階の深層分析**
  - フェーズ1: 基本分析（感情トリガー、キャラクター、オチの評価）
  - フェーズ2: 深堀り分析（ヒットの本質、感情曲線、再現可能な法則）
  - フェーズ3: 新テーマ提案（隣地拡張 + 飛び地挑戦）

- **オチの徹底分析**
  - 5つの評価軸（意外性、スカッと度、感情の落差、因果応報度、共感納得度）
  - オチパターンの分類と応用方法の提案
  - 10種類の多様なオチバリエーション

- **自動テーマ生成**
  - 5-20個のテーマを一度に生成
  - 隣地拡張（安全な拡張）と飛び地挑戦（新領域）のバランス
  - 記事タイトル、あらすじ、ヒット要素、予想PV、難易度を含む

### 📝 ネタ管理
アイデアを素早く記録し、AIが自動整理・分類します。

**特徴:**
- **💡 クイック追加**: 思いついたアイデアをすぐメモ
- **🤖 AI整理**: 未整理のメモを自動で15カテゴリに分類
  - トーン（スカッと、感動、ハラハラ、ほっこり等）
  - シチュエーション（職場、家庭、学校、結婚式等）
  - 主人公タイプ（主婦、OL、学生等）
  - 敵対者タイプ（義母、上司、元カノ等）
  - 結末パターン（因果応報、逆転勝利、成長等）
  - その他11カテゴリ

- **📋 要素一覧**: 登録済みの要素を15カテゴリで管理
- **マージ機能**: AI分析結果を既存データに統合

### 🤖 シナリオ生成
ネタ管理のデータを活用して、高品質なシナリオを自動生成します。

**特徴:**
- **データ駆動型**: ネタ管理の登録要素から動的に選択
- **柔軟な設定**:
  - 🎲 AIにおまかせ（自動選択）
  - ✏️ カスタム入力（自由記述）
  - 📚 登録要素から選択

- **出力内容**:
  - 記事タイトル（60-80文字、記号付き）
  - 起承転結の4部構成
  - 場面説明、展開、セリフ、心理描写
  - オチ・結末
  - Markdown形式でダウンロード可能

## 🚀 使い方

### Streamlit Cloudで使う（推奨）

1. **アクセス**: デプロイされたURLにアクセス
2. **API Key設定**: 「⚙️ 設定」ページでAnthropic API Keyを入力
3. **機能を選択**: 記事分析、ネタ管理、シナリオ生成のいずれかを選択
4. **使用開始**: 各機能のガイドに従って操作

### ローカルで使う

#### 1. リポジトリをクローン
```bash
git clone <repository-url>
cd manga-scenario-generator
```

#### 2. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

#### 3. API Key設定（2つの方法）

**方法A: アプリ内で設定（簡単）**
```bash
streamlit run app.py
```
→ 「⚙️ 設定」ページでAPI Keyを入力

**方法B: secrets.tomlで設定**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.tomlを編集してAPI Keyを設定
streamlit run app.py
```

## 🛠 Streamlit Cloudへのデプロイ

詳しい手順は [DEPLOY.md](DEPLOY.md) を参照してください。

### 簡易手順:

1. **GitHubリポジトリを作成**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Streamlit Cloudにデプロイ**
   - https://share.streamlit.io にアクセス
   - GitHubアカウントでログイン
   - 「New app」をクリック
   - リポジトリとブランチを選択
   - Main file path: `app.py`
   - 「Deploy」をクリック

3. **API Keyを設定**
   - デプロイ後、「Settings」→「Secrets」を開く
   - 以下を追加:
     ```toml
     ANTHROPIC_API_KEY = "your_api_key_here"
     ```
   - 保存

## 📁 ファイル構成

```
manga-scenario-generator/
├── app.py                          # メインアプリケーション
├── requirements.txt                # 依存パッケージ
├── README.md                       # このファイル
├── DEPLOY.md                       # デプロイ手順
├── .gitignore                      # Git除外設定
│
├── .streamlit/
│   ├── secrets.toml.example       # API Key設定例
│   └── secrets.toml               # API Key（gitignore）
│
├── pages/
│   └── article_analysis.py        # 記事分析ページ
│
├── utils/
│   └── prompt_library.py          # プロンプト管理
│
├── prompts/
│   ├── analysis/
│   │   ├── basic_analysis.txt     # 基本分析プロンプト
│   │   └── deep_analysis.txt      # 深堀り分析プロンプト
│   ├── theme_generation/
│   │   └── generate_themes.txt    # テーマ生成プロンプト
│   └── standalone/
│       └── chatgpt_complete_analysis.txt  # ChatGPT/Gemini用
│
└── data/
    ├── neta_elements.json         # ネタ要素データ
    └── neta_quick_notes.json      # クイック追加メモ
```

## 🎯 ChatGPT/Geminiでも使える！

`prompts/standalone/chatgpt_complete_analysis.txt` を使えば、Streamlitアプリを使わずに、ChatGPTやGeminiでも同じ分析ができます。

**使い方:**
1. ファイルを開く
2. 全体をコピー
3. 「【ここにタイトルを入力】」と「【ここに記事の内容・あらすじを入力】」を実際の記事内容に置き換え
4. ChatGPT/Geminiに貼り付けて送信

## 🔧 技術スタック

- **フロントエンド**: Streamlit 1.32+
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **データ処理**: Pandas, JSON
- **その他**: Python 3.8+

## 📊 データ管理

### ネタ要素データ（neta_elements.json）
15カテゴリ、200以上の要素を管理：
- トーン、シチュエーション、主人公タイプ、敵対者タイプ
- 結末パターン、感情トリガー、対立要因、展開パターン
- セリフパターン、数字の使い方、時期設定、場所設定
- 関係性、年齢層、文体・演出

### クイックノート（neta_quick_notes.json）
未整理のアイデアメモを一時保存。AI整理機能で自動分類されます。

## 🤝 サポート

質問や問題がある場合は、開発者に連絡してください。

## 📝 ライセンス

Private Use Only - 愛カツ内部利用限定
