import duckdb
import os

DB_PATH = os.path.join("data", "processed", "padron_definitivo.db")

def start_shell():
    con = duckdb.connect(DB_PATH)
    print(f"Conectado a {DB_PATH}. Escribe tu SQL (termina con ';') o 'exit' para salir.")
    
    while True:
        try:
            query = input("duckdb> ").strip()
            if query.lower() in ["exit", "quit", "exit;"]:
                break
            if not query:
                continue
            
            # Ejecutar y mostrar como DataFrame para que se vea ordenado
            result = con.execute(query).df()
            print(result.to_string(index=False))
            print("-" * 20)
        except Exception as e:
            print(f"Error: {e}")
    
    con.close()

if __name__ == "__main__":
    start_shell()
