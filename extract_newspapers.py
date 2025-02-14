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
    lines = text.split('\n')
    
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
    
    header_pattern = r'(.*?)/(\d{4})年(\d{1,2})月(\d{1,2})日/第(\d+)版'
    
    for line in lines[:10]:
        match = re.search(header_pattern, line)
        if match:
            info['publisher'] = match.group(1)
            info['year'] = int(match.group(2))
            info['month'] = int(match.group(3))
            info['day'] = int(match.group(4))
            info['volume'] = match.group(5)
            break
    
    for i, line in enumerate(lines):
        if '行业/人口' in line and i + 2 < len(lines):
            info['title'] = lines[i + 2].strip()
            break
    
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