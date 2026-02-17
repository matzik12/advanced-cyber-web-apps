# 1. שימוש בגרסת פייתון עדכנית ויציבה
FROM python:3.10-slim

# 2. התקנת חבילות מערכת בסיסיות (דרושות לעיתים לספריות כמו giskard או pandas)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# 3. הגדרת תיקיית העבודה
WORKDIR /app

# 4. העתקת קובץ הדרישות תחילה (לניצול יעיל של Cache)
COPY requirements.txt .

# 5. התקנת הספריות
# אנחנו משדרגים את pip ומתקינים את הכל
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. העתקת שאר קוד המקור (כולל main.py ו-giskard_wrapper.py)
COPY . .

# 7. יצירת תיקיית דוחות פנימית
RUN mkdir -p /reports

# 8. חשיפת הפורט של FastAPI
EXPOSE 8000

# 9. פקודת ההרצה
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]