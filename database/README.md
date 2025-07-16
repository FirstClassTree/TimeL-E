## Database Schema

This folder documents the current PostgreSQL schema used by the application.

### Files

- `schema.sql` – Exported schema from the running database (read-only for reference).
- `erd.png` – Entity Relationship Diagram.
- `README.md` – You are here.

### How to Update the Schema

If there are changes to the SQLAlchemy models or DB migrations, regenerate the schema file:


#### Windows (CMD)

```bash
docker exec <postgres_container_id> pg_dump --schema-only --no-owner -U timele_user timele_db > database\schema.sql
```

#### Unix/macOS or Git Bash

```
docker exec <postgres_container_id> pg_dump --schema-only --no-owner -U timele_user timele_db > database/schema.sql
```

#### Note
* To find postgres container ID 
    ```bash
    docker ps
    ```

* Ensure the database/ directory exists before running the command.

* The schema.sql is useful for understanding DB structure and generating ER diagrams.