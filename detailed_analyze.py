import pandas as pd

def analyze_sheet(file_path, sheet_name, skip_rows=0):
    """特定シートを詳しく分析"""
    print(f"\n{'='*80}")
    print(f"ファイル: {file_path.split('/')[-1]}")
    print(f"シート: {sheet_name}")
    print(f"{'='*80}\n")

    try:
        # データ読み込み（最初の100行）
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows, nrows=100)

        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")

        print(f"\nカラム名:")
        for i, col in enumerate(df.columns, 1):
            # 非null値の数とデータ型
            non_null = df[col].notna().sum()
            dtype = str(df[col].dtype)
            print(f"  {i:2d}. {col:40s} | {dtype:10s} | 非null: {non_null}/{len(df)}")

        print(f"\n最初の10行:")
        # すべてのカラムを表示（長いものは省略）
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 40)
        print(df.head(10).to_string(index=True))

        # PV、タイトル、CTR等のカラムを探す
        print(f"\n重要カラムの検出:")
        keywords = {
            'タイトル': ['タイトル', 'title', '記事', 'article'],
            'PV': ['PV', 'pv', 'ページビュー', 'pageview'],
            'CTR': ['CTR', 'ctr', 'クリック率'],
            'URL': ['URL', 'url', 'リンク', 'link'],
            '日付': ['日付', '公開日', 'date', '配信日']
        }

        for key, patterns in keywords.items():
            matches = [col for col in df.columns if any(p in str(col) for p in patterns)]
            if matches:
                print(f"  {key}: {matches}")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 分析するシート
    analyses = [
        ("/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/8502_記事ネタ提案ツール/愛カツ数字確認シート.xlsx", "LINE記事別（PV,S,PS）", 0),
        ("/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/8502_記事ネタ提案ツール/愛カツ数字確認シート.xlsx", "記事アクセス", 0),
        ("/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/8502_記事ネタ提案ツール/愛カツLINE配信シート(2025_6_16～.xlsx", "LINE配信シート", 0),
    ]

    for file_path, sheet_name, skip_rows in analyses:
        try:
            analyze_sheet(file_path, sheet_name, skip_rows)
        except Exception as e:
            print(f"\nシート '{sheet_name}' の分析に失敗: {e}\n")
