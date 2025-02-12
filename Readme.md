# AIPDET - Backend


# How to run this project locally

## Prerequisites

- Python 3.11.10 or higher
- pip (Python package manager)
- Google Earth Engine (Batch Compute Engine) access (Authorized IAM User with Service Account Credentials)
- BigQuery Instance access (Authorized IAM User with Service Account Credentials)
- PostgreSQL DB 

## Steps


### 1. Clone this repository 

### 2. Create and activate a virtual environment


```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add environment variables
- Create a .env file based on .env.sample

### 5. Seeding the Database

#### Info

If you set up PostgreSQL outside of GCP make sure to set the database connection in 'src/database.py' accordingly. 

Run all Seed files inside /setup: 
- Run bigquery.seed.sql on your BigQuery instance
- Run db.seed.sql on your PostgreSQL instance 
- Run test.seed.sql on your PostgresSQL instance to allow for integration and end-2-end tests. 


### 6. Start the development server

```bash
fastapi dev src/main.py
```

### 7. Follow the instructions printed in the terminal to access the API and docs


## Testing

To run the tests use the pytest command inside your venv

```bash
pytest
```

