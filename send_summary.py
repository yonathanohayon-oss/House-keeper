#!/usr/bin/env python3
"""
send_summary.py  –  סיכום יומי למשפחה
שולח הודעה מעוצבת בעברית לטלגרם עם כל המשימות הממתינות מ-Supabase.

משתני סביבה נדרשים:
  SUPABASE_URL          – כתובת פרויקט Supabase
  SUPABASE_KEY          – מפתח שירות (service role key)
  TELEGRAM_BOT_TOKEN    – טוקן הבוט מ-BotFather
  TELEGRAM_CHAT_ID      – מזהה הצ'אט / הקבוצה
"""

import os
import sys
import logging
import requests
from datetime import date
from supabase import create_client, Client

# ── לוגינג ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── הגדרות ───────────────────────────────────────────────────────────────────
SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_KEY       = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# תרגומים
PRIORITY_HE = {"High": "גבוהה 🔴", "Medium": "בינונית 🟡", "Low": "נמוכה 🟢"}
CAT_HE      = {"Cleaning": "🧹 ניקיון", "Shopping": "🛒 קניות",
                "Finance": "💰 כספים",  "Kids":     "👶 ילדים"}
REC_HE      = {"Weekly": "שבועי 🔁", "Monthly": "חודשי 🔁", "None": ""}

DAYS_HE = {
    "Sunday":    "יום ראשון",
    "Monday":    "יום שני",
    "Tuesday":   "יום שלישי",
    "Wednesday": "יום רביעי",
    "Thursday":  "יום חמישי",
    "Friday":    "יום שישי",
    "Saturday":  "שבת",
}
MONTHS_HE = {
    1:"ינואר",2:"פברואר",3:"מרץ",4:"אפריל",5:"מאי",6:"יוני",
    7:"יולי",8:"אוגוסט",9:"ספטמבר",10:"אוקטובר",11:"נובמבר",12:"דצמבר"
}

def hebrew_date(d: date) -> str:
    day_name = DAYS_HE[d.strftime("%A")]
    return f"{day_name}, {d.day} ב{MONTHS_HE[d.month]} {d.year}"

# ── Supabase ──────────────────────────────────────────────────────────────────
def get_supabase() -> Client:
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        log.info("התחברות ל-Supabase הצליחה.")
        return client
    except Exception as exc:
        log.error("שגיאה בהתחברות ל-Supabase: %s", exc)
        sys.exit(1)


def fetch_pending(sb: Client) -> list[dict]:
    try:
        result = (
            sb.table("tasks")
            .select("*")
            .eq("status", "Pending")
            .order("priority")
            .execute()
        )
        tasks = result.data or []
        log.info("נמצאו %d משימות ממתינות.", len(tasks))
        return tasks
    except Exception as exc:
        log.error("שגיאה בשליפת משימות: %s", exc)
        sys.exit(1)


# ── בניית ההודעה ─────────────────────────────────────────────────────────────
def build_message(tasks: list[dict]) -> str:
    today     = date.today()
    overdue   = [t for t in tasks if t.get("due_date") and t["due_date"] < today.isoformat()]
    due_today = [t for t in tasks if t.get("due_date") == today.isoformat()]

    # ספירת נקודות שהושלמו (בונוס: ניתן להרחיב)
    lines = [
        "🏠 *בית חכם – סיכום יומי*",
        f"📅 {hebrew_date(today)}",
        "",
        "📊 *סקירה כללית*",
        f"• סה\"כ ממתינות: *{len(tasks)}*",
        f"• באיחור: *{len(overdue)}*  {'⚠️' if overdue else '✅'}",
        f"• לביצוע היום: *{len(due_today)}*",
    ]

    # ── משימות באיחור ────────────────────────────────────────────────────────
    if overdue:
        lines += ["", "⚠️ *משימות באיחור*"]
        for t in sorted(overdue, key=lambda x: x.get("due_date", "")):
            cat  = CAT_HE.get(t.get("category", ""), "📌")
            pri  = PRIORITY_HE.get(t.get("priority", ""), "")
            lines.append(
                f"  {cat} *{t['title']}* | {t.get('assigned_to','?')} | יעד: {t.get('due_date','')} | {pri}"
            )

    # ── ליום זה ──────────────────────────────────────────────────────────────
    if due_today:
        lines += ["", "📌 *לביצוע היום*"]
        for t in due_today:
            cat = CAT_HE.get(t.get("category", ""), "📌")
            lines.append(f"  {cat} *{t['title']}* | {t.get('assigned_to','?')}")

    # ── לפי משתמש ────────────────────────────────────────────────────────────
    user_labels = {"Ina": "👩 *אינה*", "User": "👤 *משתמש*"}
    for user, label in user_labels.items():
        user_tasks = [t for t in tasks if t.get("assigned_to") == user]
        if not user_tasks:
            continue
        lines += ["", f"{label} ({len(user_tasks)} משימות)"]
        for priority in ("High", "Medium", "Low"):
            bucket = [t for t in user_tasks if t.get("priority") == priority]
            for t in bucket:
                cat = CAT_HE.get(t.get("category", ""), "📌")
                pri = PRIORITY_HE.get(priority, "")
                due = f" | 📅 {t['due_date']}" if t.get("due_date") else ""
                rec = f" | {REC_HE[t['recurrence']]}" if t.get("recurrence", "None") != "None" else ""
                pts = f" | ⭐{t['points']} נק'" if t.get("points") else ""
                lines.append(f"  {cat} {t['title']}{pts}{due}{rec} | {pri}")

    # ── לפי קטגוריה ──────────────────────────────────────────────────────────
    lines += ["", "📂 *לפי קטגוריה*"]
    cat_counts: dict[str, int] = {}
    for t in tasks:
        cat_counts[t.get("category", "אחר")] = cat_counts.get(t.get("category", "אחר"), 0) + 1
    for cat_db, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        cat_display = CAT_HE.get(cat_db, cat_db)
        lines.append(f"  {cat_display}: {cnt}")

    lines += ["", "─────────────────────"]
    lines.append("_נוצר אוטומטית על ידי בית חכם 🤖_")

    return "\n".join(lines)


# ── שליחה לטלגרם ─────────────────────────────────────────────────────────────
def send_telegram(message: str) -> None:
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(TELEGRAM_API, json=payload, timeout=15)
        resp.raise_for_status()
        log.info("ההודעה נשלחה בהצלחה (סטטוס %s).", resp.status_code)
    except requests.exceptions.ConnectionError as exc:
        log.error("שגיאת רשת בשליחה לטלגרם: %s", exc)
        sys.exit(1)
    except requests.exceptions.Timeout:
        log.error("פג תוקף הזמן לטלגרם.")
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        log.error("שגיאת HTTP מטלגרם %s: %s", exc.response.status_code, exc.response.text)
        sys.exit(1)
    except Exception as exc:
        log.error("שגיאה לא צפויה: %s", exc)
        sys.exit(1)


# ── ראשי ─────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("=== בית חכם – סיכום יומי ===")
    sb    = get_supabase()
    tasks = fetch_pending(sb)

    if not tasks:
        message = (
            "🏠 *בית חכם – סיכום יומי*\n"
            f"📅 {hebrew_date(date.today())}\n\n"
            "✅ אין משימות ממתינות\\! תהנו מהיום\\! 🎉"
        )
    else:
        message = build_message(tasks)

    send_telegram(message)
    log.info("סיום.")


if __name__ == "__main__":
    main()
