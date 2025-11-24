from fastmcp import FastMCP
import os
import sqlite3
import shutil

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")



# 1. Define source (read-only) and destination (writable) paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
READONLY_DB = os.path.join(BASE_DIR, 'expenses.db')
WRITABLE_DB = '/tmp/expenses.db'

# 2. Copy the DB to /tmp if it doesn't exist there yet
if not os.path.exists(WRITABLE_DB):
    # If you ship an empty DB in your repo, copy it over
    if os.path.exists(READONLY_DB):
        shutil.copy2(READONLY_DB, WRITABLE_DB)
    else:
        # Or just let sqlite create a new one
        pass

# create a FatMCP server instance
mcp = FastMCP(name="Expense Tracker")

def init_db():
    with sqlite3.connect(WRITABLE_DB) as conn:
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS expenses (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         date TEXT NOT NULL,
                         amount REAL NOT NULL,
                         category TEXT NOT NULL,
                         subcategory TEXT NOT NULL,
                         note TEX DEFAULT ''                         
                     )
                    """)
    
init_db()

@mcp.tool
def add_expense(date: str, amount: float, category: str, subcategory = "", note: str = "") -> str:
    """Add an expense record to the database."""
    with sqlite3.connect(WRITABLE_DB) as conn:
        conn.execute("""
                     INSERT INTO expenses (date, amount, category, subcategory, note)
                     VALUES (?, ?, ?, ?, ?)
                     """, (date, amount, category, subcategory, note))
    return {"status": "ok"}

@mcp.tool
def list_expenses() -> list[dict]:
    """List all expense records in the database."""
    with sqlite3.connect(WRITABLE_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM expenses order by id ASC")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

@mcp.tool
def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive data range.'''
    with sqlite3.connect(WRITABLE_DB) as conn:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            from expenses
            Where date BETWEEN ? AND ?
            """
        ) 
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)
        query += " GROUP BY category ORDER BY category ASC"

        cur = conn.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()    

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

# To run the server, execute this script and connect to it using a FastMCP client.
# You can then call the `add_expense` and `list_expenses` tools remotely.@mcp.tool
