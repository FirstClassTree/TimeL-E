## pgAdmin Usage Instructions

### 1. Start pgAdmin

Run the following command to start all services, including pgAdmin:

```bash
docker-compose up --build
```
Make sure the .env file includes the necessary pgAdmin and Postgres credentials.

### 2. Open pgAdmin in Browser

Visit: http://localhost:5050

### 3. Login Credentials

Use the credentials defined in the .env file:

Email: `PGADMIN_DEFAULT_EMAIL`

Password: `PGADMIN_DEFAULT_PASSWORD`

### 4. Manually Add the Server (first time)

If no servers are visible:

Click "Add New Server" in the General tab, set:

* Name: `TimeleDB`

In the Connection tab, fill in using the credentials defined in the .env file:

* Host: `DB_HOST`
* Port: `5432`
* Maintenance DB: `POSTGRES_DB`
* Username: `POSTGRES_USER`
* Password: `POSTGRES_PASSWORD`

Click Save.

### 5. Access PostgreSQL Database

Click to expand TimeleDB server and browse the timele_db database,

which contains all the tables and schemas (e.g. orders, products, users).

Utilize SQL query tool to query the postgres db directly.
