import psycopg2

# Connection parameters
DB_HOST = "spectranewcrm.cj8ia60gaujz.me-central-1.rds.amazonaws.com"
DB_PORT = "5432"
DB_NAME = "SgfxClient"
DB_USER = "postgres"
DB_PASSWORD = "~ae_QPZ%zAGD26NJ_v}f"

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    print("✅ Connected successfully!")

    cur = conn.cursor()
    cur.execute("SELECT NOW();")
    print("Server time:", cur.fetchone())

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Error:", e)
