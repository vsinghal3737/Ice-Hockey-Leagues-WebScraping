import psycopg2

def get_db_connection():
    connection = psycopg2.connect(
            host = 'hockeydb-prod.cqnkxgkqtyxw.us-west-1.rds.amazonaws.com',
            port = 5432,
            user = 'readonly',
            password = 'nJEqr66UkT08',
            database='hockeydb'
            )
    return connection