import duckdb
import os

DB_PATH = os.path.join("data", "processed", "padron_matching.db")

def replace_characters():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    print(f"Connecting to {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    # 1. Reemplazar Ñ por N en la tabla electores
    print("Checking for 'Ñ' in electores table...")
    count_before = con.execute("SELECT count(*) FROM electores WHERE nombre LIKE '%Ñ%';").fetchone()[0]
    print(f"Found {count_before:,} rows with 'Ñ'.")

    if count_before > 0:
        print("Replacing 'Ñ' with 'N'...")
        con.execute("UPDATE electores SET nombre = REPLACE(nombre, 'Ñ', 'N') WHERE nombre LIKE '%Ñ%';")
        
        count_after = con.execute("SELECT count(*) FROM electores WHERE nombre LIKE '%Ñ%';").fetchone()[0]
        print(f"Done. Rows with 'Ñ' remaining: {count_after}")
    else:
        print("No rows with 'Ñ' found.")
    
    con.close()
    print("Done.")

if __name__ == "__main__":
    replace_characters()
