import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import os

# ── הגדרות עמוד ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🏠 בית חכם",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── עיצוב CSS עם תמיכה מלאה ב-RTL ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&display=swap');

/* RTL גלובלי */
* {
    font-family: 'Heebo', sans-serif !important;
    direction: rtl;
    text-align: right;
}

/* רקע */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* תיקוני Streamlit ל-RTL */
div[data-testid="stHorizontalBlock"] { direction: rtl; }
div[data-testid="column"] { direction: rtl; }
.stSelectbox > div, .stTextInput > div, .stTextArea > div { direction: rtl; }
div[data-testid="stMarkdownContainer"] { direction: rtl; text-align: right; }
label { direction: rtl !important; text-align: right !important; }

/* כרטיסי משימות */
.task-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 10px;
    backdrop-filter: blur(8px);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    direction: rtl;
    text-align: right;
}
.task-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}

/* תגיות עדיפות */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
}
.badge-high   { background:#ff4d6d22; color:#ff4d6d; border:1px solid #ff4d6d55; }
.badge-medium { background:#ffd16622; color:#ffd166; border:1px solid #ffd16655; }
.badge-low    { background:#06d6a022; color:#06d6a0; border:1px solid #06d6a055; }

/* צ'יפ נקודות */
.points-chip {
    display: inline-block;
    background: linear-gradient(90deg,#7b2ff7,#f107a3);
    color: #fff;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-right: 8px;
}

/* כרטיסי מדדים */
.metric-card {
    background: rgba(255,255,255,0.06);
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.1);
    padding: 20px;
    text-align: center;
    direction: rtl;
}
.metric-val {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg,#a78bfa,#f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label { color:#a0a0c0; font-size:0.82rem; margin-top:4px; }

/* כותרות */
h2, h3 { color: #e8e8ff !important; direction: rtl; text-align: right; }

/* ווידג'טים של Streamlit */
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stDateInput"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextArea"] label {
    color: #c0c0e0 !important;
    font-size: 0.88rem;
    direction: rtl;
    text-align: right;
}
div[data-testid="stButton"] button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Heebo', sans-serif !important;
}

/* רשימת משימות עם גלילה */
.task-list { max-height: 600px; overflow-y: auto; padding-left: 4px; }

/* שורת מטא-נתונים בכרטיס */
.task-meta {
    color: #8080a0;
    font-size: 0.8rem;
    margin-top: 6px;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    direction: rtl;
    justify-content: flex-start;
}

/* מובייל */
@media (max-width: 640px) {
    .metric-val { font-size: 1.8rem; }
    .task-card  { padding: 12px 14px; }
}
</style>
""", unsafe_allow_html=True)

# ── התחברות ל-Supabase ────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")
    if not url or not key:
        st.error("⚠️ חסרים פרטי התחברות ל-Supabase. הוסיפי SUPABASE_URL ו-SUPABASE_KEY ב-Secrets.")
        st.stop()
    return create_client(url, key)

supabase = get_supabase()

# ── קבועים ───────────────────────────────────────────────────────────────────
# ערכי DB נשמרים באנגלית – תצוגה בעברית
CATEGORIES_DB  = ["Cleaning", "Shopping", "Finance", "Kids"]
CATEGORIES_HE  = {"Cleaning": "ניקיון", "Shopping": "קניות", "Finance": "כספים", "Kids": "ילדים"}
CATEGORIES_HE_R = {v: k for k, v in CATEGORIES_HE.items()}  # היפוך: עברית → DB

PRIORITIES_DB = ["High", "Medium", "Low"]
PRIORITIES_HE = {"High": "גבוהה", "Medium": "בינונית", "Low": "נמוכה"}
PRIORITIES_HE_R = {v: k for k, v in PRIORITIES_HE.items()}

USERS = ["Ina", "User"]

RECURRENCES_DB = ["None", "Weekly", "Monthly"]
RECURRENCES_HE = {"None": "ללא", "Weekly": "שבועי", "Monthly": "חודשי"}
RECURRENCES_HE_R = {v: k for k, v in RECURRENCES_HE.items()}

STATUS_DB = ["Pending", "Done"]
STATUS_HE = {"Pending": "ממתין", "Done": "הושלם", "All": "הכל"}

CAT_ICONS  = {"Cleaning": "🧹", "Shopping": "🛒", "Finance": "💰", "Kids": "👶"}
PRI_COLORS = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}
PRI_EMOJI  = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

# ── פונקציות נתונים ───────────────────────────────────────────────────────────
def load_tasks(status_filter=None):
    q = supabase.table("tasks").select("*").order("created_at", desc=True)
    if status_filter and status_filter != "All":
        q = q.eq("status", status_filter)
    return q.execute().data or []

def load_points():
    rows = supabase.table("tasks").select("assigned_to, points").eq("status", "Done").execute().data or []
    totals = {u: 0 for u in USERS}
    for r in rows:
        if r["assigned_to"] in totals:
            totals[r["assigned_to"]] += r.get("points", 0) or 0
    return totals

def complete_task(task_id):
    supabase.table("tasks").update({
        "status": "Done",
        "completed_at": datetime.utcnow().isoformat()
    }).eq("id", task_id).execute()

    task = supabase.table("tasks").select("*").eq("id", task_id).single().execute().data
    if task and task.get("recurrence") in ("Weekly", "Monthly"):
        due = date.fromisoformat(task["due_date"]) if task.get("due_date") else date.today()
        new_due = due + (timedelta(weeks=1) if task["recurrence"] == "Weekly" else timedelta(days=30))
        supabase.table("tasks").insert({
            "title":       task["title"],
            "category":    task["category"],
            "priority":    task["priority"],
            "assigned_to": task["assigned_to"],
            "status":      "Pending",
            "points":      task["points"],
            "recurrence":  task["recurrence"],
            "due_date":    new_due.isoformat(),
            "notes":       task.get("notes", ""),
        }).execute()

def add_task(title, category_db, priority_db, assigned_to, due_date, recurrence_db, points, notes):
    supabase.table("tasks").insert({
        "title":       title,
        "category":    category_db,
        "priority":    priority_db,
        "assigned_to": assigned_to,
        "status":      "Pending",
        "points":      points,
        "recurrence":  recurrence_db,
        "due_date":    due_date.isoformat() if due_date else None,
        "notes":       notes,
    }).execute()

def delete_task(task_id):
    supabase.table("tasks").delete().eq("id", task_id).execute()

# ── כותרת ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:28px 0 16px; direction:rtl;">
  <div style="font-size:2.8rem; font-weight:800;
    background:linear-gradient(90deg,#a78bfa,#f472b6,#fb923c);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
    🏠 בית חכם
  </div>
  <div style="color:#7070a0; font-size:0.95rem; margin-top:6px;">
    מרכז ניהול משק הבית המשפחתי
  </div>
</div>
""", unsafe_allow_html=True)

# ── טעינת נתונים ──────────────────────────────────────────────────────────────
pts       = load_points()
all_tasks = load_tasks()
pending   = [t for t in all_tasks if t["status"] == "Pending"]
done_today = [t for t in all_tasks
              if t["status"] == "Done"
              and (t.get("completed_at") or "")[:10] == date.today().isoformat()]

# ── לוח מדדים ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val">⭐ {pts.get('Ina', 0)}</div>
        <div class="metric-label">נקודות של אינה</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val">⭐ {pts.get('User', 0)}</div>
        <div class="metric-label">נקודות של משתמש</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val">{len(pending)}</div>
        <div class="metric-label">משימות ממתינות</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val">{len(done_today)}</div>
        <div class="metric-label">הושלמו היום</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── פריסה ראשית: רשימה | טופס ────────────────────────────────────────────────
left, right = st.columns([2, 1], gap="large")

# ════════════════════════════════════════════════════════
# עמודה שמאל – רשימת משימות
# ════════════════════════════════════════════════════════
with left:
    st.markdown("### 📋 רשימת משימות")

    f1, f2, f3 = st.columns(3)
    with f1:
        sel_cat_he = st.selectbox(
            "קטגוריה",
            ["הכל"] + [CATEGORIES_HE[c] for c in CATEGORIES_DB],
            key="fcat"
        )
    with f2:
        sel_user = st.selectbox("מוקצה ל", ["הכל"] + USERS, key="fusr")
    with f3:
        sel_status_he = st.selectbox("סטטוס", ["ממתין", "הושלם", "הכל"], key="fsts")

    # המרה חזרה ל-DB
    status_db_map = {"ממתין": "Pending", "הושלם": "Done", "הכל": None}
    tasks = load_tasks(status_db_map[sel_status_he])

    if sel_cat_he != "הכל":
        cat_db_filter = CATEGORIES_HE_R[sel_cat_he]
        tasks = [t for t in tasks if t["category"] == cat_db_filter]
    if sel_user != "הכל":
        tasks = [t for t in tasks if t["assigned_to"] == sel_user]

    # מיון: גבוהה → בינונית → נמוכה
    pri_order = {"High": 0, "Medium": 1, "Low": 2}
    tasks.sort(key=lambda t: (
        pri_order.get(t.get("priority", "Low"), 2),
        t.get("due_date") or "9999"
    ))

    if not tasks:
        st.info("✨ אין משימות להצגה בפילטרים הנבחרים.")
    else:
        st.markdown('<div class="task-list">', unsafe_allow_html=True)
        for task in tasks:
            icon      = CAT_ICONS.get(task["category"], "📌")
            badge_cls = PRI_COLORS.get(task["priority"], "badge-low")
            pri_he    = PRIORITIES_HE.get(task["priority"], task["priority"])
            cat_he    = CATEGORIES_HE.get(task["category"], task["category"])
            rec_he    = RECURRENCES_HE.get(task.get("recurrence", "None"), "")
            due_str   = f"📅 {task['due_date']}" if task.get("due_date") else ""
            rec_str   = f"🔁 {rec_he}" if task.get("recurrence", "None") != "None" else ""
            pts_str   = f'<span class="points-chip">+{task["points"]} נק׳</span>' if task.get("points") else ""
            notes_str = (f'<div style="color:#7070a0;font-size:0.8rem;margin-top:6px;direction:rtl;">'
                         f'💬 {task["notes"]}</div>') if task.get("notes") else ""
            done_tick = "✅ " if task["status"] == "Done" else ""

            # בדיקת פיגור
            is_overdue = (task["status"] == "Pending"
                          and task.get("due_date")
                          and task["due_date"] < date.today().isoformat())
            overdue_style = "border-color:#ff4d6d88;" if is_overdue else ""
            overdue_label = '<span style="color:#ff4d6d;font-size:0.75rem;font-weight:700;">⚠️ באיחור</span>' if is_overdue else ""

            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
                <div class="task-card" style="{overdue_style}">
                  <div style="display:flex;align-items:center;justify-content:space-between;
                              flex-wrap:wrap;gap:6px;direction:rtl;">
                    <div style="font-weight:600;color:#e0e0ff;font-size:1rem;direction:rtl;">
                      {done_tick}{icon} {task['title']} {pts_str} {overdue_label}
                    </div>
                    <span class="badge {badge_cls}">{pri_he}</span>
                  </div>
                  <div class="task-meta">
                    <span>👤 {task['assigned_to']}</span>
                    <span>🏷 {cat_he}</span>
                    {f'<span>{due_str}</span>' if due_str else ''}
                    {f'<span>{rec_str}</span>' if rec_str else ''}
                  </div>
                  {notes_str}
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if task["status"] == "Pending":
                    if st.button("✔", key=f"done_{task['id']}", help="סמן כהושלם"):
                        complete_task(task["id"])
                        st.rerun()
                if st.button("🗑", key=f"del_{task['id']}", help="מחק"):
                    delete_task(task["id"])
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# עמודה ימין – הוספת משימה
# ════════════════════════════════════════════════════════
with right:
    st.markdown("### ➕ משימה חדשה")
    with st.container():
        title = st.text_input("שם המשימה *", placeholder="לדוגמה: לנקות את המטבח")

        col_a, col_b = st.columns(2)
        with col_a:
            cat_he_sel = st.selectbox("קטגוריה", [CATEGORIES_HE[c] for c in CATEGORIES_DB], key="ncat")
            pri_he_sel = st.selectbox("עדיפות",   [PRIORITIES_HE[p] for p in PRIORITIES_DB],  key="npri")
        with col_b:
            assigned    = st.selectbox("מוקצה ל",    USERS,                                       key="nusr")
            rec_he_sel  = st.selectbox("חזרה",       [RECURRENCES_HE[r] for r in RECURRENCES_DB], key="nrec")

        due_date = st.date_input("תאריך יעד", value=None, min_value=date.today())
        points   = st.slider("נקודות", 1, 20, 5)
        notes    = st.text_area("הערות (אופציונלי)", height=80, placeholder="פרטים נוספים...")

        if st.button("🚀 הוסף משימה", use_container_width=True, type="primary"):
            if not title.strip():
                st.warning("שם המשימה הוא שדה חובה.")
            else:
                add_task(
                    title.strip(),
                    CATEGORIES_HE_R[cat_he_sel],
                    PRIORITIES_HE_R[pri_he_sel],
                    assigned,
                    due_date,
                    RECURRENCES_HE_R[rec_he_sel],
                    points,
                    notes.strip(),
                )
                st.success(f"✅ המשימה '{title}' נוספה בהצלחה!")
                st.rerun()

    # ── סטטיסטיקה לפי קטגוריה ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 ממתינות לפי קטגוריה")
    cat_counts = {c: sum(1 for t in pending if t["category"] == c) for c in CATEGORIES_DB}
    for cat_db, count in cat_counts.items():
        pct = int(count / max(len(pending), 1) * 100)
        cat_he = CATEGORIES_HE[cat_db]
        st.markdown(f"""
        <div style="margin-bottom:10px;direction:rtl;">
          <div style="display:flex;justify-content:space-between;
                      color:#c0c0e0;font-size:0.85rem;direction:rtl;">
            <span>{CAT_ICONS[cat_db]} {cat_he}</span><span>{count}</span>
          </div>
          <div style="background:rgba(255,255,255,0.08);border-radius:6px;
                      height:6px;margin-top:4px;">
            <div style="background:linear-gradient(90deg,#a78bfa,#f472b6);
                        width:{pct}%;height:6px;border-radius:6px;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── כותרת תחתית ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#404060;font-size:0.75rem;
            padding:24px 0 8px;direction:rtl;">
  בית חכם 🏠 • סיכום יומי נשלח בשעה 08:00 🇮🇱
</div>
""", unsafe_allow_html=True)
