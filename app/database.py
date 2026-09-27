import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import settings

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 目标对象表 (可跟踪多个聊天对象档案)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alias TEXT NOT NULL,
        mbti TEXT DEFAULT '',
        relationship_stage TEXT DEFAULT '暧昧/了解中',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 历史分析记录表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER,
        source_type TEXT NOT NULL,  -- 'text' or 'screenshot'
        raw_input TEXT,
        dialogue_parsed TEXT,       -- JSON format of parsed messages
        jev_analysis TEXT,          -- JSON format of Jev System 1 metrics
        llm_reply TEXT,             -- JSON format of System 2 generated replies
        selected_strategy TEXT,     -- e.g. 承接, 降压, 调侃
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (target_id) REFERENCES targets (id) ON DELETE SET NULL
    )
    """)
    
    conn.commit()
    conn.close()

def save_analysis(
    source_type: str,
    raw_input: str,
    dialogue_parsed: List[Dict[str, Any]],
    jev_result: Dict[str, Any],
    llm_result: Dict[str, Any],
    target_id: Optional[int] = None
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO analyses (
        target_id, source_type, raw_input, dialogue_parsed,
        jev_analysis, llm_reply, selected_strategy
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        target_id,
        source_type,
        raw_input,
        json.dumps(dialogue_parsed, ensure_ascii=False),
        json.dumps(jev_result, ensure_ascii=False),
        json.dumps(llm_result, ensure_ascii=False),
        jev_result.get("primary_strategy", "")
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_recent_analyses(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, target_id, source_type, dialogue_parsed, jev_analysis, llm_reply, selected_strategy, created_at
    FROM analyses
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "target_id": r["target_id"],
            "source_type": r["source_type"],
            "dialogue_parsed": json.loads(r["dialogue_parsed"]) if r["dialogue_parsed"] else [],
            "jev_analysis": json.loads(r["jev_analysis"]) if r["jev_analysis"] else {},
            "llm_reply": json.loads(r["llm_reply"]) if r["llm_reply"] else {},
            "selected_strategy": r["selected_strategy"],
            "created_at": r["created_at"]
        })
    conn.close()
    return results
