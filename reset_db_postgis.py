import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

DDL_QUERIES = """
-- 1. Enable PostGIS Extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Drop existing tables
DROP TABLE IF EXISTS atm_cashouts CASCADE;
DROP TABLE IF EXISTS cfcfrms_transactions CASCADE;
DROP TABLE IF EXISTS ncrp_complaints CASCADE;

-- 3. Recreate Tables
CREATE TABLE ncrp_complaints (
    ack_no VARCHAR(20) PRIMARY KEY,
    incident_timestamp TIMESTAMP NOT NULL,
    reported_timestamp TIMESTAMP NOT NULL,
    crime_category VARCHAR(50) NOT NULL,
    defrauded_amount NUMERIC(12, 2) NOT NULL,
    initial_beneficiary_upi VARCHAR(255) NOT NULL,
    victim_state VARCHAR(50) NOT NULL
);

CREATE TABLE cfcfrms_transactions (
    txn_utr VARCHAR(50) PRIMARY KEY,
    source_account VARCHAR(255) NOT NULL,
    beneficiary_account VARCHAR(255) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    layer_depth INTEGER NOT NULL,
    channel VARCHAR(20) NOT NULL
);

CREATE TABLE atm_cashouts (
    cashout_id UUID PRIMARY KEY,
    mule_account VARCHAR(255) NOT NULL,
    terminal_id VARCHAR(50) NOT NULL,
    terminal_type VARCHAR(20) NOT NULL,
    amount_withdrawn NUMERIC(12, 2) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    location GEOMETRY(Point, 4326) -- PostGIS Spatial Column
);

-- 4. Standard Indexes
CREATE INDEX idx_complaints_reported_time ON ncrp_complaints(reported_timestamp);
CREATE INDEX idx_txn_source ON cfcfrms_transactions(source_account);
CREATE INDEX idx_txn_beneficiary ON cfcfrms_transactions(beneficiary_account);
CREATE INDEX idx_cashout_terminal ON atm_cashouts(terminal_id);
CREATE INDEX idx_cashout_time ON atm_cashouts(timestamp);
"""

def reset_db_with_postgis():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    files_to_copy = [
        ('ncrp_complaints', os.path.join(data_dir, 'ncrp_complaints.csv')),
        ('cfcfrms_transactions', os.path.join(data_dir, 'cfcfrms_transactions.csv')),
        ('atm_cashouts', os.path.join(data_dir, 'atm_cashouts.csv'))
    ]

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("Executing PostGIS DDL to recreate tables...")
        cur.execute(DDL_QUERIES)
        conn.commit()

        # Ingest CSVs. We only ingest columns that exist in the CSV (which excludes the new 'location' column)
        for table_name, csv_path in files_to_copy:
            print(f"Ingesting {csv_path} into {table_name}...")
            with open(csv_path, 'r') as f:
                # Dynamically get columns from CSV header so we don't try to insert into 'location' yet
                columns = f.readline().strip().split(',')
                f.seek(0)
                copy_sql = f"COPY {table_name} ({','.join(columns)}) FROM STDIN WITH CSV HEADER DELIMITER as ','"
                cur.copy_expert(sql=copy_sql, file=f)
                conn.commit()

        # Populate the PostGIS GEOMETRY column using the latitude/longitude data
        print("Populating PostGIS spatial location column...")
        cur.execute("""
            UPDATE atm_cashouts 
            SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);
        """)
        
        # Create a blazing fast Spatial Index on the geometry column
        print("Building GiST Spatial Index...")
        cur.execute("CREATE INDEX idx_cashouts_location_gist ON atm_cashouts USING GIST (location);")
        conn.commit()

        cur.close()
        conn.close()
        print("\nDatabase reset complete! PostGIS enabled and populated.")

    except Exception as e:
        print(f"\nDatabase error occurred: {e}")
        print("WARNING: Did you install the PostGIS extension for your PostgreSQL server?")

if __name__ == "__main__":
    reset_db_with_postgis()
