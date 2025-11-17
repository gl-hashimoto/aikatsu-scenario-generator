import pandas as pd
import sys

def analyze_excel(file_path):
    """Excelファイルの構造を分析"""
    print(f"\n{'='*60}")
    print(f"ファイル: {file_path}")
    print(f"{'='*60}\n")

    try:
        # 全シート名を取得
        excel_file = pd.ExcelFile(file_path)
        print(f"シート名: {excel_file.sheet_names}\n")

        # 各シートを分析
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- シート: {sheet_name} ---")
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            print(f"行数: {len(df)}")
            print(f"列数: {len(df.columns)}")
            print(f"\nカラム名:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i}. {col}")

            print(f"\n最初の3行のデータ:")
            print(df.head(3).to_string())

            print(f"\n基本統計:")
            print(df.describe().to_string())

    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    files = [
        "/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/8502_記事ネタ提案ツール/愛カツ数字確認シート.xlsx",
        "/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/8502_記事ネタ提案ツール/愛カツLINE配信シート(2025_6_16～.xlsx"
    ]

    for file_path in files:
        analyze_excel(file_path)
