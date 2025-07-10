# nvd_sync
Sync NVD database to a local copy

This is a part of CVE Hunter project which can be found here:
CVE Hunter Web App github project: [https://github.com/hum4nG0D/CVEhunter](https://github.com/hum4nG0D/CVEhunter)
Write up: [https://hum4ng0d.github.io/posts/Code-Project-CVE-Hunter/](https://hum4ng0d.github.io/posts/Code-Project-CVE-Hunter/)


## Database Setup (assumming you already have postgreSQL installed):
Creating database user and database:
```
# Switch to postgres user
sudo -i -u postgres

# Create a new user (replace 'your_username' with your desired username)
createuser --interactive --pwprompt postgreadmin

# Create the database
createdb nvd_database 
```

Setting up table to store CVE data:
```
sudo -i -u postgres
psql -d cvehunter

# Grant permission
GRANT CREATE ON SCHEMA public TO postgreadmin;
ALTER SCHEMA public OWNER TO postgreadmin;

\q


psql -U postgregoat -d cvehunter

# create table
CREATE TABLE cves (
  cve_id TEXT PRIMARY KEY,
  full_json JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Fetching the NVD Database

Using API Key as environment variable:
```
export NVD_API_KEY="your-nvd-api-key"
```

Download initial NVD Database:
```
python nvd_fetch.py
```
![Running sync.sh](/assets/img/nvd_fetch.png)


After that, fun the delta sync script to sync or you can run the `sync.sh` script to keep syncing every 3 hours:
```
python nvd_delta_sync.py

chmod +x run.sh
./sync.sh
```

![Running sync.sh](/assets/img/deltasync.png)