import sqlite3
from datetime import date

db_path = "個人醫療問診系統.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

user_input = input("請輸入您的症狀：")

cursor.execute("SELECT symptom_id, symptom_name FROM Symptom")
symptoms = cursor.fetchall()

matched_symptom = None

for symptom_id, symptom_name in symptoms:
    if symptom_name in user_input:
        matched_symptom = (symptom_id, symptom_name)
        break

if matched_symptom is None:
    print("找不到對應症狀，建議尋求專業醫療協助。")
else:
    symptom_id, symptom_name = matched_symptom

    cursor.execute("""
        SELECT Department.department_name, Department.description
        FROM Department
        JOIN Department_Symptom
        ON Department.department_id = Department_Symptom.department_id
        WHERE Department_Symptom.symptom_id = ?
    """, (symptom_id,))

    results = cursor.fetchall()

    print("\n========== 問診結果 ==========")
    print(f"偵測到症狀：{symptom_name}")

    for department_name, description in results:
        print(f"\n建議科別：{department_name}")
        print(f"科別說明：{description}")

        cursor.execute("""
            INSERT INTO Consultation_Record
            (record_date, user_input, symptom_name, department_name, department_description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(date.today()),
            user_input,
            symptom_name,
            department_name,
            description
        ))

    conn.commit()
    print("\n已儲存本次問診紀錄。")

conn.close()