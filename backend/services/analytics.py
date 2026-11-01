"""One classroom-scoped read model for all recorded reading engines."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from database.schema import get_db_connection


def students_for(user):
    with get_db_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM students WHERE archived=0 AND classroom_id=? AND (?='teacher' OR id=?) ORDER BY name",
            (user["classroom_id"], user["role"], user.get("student_id"))).fetchall()]


def attempts_for(user, student_id=None):
    """Accuracy is always 0–100; simulated and archived records are excluded."""
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT a.* FROM (
                SELECT s.id, s.student_id, s.target_sentence, s.transcript,
                       s.accuracy*100 AS accuracy, s.wpm, 0 AS stars,
                       CASE WHEN s.accuracy>=0.7 THEN 1 ELSE 0 END AS passed,
                       s.timestamp AS created_at, s.language, 'classic' AS engine,
                       s.words_json, NULL AS story_id, NULL AS checkpoint_id
                FROM sessions s WHERE s.is_mock=0
                UNION ALL
                SELECT ss.id, ss.student_id, cr.target_text, cr.transcript, cr.accuracy,
                       cr.wpm, cr.stars, cr.passed, cr.created_at, ss.language, 'checkpoint',
                       cr.words_json, ss.story_id, cr.checkpoint_id
                FROM checkpoint_results cr JOIN story_sessions ss ON ss.id=cr.session_id WHERE ss.is_mock=0
                UNION ALL
                SELECT a.id, a.student_id, l.sentence, json_extract(a.result_json,'$.transcript'),
                       a.accuracy, json_extract(a.result_json,'$.wpm'), a.stars, a.passed,
                       a.created_at, a.track, 'dynamic', json_extract(a.result_json,'$.words'),
                       'level-' || a.level, 'level-' || a.level
                FROM story_attempts a LEFT JOIN story_levels l ON l.track=a.track AND l.level=a.level
                WHERE a.is_mock=0
            ) a JOIN students st ON st.id=a.student_id
            WHERE st.classroom_id=? AND st.archived=0
              AND (?='teacher' OR st.id=?) AND (? IS NULL OR st.id=?)
            ORDER BY a.created_at DESC, a.id DESC LIMIT 5000
        """, (user["classroom_id"], user["role"], user.get("student_id"), student_id, student_id)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        try:
            words = json.loads(item.pop("words_json") or "[]")
            item["words"] = words if isinstance(words, list) else []
        except (ValueError, TypeError):
            item["words"] = []
        result.append(item)
    return result


def average(rows, key="accuracy"):
    values = [float(r[key]) for r in rows if r.get(key) is not None]
    return round(sum(values)/len(values), 1) if values else None


def stats(rows):
    return {"attempted": len(rows), "passed": sum(bool(r["passed"]) for r in rows),
            "stars": sum(r["stars"] or 0 for r in rows), "avg_accuracy": average(rows),
            "last_active": rows[0]["created_at"] if rows else None}


def errors(rows):
    return Counter(str(w["word"]).lower() for r in rows for w in r["words"]
                   if isinstance(w, dict) and w.get("word") and not w.get("correct"))


def roster(user):
    records = attempts_for(user)
    with get_db_connection() as conn:
        accounts = {r["student_id"]: dict(r) for r in conn.execute(
            "SELECT username,status,student_id FROM users WHERE classroom_id=?", (user["classroom_id"],))}
    result = []
    for student in students_for(user):
        data = stats([r for r in records if r["student_id"] == student["id"]])
        account = accounts.get(student["id"], {})
        result.append({**student, "checkpoints_attempted": data["attempted"], "checkpoints_passed": data["passed"],
                       "stars": data["stars"], "avg_accuracy": data["avg_accuracy"], "last_active": data["last_active"],
                       "parent_update_enabled": bool(student.get("parent_update_enabled", 1)),
                       "account_username": account.get("username"), "account_status": account.get("status")})
    return result


