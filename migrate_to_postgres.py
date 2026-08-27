import os
import psycopg2
from dotenv import load_dotenv

# Load credentials from the root .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or "myuser" in DATABASE_URL:
    print("WARNING: Please update the DATABASE_URL in the .env file with your actual PostgreSQL credentials.")
    exit(1)

DDL_QUERIES = """
-- Drop tables if they already exist to ensure a clean slate
DROP TABLE IF EXISTS atm_cashouts CASCADE;
DROP TABLE IF EXISTS cfcfrms_transactions CASCADE;
DROP TABLE IF EXISTS ncrp_complaints CASCADE;

-- 1. Table for National Cybercrime Reporting Portal (NCRP) Complaints
CREATE TABLE ncrp_complaints (
    ack_no VARCHAR(20) PRIMARY KEY,
    incident_timestamp TIMESTAMP NOT NULL,
    reported_timestamp TIMESTAMP NOT NULL,
    crime_category VARCHAR(50) NOT NULL,
    defrauded_amount NUMERIC(12, 2) NOT NULL,
    initial_beneficiary_upi VARCHAR(255) NOT NULL,
    victim_state VARCHAR(50) NOT NULL
);

CREATE INDEX idx_complaints_reported_time ON ncrp_complaints(reported_timestamp);

-- 2. Table for Mule Network Transactions (CFCFRMS layer)
CREATE TABLE cfcfrms_transactions (
    txn_utr VARCHAR(50) PRIMARY KEY,
    source_account VARCHAR(255) NOT NULL,
    beneficiary_account VARCHAR(255) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    layer_depth INTEGER NOT NULL,
    channel VARCHAR(20) NOT NULL
);

CREATE INDEX idx_txn_source ON cfcfrms_transactions(source_account);
CREATE INDEX idx_txn_beneficiary ON cfcfrms_transactions(beneficiary_account);

-- 3. Table for Physical Hotspots and Terminal Cashouts
CREATE TABLE atm_cashouts (
    cashout_id UUID PRIMARY KEY,
    mule_account VARCHAR(255) NOT NULL,
    terminal_id VARCHAR(50) NOT NULL,
    terminal_type VARCHAR(20) NOT NULL,
    amount_withdrawn NUMERIC(12, 2) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL
);

CREATE INDEX idx_cashout_terminal ON atm_cashouts(terminal_id);
CREATE INDEX idx_cashout_time ON atm_cashouts(timestamp);
CREATE INDEX idx_cashout_location ON atm_cashouts(latitude, longitude);
"""

def migrate_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    files_to_copy = [
        ('ncrp_complaints', os.path.join(data_dir, 'ncrp_complaints.csv')),
        ('cfcfrms_transactions', os.path.join(data_dir, 'cfcfrms_transactions.csv')),
        ('atm_cashouts', os.path.join(data_dir, 'atm_cashouts.csv'))
    ]

    for _, file_path in files_to_copy:
        if not os.path.exists(file_path):
            print(f"ERROR: Cannot find {file_path}. Have you generated the synthetic data yet?")
            return

    try:
        print(f"Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("Executing DDL to create tables and indexes...")
        cur.execute(DDL_QUERIES)
        conn.commit()
        print("Tables created successfully.")

        # Bulk copy data from CSVs
        for table_name, csv_path in files_to_copy:
            print(f"Ingesting {csv_path} into table '{table_name}'...")
            with open(csv_path, 'r') as f:
                # copy_expert allows us to use Postgres native COPY command for massive speed
                copy_sql = f"COPY {table_name} FROM STDIN WITH CSV HEADER DELIMITER as ','"
                cur.copy_expert(sql=copy_sql, file=f)
                conn.commit()
            print(f"Successfully loaded {table_name}.")

        cur.close()
        conn.close()
        print("\nAll data migrated successfully!")

    except Exception as e:
        print(f"\nDatabase error occurred: {e}")

if __name__ == "__main__":
    migrate_data()
