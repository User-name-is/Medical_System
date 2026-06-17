import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "data", "medical_knowledge.txt")


def retrieve_knowledge(user_input):
    if not os.path.exists(KNOWLEDGE_PATH):
        return "目前尚未建立醫療知識庫。"

    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as file:
        knowledge = file.read()

    keywords = [
        "頭痛", "發燒", "咳嗽", "腹瀉", "肚子痛", "胃痛",
        "腰痛", "胸痛", "胸悶", "鼻塞", "喉嚨痛",
        "眼睛癢", "失眠", "焦慮", "頻尿", "經痛"
    ]

    matched_text = []

    for keyword in keywords:
        if keyword in user_input and keyword in knowledge:
            start = knowledge.find(keyword)
            end = knowledge.find("\n\n", start)

            if end == -1:
                end = len(knowledge)

            matched_text.append(knowledge[start:end])

    if matched_text:
        return "\n\n".join(matched_text)

    return knowledge[:800]