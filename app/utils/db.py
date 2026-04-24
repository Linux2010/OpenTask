"""
Database Connection Utility

MySQL connection helper using pymysql.
"""

import pymysql
from typing import Optional
from app.config import settings


def get_db_connection():
    """Get database connection"""
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def execute_query(sql: str, params: Optional[tuple] = None):
    """Execute a query and return results"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            return result
    finally:
        conn.close()


def execute_insert(sql: str, params: tuple):
    """Execute an insert and return the inserted ID"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def execute_update(sql: str, params: tuple):
    """Execute an update and return affected rows"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, params)
            conn.commit()
            return affected
    finally:
        conn.close()