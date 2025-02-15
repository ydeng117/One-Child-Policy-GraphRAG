import os
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import pandas as pd
import re
import argparse
from tqdm import tqdm  # For progress bar

def extract_newspaper_info(pdf_path):
    """
    Extract information from Chinese newspaper PDF files.
    Returns a dictionary with publisher, date info, title and text content.
    """
    laparams = LAParams(
        line_margin=0.5,
        word_margin=0.1,
        char_margin=2.0,
        boxes_flow=0.5,
        detect_vertical=True
    )
    
    text = extract_text(pdf_path, laparams=laparams)
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    
    info = {
        'filename': os.path.basename(pdf_path),
        'publisher': None,
        'year': None,
        'month': None,
        'day': None,
        'volume': None,
        'title': None,
        'text': text
    }
    
    if paragraphs:
        # 第一段通常是header信息
        header = paragraphs[0].strip()
        print(f"Debug - Header content: {header}")  # 调试信息
        
        # 尝试不同的分隔符
        header_parts = []
        if '/' in header:
            header_parts = [part.strip() for part in header.split('/') if part.strip()]
        else:
            header_parts = [part.strip() for part in re.split(r'[/\s]+', header) if part.strip()]
        
        print(f"Debug - Header parts: {header_parts}")  # 调试信息
        
        if header_parts:
            # 提取出版商
            info['publisher'] = header_parts[0]
            
            # 遍历所有部分来查找年月日和版次
            for part in header_parts:
                # 查找年份
                year_match = re.search(r'(\d+) 年', part)
                if year_match:
                    info['year'] = int(year_match.group(1))
                
                # 查找月份
                month_match = re.search(r'(\d+) 月', part)
                if month_match:
                    info['month'] = int(month_match.group(1))
                
                # 查找日期
                day_match = re.search(r'(\d+) 日', part)
                if day_match:
                    info['day'] = int(day_match.group(1))
                
                # 查找版次
                volume_match = re.search(r'第 (\d+) 版', part)
                if volume_match:
                    info['volume'] = volume_match.group(1)
        
        # 如果有第二段，可能是标题
        if len(paragraphs) > 1:
            info['title'] = paragraphs[1].strip()
        
        # 从第三段开始是正文
        if len(paragraphs) > 2:
            info['text'] = '\n'.join(paragraphs[2:])
    
    # 打印提取的信息用于调试
    print(f"Debug - Extracted info: {info}")
    
    return info

def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Extract information from Chinese newspaper PDFs')
    parser.add_argument('input_path', help='Path to folder containing PDF files')
    parser.add_argument('--output', '-o', help='Output CSV file path (default: newspaper_data.csv)',
                      default='newspaper_data.csv')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print detailed progress')
    
    args = parser.parse_args()
    
    # Verify input path exists
    if not os.path.exists(args.input_path):
        print(f"Error: Input path '{args.input_path}' does not exist")
        return
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(args.input_path) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in {args.input_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    all_data = []
    errors = []
    
    # Process files with progress bar
    for filename in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(args.input_path, filename)
        try:
            if args.verbose:
                print(f"\nProcessing: {filename}")
            info = extract_newspaper_info(pdf_path)
            all_data.append(info)
            if args.verbose:
                print(f"Successfully processed: {filename}")
        except Exception as e:
            errors.append((filename, str(e)))
            if args.verbose:
                print(f"Error processing {filename}: {str(e)}")
    
    # Create DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        column_order = ['filename', 'title', 'publisher', 'year', 'month', 'day', 'volume', 'text']
        df = df[column_order]
        
        # Save to CSV
        df.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"\nExtraction complete! Data saved to: {args.output}")
        
        # Display summary
        print(f"\nSummary:")
        print(f"Total files processed: {len(all_data)}")
        print(f"Successfully processed: {len(all_data)}")
        print(f"Errors encountered: {len(errors)}")
        print(f"Unique publishers: {df['publisher'].nunique()}")
        if len(all_data) > 0:
            print(f"Date range: {df['year'].min()}-{df['month'].min()} to {df['year'].max()}-{df['month'].max()}")
    
    # Print errors if any
    if errors:
        print("\nErrors encountered:")
        for filename, error in errors:
            print(f"- {filename}: {error}")

if __name__ == "__main__":
    main()