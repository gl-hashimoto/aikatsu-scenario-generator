import pandas as pd

def quick_analyze(file_path):
    """軽量な分析（最初の数行のみ）"""
    print(f"\n{'='*60}")
    print(f"ファイル: {file_path.split('/')[-1]}")
    print(f"{'='*60}\n")

    try:
        # シート名のみ取得
        excel_file = pd.ExcelFile(file_path)
        print(f"シート数: {len(excel_file.sheet_names)}")
        print(f"シート名: {excel_file.sheet_names}\n")

        # 最初のシートのみ分析
        first_sheet = excel_file.sheet_names[0]
        print(f"分析対象: {first_sheet}")

        # 最初の10行のみ読み込み
        df = pd.read_excel(file_path, sheet_name=first_sheet, nrows=10)

        print(f"\n行数（サンプル）: 10行")
        print(f"列数: {len(df.columns)}")
        print(f"\nカラム名:")
        for i, col in enumerate(df.columns, 1):
            # データ型も表示
            dtype = df[col].dtype
            print(f"  {i}. {col} ({dtype})")

        print(f"\n最初の5行:")
        print(df.head(5).to_string(max_colwidth=30))

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    files = [
        "/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/8502_記事ネタ提案ツール/愛カツ数字確認シート.xlsx",
        "/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/8502_記事ネタ提案ツール/愛カツLINE配信シート(2025_6_16～.xlsx"
    ]

    for file_path in files:
        quick_analyze(file_path)
