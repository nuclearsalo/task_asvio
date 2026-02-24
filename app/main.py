import os
import socket
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

#Graceful Shutdown using lifespan context
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC  ---
    print("Application starting: attempting to connect to PostgreSQL...")
    retries = 5
    while retries > 0:
        try:
            conn = get_db_connection()
            conn.close()
            print("Successfully connected to the database!")
            break
        except Exception:
            print(f"Database not ready yet. Retrying in 3 seconds... ({retries} attempts left)")
            retries -= 1
            time.sleep(3)

    yield  # App is running and receiving requests here

    #SHUTDOWN LOGIC
    print("Application is shutting down gracefully. Cleaning up resources...")


app = FastAPI(title="DevOps Task API", lifespan=lifespan)

# Fulfills Requirement: Configuration via Environment Variables
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")  # No hardcoded passwords!


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


#GET /health
@app.get("/health", status_code=200)
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")  # Fulfills Requirement: Executes SELECT 1
        cur.fetchone()
        cur.close()
        conn.close()
        return {"status": 200}  # Fulfills Requirement: HTTP 200 on success
    except Exception as e:
        # Fulfills Requirement: HTTP 500 on error
        raise HTTPException(status_code=500, detail="Database connection failed")


#GET /api/v1/get-status
@app.get("/api/v1/get-status")
def get_status():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM service_status ORDER BY created_at DESC;")
        records = cur.fetchall()
        cur.close()
        conn.close()
        return records  # Fulfills Requirement: Returns records in JSON
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Model for POST request payload
class StatusItem(BaseModel):
    status: str


#POST /api/v1/set-status
@app.post("/api/v1/set-status")
def set_status(item: StatusItem):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO service_status (status) VALUES (%s) RETURNING id;", (item.status,))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Record inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#GET /info
@app.get("/info")
def get_info():
    return {
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "hostname": socket.gethostname(),
        "environment": os.getenv("ENVIRONMENT", "dev")
    }
