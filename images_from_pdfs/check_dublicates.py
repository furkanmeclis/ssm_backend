import pandas as pd

# Load the Excel file
file_path = 'excel_tables/LYS.xlsx'  # Replace with your actual file path
df = pd.read_excel(file_path)

# Specify the columns to check for duplicates
columns_to_check = ['SINAV ADI', 'SINAV YILI', 'SORU NUMARASI', 'DERS ADI']

# Find the duplicates (only subsequent duplicates)
duplicates = df[df.duplicated(subset=columns_to_check)]

# Display all rows without truncation
pd.set_option('display.max_rows', None)

# Print only the columns you want to check
if not duplicates.empty:
    print("Duplicate rows found:")
    print(duplicates[columns_to_check])
else:
    print("No duplicate rows found.")
