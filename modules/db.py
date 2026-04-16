import sqlite3
from pathlib import Path
import json


class Database:
    def __init__(self, db_path="data/leads.db"):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nb_leads INTEGER DEFAULT 0,
                nb_sent INTEGER DEFAULT 0,
                nb_qualified INTEGER DEFAULT 0,
                duree_sec INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER REFERENCES sessions(id),
                siret TEXT,
                nom TEXT,
                societe TEXT,
                secteur TEXT,
                ville TEXT,
                email TEXT DEFAULT '',
                tel TEXT DEFAULT '',
                score INTEGER DEFAULT 0,
                priorite INTEGER DEFAULT 3,
                signaux TEXT DEFAULT '[]',
                source TEXT DEFAULT 'SIRENE',
                status TEXT DEFAULT 'new',
                mode TEXT DEFAULT 'manual',
                message_linkedin TEXT DEFAULT '',
                message_email TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER REFERENCES leads(id),
                canal TEXT,
                role TEXT,
                message TEXT,
                score_maturite INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def create_session(self):
        cur = self.conn.execute("INSERT INTO sessions DEFAULT VALUES")
        self.conn.commit()
        return cur.lastrowid

    def update_session(self, session_id, **kwargs):
        cols = ", ".join(f"{k}=?" for k in kwargs)
        self.conn.execute(
            f"UPDATE sessions SET {cols} WHERE id=?",
            (*kwargs.values(), session_id)
        )
        self.conn.commit()

    def insert_lead(self, session_id, lead):
        signaux = lead.get("signaux", [])
        if isinstance(signaux, list):
            signaux = json.dumps(signaux, ensure_ascii=False)
        cur = self.conn.execute("""
            INSERT INTO leads (session_id, siret, nom, societe, secteur, ville,
                               email, tel, score, priorite, signaux, source,
                               message_linkedin, message_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, lead.get("siret", ""), lead.get("nom", ""),
            lead.get("societe", ""), lead.get("secteur", ""), lead.get("ville", ""),
            lead.get("email", ""), lead.get("tel", ""),
            lead.get("score", 0), lead.get("priorite", 3), signaux,
            lead.get("source", "SIRENE"),
            lead.get("message_linkedin", ""), lead.get("message_email", "")
        ))
        self.conn.commit()
        return cur.lastrowid

    def get_leads_by_session(self, session_id):
        rows = self.conn.execute(
            "SELECT * FROM leads WHERE session_id=? ORDER BY score DESC",
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_lead_status(self, lead_id, status, mode=None):
        if mode:
            self.conn.execute(
                "UPDATE leads SET status=?, mode=? WHERE id=?",
                (status, mode, lead_id)
            )
        else:
            self.conn.execute(
                "UPDATE leads SET status=? WHERE id=?",
                (status, lead_id)
            )
        self.conn.commit()

    def insert_conversation(self, lead_id, canal, role, message, score_maturite=0):
        cur = self.conn.execute("""
            INSERT INTO conversations (lead_id, canal, role, message, score_maturite)
            VALUES (?, ?, ?, ?, ?)
        """, (lead_id, canal, role, message, score_maturite))
        self.conn.commit()
        return cur.lastrowid

    def get_conversations(self, lead_id):
        rows = self.conn.execute(
            "SELECT * FROM conversations WHERE lead_id=? ORDER BY timestamp",
            (lead_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_sessions(self):
        rows = self.conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_leads_pending_agent(self):
        """Returns leads in agent mode awaiting response."""
        rows = self.conn.execute("""
            SELECT * FROM leads
            WHERE mode='agent' AND status='sent'
            ORDER BY created_at ASC
        """).fetchall()
        return [dict(r) for r in rows]
