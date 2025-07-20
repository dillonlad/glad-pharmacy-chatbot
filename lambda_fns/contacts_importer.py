import os
import pandas as pd
import mysql.connector

# CONFIGURATION
EXCEL_PATH = "C:\\Users\\Dillon\\OneDrive\\Documents\\Patient list.xlsx"  # Update this
DB_CONFIG = {
    'host': '',
    'user': '',
    'password': '',
    'database': '',
    'port': 3306,
}

def format_phone_number(raw):
    if pd.isna(raw) or str(raw).lower() == 'x':
        return None
    raw = str(raw).strip()
    if raw.startswith('1') or raw == '':
        return None
    return '44' + raw

def phone_exists(cursor, phone_number):
    query = "SELECT 1 FROM conversations WHERE phone_number = %s LIMIT 1"
    cursor.execute(query, (phone_number,))
    return cursor.fetchone() is not None

def main():
    # Read the Excel file skipping the first row (empty)
    df = pd.read_excel(EXCEL_PATH, header=None, skiprows=1)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        surname = str(row[0]).strip() if not pd.isna(row[0]) else ''
        firstname = str(row[1]).strip() if not pd.isna(row[1]) else ''
        middlename = str(row[2]).strip() if not pd.isna(row[2]) else ''
        dob = str(row[3]).strip() if not pd.isna(row[3]) else ''
        phone1_raw = row[4]
        phone2_raw = row[5]
        email = str(row[6]).strip() if not pd.isna(row[6]) else ''

        phone1 = format_phone_number(phone1_raw)
        phone2 = format_phone_number(phone2_raw)

        chosen_phone = None

        if phone1 and not phone_exists(cursor, phone1):
            chosen_phone = phone1
        elif phone2 and not phone_exists(cursor, phone2):
            chosen_phone = phone2
        else:
            print("Skipping")
            continue  # Skip row if both phones are invalid or exist

        profile_name = f"{firstname} {surname}".strip()
        display_name = f"{firstname} {surname} {dob}".strip()

        insert_query = """
        INSERT INTO conversations (phone_number, profile_name, display_name, preference, active)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (chosen_phone, profile_name, display_name, 2, 1))
        conn.commit()

    cursor.close()
    conn.close()
    print("Import complete.")

if __name__ == "__main__":
    main()
