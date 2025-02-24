
import os
import asyncpg
import dotenv
from Library.settings import *
from typing import Optional

dotenv.load_dotenv()

conn_pool: Optional[asyncpg.Pool] = None


async def init_postgres() -> None:
    global conn_pool
    try:
        print("Initializing PostgreSQL connection pool...")
        
        conn_pool = await asyncpg.create_pool(
            dsn=CONNECTION_STRING,
            min_size=1, max_size=10  )
        
        print("PostgreSQL connection pool created successfully.")

    except Exception as e:
        print(f"Error initializing PostgreSQL connection pool: {e}")
        raise

async def get_postgres() -> asyncpg.Pool:
    """
    Get the PostgreSQL connection pool.
    """
    global conn_pool
    if conn_pool is None:
        print("Connection pool is not initialized.")
        try:
            return conn_pool
        except Exception as e:
            raise ConnectionError(f"PostgreSQL connection pool is not initialized.={e}")
    return conn_pool


async def close_postgres() -> None:
    """Close the PostgreSQL connection pool. """
    global conn_pool
    if conn_pool is not None:
        try:
            print("Closing PostgreSQL connection pool...")
            await conn_pool.close()
            print("PostgreSQL connection pool closed successfully.")
        except Exception as e:
            print(f"Error closing PostgreSQL connection pool: {e}")
            raise
    else:
        print("PostgreSQL connection pool was not initialized.")
        
        