def reports(user):
    records = attempts_for(user)
    result = []
    for student in roster(user):
        reads = [r for r in records if r["student_id"] == student["id"]]
        if not reads:
            continue
        result.append({**student, "student_id": student["id"],
            "trend": "on_track" if (average(reads) or 0)>=80 else "needs-practice",
            "recent_checkpoints": [{"checkpoint_id": r["checkpoint_id"] or r["id"], "accuracy": r["accuracy"],
                "stars": r["stars"], "created_at": r["created_at"], "story_id": r["story_id"] or "classic",
                "language": r["language"], "story_title": r["target_sentence"]} for r in reads[:5]]})
    return {"generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "reports": result}


def parent_message(user, student_id):
    student = next((s for s in students_for(user) if s["id"] == student_id), None)
    if not student or not student.get("parent_update_enabled", 1):
        return {"enabled": False, "message": None}
    reads = attempts_for(user, student_id)
    if not reads:
        return {"enabled": True, "student_name": student["name"], "message": f"{student['name']} has not completed a recorded reading yet."}
    last = reads[0]
    tricky = errors([last]).most_common(3)
    text = f"{student['name']} completed reading practice with {round(last['accuracy'])}% word accuracy."
    if tricky:
        text += " Practice words: " + ", ".join(w for w, _ in tricky) + "."
    if last["language"] == "ur":
        text = f"{student['name']} نے پڑھنے کی مشق مکمل کی۔ الفاظ کی درستگی {round(last['accuracy'])}% رہی۔"
        if tricky:
            text += " مشق کے الفاظ: " + "، ".join(w for w, _ in tricky) + "۔"
    return {"enabled": True, "student_name": student["name"], "message": text,
            "based_on": {"date": last["created_at"], "accuracy": last["accuracy"]}}


def practice(user):
    reads = attempts_for(user)
    counts = errors(reads)
    recent = errors(reads[:max(1,len(reads)//2)])
    older = errors(reads[max(1,len(reads)//2):])
    exercises = []
    for i, (word, count) in enumerate(counts.most_common(12)):
        example = next(r for r in reads if any(w.get("word", "").lower()==word for w in r["words"] if isinstance(w,dict)))
        exercises.append({"id": f"word-{i}", "focus": f"Word: {word}", "frequency": count, "words": [word],
            "sentence": example["target_sentence"], "story_id": example["story_id"], "checkpoint_id": example["checkpoint_id"],
            "sources": [example["engine"]], "trend": "new" if not older[word] else "steady"})
    return {"exercises": exercises, "struggling_words": [{"word": w,"count": n} for w,n in counts.most_common(12)],
            "scope": "student" if user["role"]=="student" else "class", "total_words_analyzed": sum(len(r["words"]) for r in reads),
            "progress": {"improving": [w for w in older if older[w]>recent[w]],
                         "worsening": [w for w in older if recent[w]>older[w]], "new_sounds": [], "conquered_words": []}}


def dashboard(user, student_id, period="all"):
    student = next(s for s in students_for(user) if s["id"] == student_id)
    reads = attempts_for(user, student_id)
    if period == "week":
        cutoff=(datetime.utcnow()-timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        reads=[r for r in reads if r["created_at"]>=cutoff]
    elif period == "session":
        reads=reads[:1]
    data=stats(reads); days=defaultdict(list)
    for read in reads: days[read["created_at"][:10]].append(read)
    from routers.v1 import STORIES
    stories=[]
    for sid, story in STORIES.items():
        checkpoints=[r for r in reads if r["story_id"]==sid]
        passed=len({r["checkpoint_id"] for r in checkpoints if r["passed"]})
        stories.append({"story_id":sid,"title":story["title"],"emoji":story["emoji"],"passed":passed,
                        "total":len(story["checkpoints"]),"stars":sum(r["stars"] or 0 for r in checkpoints)})
    return {"student":student,"summary":{"stars":data["stars"],"checkpoints_passed":data["passed"],
        "checkpoints_attempted":data["attempted"],"avg_accuracy":data["avg_accuracy"],"recent_score":average(reads[:3]),
        "progress_pct":round(100*sum(s["passed"] for s in stories)/max(1,sum(s["total"] for s in stories))),
        "classic_sessions":sum(r["engine"]=="classic" for r in reads),"story_sessions":sum(r["engine"]!="classic" for r in reads)},
        "trend":[{"date":d,"accuracy":average(rows),"wpm":average(rows,"wpm") or 0,"checkpoints":len(rows)} for d,rows in sorted(days.items())[-14:]],
        "struggling_words":[{"word":w,"count":n} for w,n in errors(reads).most_common(8)], "phoneme_errors":[],"stories":stories,
        "recent_sessions":[{"id":r["id"],"story_id":r["story_id"],"language":r["language"],"created_at":r["created_at"],
            "completed_at":r["created_at"],"attempted":1,"avg_accuracy":r["accuracy"],"stars":r["stars"],
            "kind":"classic" if r["engine"]=="classic" else "story","label":r["target_sentence"] or "Reading attempt","wpm":r["wpm"]} for r in reads[:8]]}


def overview(user):
    reads=attempts_for(user);days=defaultdict(list)
    for read in reads: days[read["created_at"][:10]].append(read)
    counts=errors(reads);total=sum(counts.values()) or 1
    from routers.v1 import STORIES
    checkpoint_groups=defaultdict(list)
    for read in reads:
        if read["engine"] != "classic":
            checkpoint_groups[(read["story_id"],read["checkpoint_id"])].append(read)
    checkpoint_progress=[]
    for (story_id,checkpoint_id),rows in checkpoint_groups.items():
        story=STORIES.get(story_id,{})
        checkpoint_progress.append({"story_id":story_id,"story_title":story.get("title",story_id),
            "story_emoji":story.get("emoji","📖"),"checkpoint_id":checkpoint_id,
            "checkpoint_label":rows[0]["target_sentence"] or checkpoint_id,"attempted":len(rows),
            "passed":sum(bool(r["passed"]) for r in rows),"avg_accuracy":average(rows) or 0})
    return {"totals":{"active_students":len(students_for(user)),"sessions_today":len(days.get(datetime.utcnow().strftime("%Y-%m-%d"),[])),
            "class_accuracy":average(reads[:40]),"stars_awarded":sum(r["stars"] or 0 for r in reads)},
        "weekly":[{"day":d,"accuracy":average(rows),"sessions":len(rows)} for d,rows in sorted(days.items())[-7:]],
        "struggling_areas":[{"label":f"Word: {w}","count":n,"rate":round(100*n/total)} for w,n in counts.most_common(5)],
        "phoneme_heatmap":[],"words_analyzed":sum(len(r["words"]) for r in reads),"checkpoint_progress":checkpoint_progress}
