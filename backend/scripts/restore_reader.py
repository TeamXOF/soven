"""Local administrator recovery: python scripts/restore_reader.py STUDENT_ID."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.schema import init_db, get_db_connection


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('student_id')
    args=parser.parse_args()
    init_db()
    with get_db_connection() as conn:
        changed=conn.execute('UPDATE students SET archived=0 WHERE id=?',(args.student_id,)).rowcount
        if not changed:
            raise SystemExit('Reader profile not found')
        conn.execute("UPDATE users SET status='pending' WHERE student_id=?",(args.student_id,))
        conn.commit()
    print('Reader restored. A teacher must approve the account before login.')


if __name__=='__main__':
    main()
