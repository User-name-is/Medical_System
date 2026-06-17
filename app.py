from flask import Flask, render_template, request
import sqlite3
from datetime import date
import os

from rag import retrieve_knowledge
from llm import generate_response
from prompts import SYSTEM_PROMPT

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "個人醫療問診系統.db")


def search_department(user_input):
    symptom_alias = {
        "腰痛": ["腰痛", "腰好痛", "腰很痛", "腰痠", "腰酸", "腰不舒服", "腰怪怪的"],
        "肚子痛": ["肚子痛", "腹痛", "肚子好痛", "肚子不舒服", "肚子怪怪的", "肚子絞痛", "拉肚子"],
        "胃痛": ["胃痛", "胃好痛", "胃不舒服", "胃悶", "胃脹"],
        "腹瀉": ["腹瀉", "拉肚子", "一直拉", "烙賽", "水瀉"],
        "便秘": ["便秘", "大不出來", "排便困難", "好幾天沒大便"],
        "嘔吐": ["嘔吐", "想吐", "吐了", "噁心想吐"],
        "咳嗽": ["咳嗽", "一直咳", "咳不停", "乾咳", "咳很久"],
        "咳痰": ["咳痰", "有痰", "痰很多", "喉嚨有痰"],
        "呼吸困難": ["呼吸困難", "喘不過氣", "很喘", "呼吸不順", "吸不到氣"],
        "胸悶": ["胸悶", "胸口悶", "胸口壓迫", "胸口不舒服"],
        "胸痛": ["胸痛", "胸口痛", "胸口很痛", "心口痛"],
        "頭痛": ["頭痛", "頭好痛", "頭很痛", "偏頭痛", "頭脹"],
        "頭暈": ["頭暈", "暈眩", "頭昏", "天旋地轉", "站不穩"],
        "發燒": ["發燒", "燒起來", "體溫高", "高燒", "低燒"],
        "全身倦怠": ["全身倦怠", "很累", "沒力", "全身無力", "疲倦"],
        "紅疹": ["紅疹", "起疹子", "皮膚紅紅的", "身上長疹子"],
        "皮膚癢": ["皮膚癢", "身體很癢", "一直抓", "癢癢的"],
        "眼睛癢": ["眼睛癢", "眼睛好癢", "眼睛不舒服", "眼睛好酸", "眼壓好高", "眼壓高"],
        "視力模糊": ["視力模糊", "看不清楚", "眼睛霧霧的", "視線模糊"],
        "耳鳴": ["耳鳴", "耳朵嗡嗡叫", "耳朵有聲音"],
        "鼻塞": ["鼻塞", "鼻子塞住", "鼻子不通", "呼吸不順"],
        "流鼻血": ["流鼻血", "鼻血", "一直流鼻血"],
        "喉嚨疼痛": ["喉嚨疼痛", "喉嚨痛", "喉嚨不舒服", "吞口水會痛"],
        "吞嚥困難": ["吞嚥困難", "吞不下去", "吃東西卡卡", "吞東西痛"],
        "心悸": ["心悸", "心跳很快", "心跳亂跳", "心臟跳很大力"],
        "高血壓": ["高血壓", "血壓高", "血壓偏高"],
        "關節疼痛": ["關節疼痛", "關節痛", "膝蓋痛", "手腕痛"],
        "拉傷": ["拉傷", "肌肉拉傷", "運動拉傷", "肌肉好痛"],
        "扭傷": ["扭傷", "腳扭到", "手扭到", "扭到了"],
        "排尿疼痛": ["排尿疼痛", "尿尿痛", "小便痛", "尿道痛"],
        "頻尿": ["頻尿", "一直想尿尿", "一直跑廁所", "尿很多次"],
        "血尿": ["血尿", "尿尿有血", "尿液紅紅的"],
        "經期不正常": ["經期不正常", "月經不順", "生理期不順", "經期亂掉"],
        "經痛": ["經痛", "生理痛", "月經痛", "肚子經痛"],
        "失眠": ["失眠", "睡不著", "很難睡", "一直醒來"],
        "入睡困難": ["入睡困難", "躺很久睡不著", "難入睡"],
        "記憶力明顯衰退": ["記憶力明顯衰退", "記憶力變差", "常常忘記事情", "記性變差"],
        "失智": ["失智", "疑似失智", "認不得人", "忘東忘西"],
        "情緒低落": ["長期情緒低落", "心情不好", "很憂鬱", "提不起勁"],
        "焦慮": ["莫名焦慮緊張", "焦慮", "很緊張", "恐慌"],
        "針灸治療": ["針灸"]
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT symptom_id, symptom_name FROM Symptom")
    symptoms = cursor.fetchall()

    matched_symptoms = []

    for symptom_id, symptom_name in symptoms:
        if symptom_name in user_input:
            if (symptom_id, symptom_name) not in matched_symptoms:
                matched_symptoms.append((symptom_id, symptom_name))
            continue

        if symptom_name in symptom_alias:
            for alias in symptom_alias[symptom_name]:
                if alias in user_input:
                    if (symptom_id, symptom_name) not in matched_symptoms:
                        matched_symptoms.append((symptom_id, symptom_name))
                    break

    if len(matched_symptoms) == 0:
        conn.close()
        return None

    found_symptoms = []
    all_results = []

    for symptom_id, symptom_name in matched_symptoms:
        if symptom_name not in found_symptoms:
            found_symptoms.append(symptom_name)

        cursor.execute("""
            SELECT Department.department_name,
                   Department.description
            FROM Department
            JOIN Department_Symptom
            ON Department.department_id = Department_Symptom.department_id
            WHERE Department_Symptom.symptom_id = ?
        """, (symptom_id,))

        rows = cursor.fetchall()

        for department_name, description in rows:
            if (department_name, description) not in all_results:
                all_results.append((department_name, description))

            cursor.execute("""
                INSERT INTO Consultation_Record
                (
                    record_date,
                    user_input,
                    symptom_name,
                    department_name,
                    department_description
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(date.today()),
                user_input,
                symptom_name,
                department_name,
                description
            ))

    conn.commit()
    conn.close()

    return found_symptoms, all_results


def get_records(search_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if search_date:
        cursor.execute("""
            SELECT record_date, symptom_name, department_name, department_description
            FROM Consultation_Record
            WHERE record_date = ?
            ORDER BY record_id DESC
        """, (search_date,))
    else:
        cursor.execute("""
            SELECT record_date, symptom_name, department_name, department_description
            FROM Consultation_Record
            ORDER BY record_id DESC
        """)

    records = cursor.fetchall()
    conn.close()
    return records


@app.route("/", methods=["GET", "POST"])
def index():
    user_input = ""
    result = None
    ai_response = None

    search_date = request.args.get("search_date")
    records = get_records(search_date)

    if request.method == "POST":
        user_input = request.form["user_input"]
        result = search_department(user_input)

        if result:
            try:
                knowledge = retrieve_knowledge(user_input)

                symptoms_text = "、".join(result[0])
                departments_text = "、".join(
                    [department_name for department_name, description in result[1]]
                )

                prompt = f"""
{SYSTEM_PROMPT}

使用者症狀：
{user_input}

系統辨識到的症狀：
{symptoms_text}

相關醫療知識：
{knowledge}

建議科別：
{departments_text}

請用聊天機器人的口吻，生成一段簡短、清楚、適合一般民眾閱讀的醫療資訊輔助回覆。

回答請包含：
1. 對使用者症狀的簡短理解
2. 建議科別
3. 健康提醒
4. 醫療安全提醒

請注意：
不可做疾病診斷。
不可保證疾病結果。
不可開藥。
不要用資料庫欄位格式回答。
"""

                ai_response = generate_response(prompt)

            except Exception as e:
                print("AI 產生錯誤：", e)
                ai_response = "目前 AI 回覆暫時無法產生，但上方已提供初步科別建議。"

        records = get_records(search_date)

    return render_template(
        "index.html",
        user_input=user_input,
        result=result,
        ai_response=ai_response,
        records=records,
        search_date=search_date,
        emergency_response=None,
        emergency_input=""
    )


@app.route("/emergency", methods=["POST"])
def emergency():
    emergency_input = request.form["emergency_input"]

    prompt = f"""
{SYSTEM_PROMPT}

你是一位醫療風險分級助理。

請根據使用者描述，將風險分成：

綠色：可先觀察
黃色：建議盡快門診就醫
紅色：建議立即急診或撥打119

使用者描述：
{emergency_input}

請用繁體中文回答，格式包含：
1. 風險等級
2. 判斷原因
3. 建議行動
4. 醫療安全提醒

注意：
不可診斷疾病。
不可開藥。
不可保證疾病結果。
"""

    try:
        emergency_response = generate_response(prompt)

    except Exception as e:
        print("緊急評估錯誤：", e)
        emergency_response = "目前 AI 緊急評估暫時無法產生。若有嚴重不適，請立即就醫或撥打 119。"

    records = get_records()

    return render_template(
        "index.html",
        user_input="",
        result=None,
        ai_response=None,
        records=records,
        search_date=None,
        emergency_response=emergency_response,
        emergency_input=emergency_input
    )


if __name__ == "__main__":
    app.run(debug=True)