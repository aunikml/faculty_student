
# FacultyEval - Installation Guide for Ubuntu VM

Welcome to **FacultyEval**, a Django-based system for evaluating faculty performance [or replace with a specific description, e.g., "streamlining faculty performance reviews and feedback collection"]. This guide provides step-by-step instructions to set up and run FacultyEval on an Ubuntu virtual machine using Python 3.11 and PostgreSQL as the database.

## Prerequisites

Before you begin, ensure you have:

- An Ubuntu virtual machine (e.g., Ubuntu 20.04 or 22.04) with internet access.
- Python 3.11 installed.
- Git installed to clone the repository.
- PostgreSQL installed and running.
- Basic knowledge of terminal commands.
- A text editor (e.g., `nano`, `vim`, or VS Code) for editing configuration files.
- [Optional] A virtual machine provider like VirtualBox, VMware, or a cloud service (e.g., AWS, Azure).

## System Requirements

- **OS**: Ubuntu 20.04 LTS or later
- **Python**: 3.11
- **Database**: PostgreSQL 13 or later
- **RAM**: At least 2GB (4GB recommended)
- **Storage**: At least 10GB free disk space
- **Dependencies**: Django, PostgreSQL, and other Python packages listed in `requirements.txt`

## Installation Steps

Follow these steps to install and configure FacultyEval on your Ubuntu VM.

### Step 1: Update the System

Ensure your Ubuntu VM is up to date to avoid compatibility issues.

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Required Software

Install Python 3.11, Git, PostgreSQL, and necessary development tools.

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev git postgresql postgresql-contrib build-essential libpq-dev
```

Verify installations:

```bash
python3.11 --version
psql --version
```

### Step 3: Clone the Repository

Clone the FacultyEval repository from GitHub to your Ubuntu VM.

```bash
git clone https://github.com/aunikml/facultyeval.git
cd facultyeval
```

### Step 4: Set Up a Virtual Environment

Create and activate a Python virtual environment to isolate dependencies.

```bash
python3.11 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### Step 5: Install Python Dependencies

Install the required Python packages listed in `requirements.txt`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Ensure `psycopg2` or `psycopg2-binary` is included in `requirements.txt` for PostgreSQL connectivity. If not, install it manually:

```bash
pip install psycopg2-binary
```

### Step 6: Configure PostgreSQL Database

Set up a PostgreSQL database for FacultyEval.

1. Start the PostgreSQL service:

   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. Create a database and user:

   ```bash
   sudo -u postgres psql
   ```

   In the PostgreSQL prompt, run:

   ```sql
   CREATE DATABASE facultyeval;
   CREATE USER facultyeval_user WITH PASSWORD 'your_secure_password';
   ALTER ROLE facultyeval_user SET client_encoding TO 'utf8';
   ALTER ROLE facultyeval_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE facultyeval_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE facultyeval TO facultyeval_user;
   \q
   ```

3. Update Django settings:

   Edit `facultyeval/settings.py` (or the appropriate settings file) to configure the database connection:

   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'facultyeval',
           'USER': 'facultyeval_user',
           'PASSWORD': 'your_secure_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

### Step 7: Apply Database Migrations

Run Django migrations to set up the database schema.

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 8: Create a Superuser (Optional)

Create an admin user to access the Django admin panel.

```bash
python manage.py createsuperuser
```

Follow the prompts to set up a username, email, and password.

### Step 9: Test the Application

Start the Django development server to verify the setup.

```bash
python manage.py runserver 0.0.0.0:8000
```

- **Note**: Using `0.0.0.0:8000` makes the server accessible from outside the VM (e.g., your host machine). Ensure your VM’s network settings and firewall allow connections to port 8000.

Open a web browser and navigate to:

- `http://<your-vm-ip>:8000/` (replace `<your-vm-ip>` with your VM’s IP address)
- Admin panel: `http://<your-vm-ip>:8000/admin/`

You should see the FacultyEval application running. Log in to the admin panel using the superuser credentials.

### Step 10: Configure for Production (Optional)

For production deployment, follow these additional steps:

1. **Set `DEBUG = False`**:

   Edit `facultyeval/settings.py` and set `DEBUG = False` for security.

2. **Collect Static Files**:

   ```bash
   python manage.py collectstatic
   ```

3. **Install a WSGI Server**:

   Install Gunicorn for serving the application:

   ```bash
   pip install gunicorn
   gunicorn --workers 3 facultyeval.wsgi:application --bind 0.0.0.0:8000
   ```

4. **Set Up a Web Server**:

   Use Nginx as a reverse proxy. Example Nginx configuration:

   ```nginx
   server {
       listen 80;
       server_name your_domain_or_ip;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }

       location /static/ {
           alias /path/to/facultyeval/static/;
       }
   }
   ```

   Install and configure Nginx:

   ```bash
   sudo apt install -y nginx
   sudo cp your_nginx_config /etc/nginx/sites-available/facultyeval
   sudo ln -s /etc/nginx/sites-available/facultyeval /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

5. **Secure with HTTPS**:

   Obtain an SSL certificate using Certbot:

   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d your_domain
   ```

### Step 11: Firewall Configuration

Allow HTTP/HTTPS traffic and port 8000 (for development) through the firewall.

```bash
sudo ufw allow 8000
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## Troubleshooting

- **Python version mismatch**: Verify Python 3.11 is used (`python3.11 --version`).
- **ModuleNotFoundError**: Ensure all dependencies are installed (`pip install -r requirements.txt`).
- **Database connection issues**: Check `facultyeval/settings.py` for correct database settings and ensure PostgreSQL is running (`sudo systemctl status postgresql`).
- **Server not accessible**: Confirm the VM’s IP, ensure port 8000 is open, and check VM network settings for external access.
- **Permission errors**: Ensure the user has write permissions for the project directory.

For additional help, refer to the [Django documentation](https://docs.djangoproject.com/) or open an issue on the [GitHub repository](https://github.com/aunikml/facultyeval).

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please ensure your code follows the project’s coding standards and includes tests where applicable.

## License

This project is licensed under the [specify your license, e.g., MIT License]. See the `LICENSE` file for details.

## Contact

For questions or feedback, contact [your name] at [your email] or open an issue on the [GitHub repository](https://github.com/aunikml/facultyeval).

---

## Notes for You (Not Part of the README)

- **Repository Access**: The repository `https://github.com/aunikml/facultyeval.git` wasn’t accessible, so I assumed a standard Django project structure for a faculty evaluation system. If there are specific features (e.g., custom apps, external APIs, or unique dependencies), please share details, and I can update the guide.
- **PostgreSQL Focus**: As requested, the guide uses PostgreSQL exclusively, omitting SQLite or other database options. I included `libpq-dev` and `psycopg2-binary` for PostgreSQL support.
- **Project Description**: The placeholder description `[streamlining faculty performance reviews...]` can be replaced with a specific description of FacultyEval’s purpose (e.g., “a system for collecting student feedback on faculty”).
- **License**: You’ll need to specify the license (e.g., MIT, GPL). If unsure, I can provide guidance.
- **Dependencies**: The guide assumes a `requirements.txt` file. If your project has specific dependencies, share them for a more precise installation step.
- **Production Setup**: The production steps (Gunicorn, Nginx, HTTPS) are optional but included for completeness. Remove them if FacultyEval is for development only.
- **Search Results**: The provided search results for `facultyeval.git` were mostly generic GitHub-related content and not specific to your repository. I relied on the Django and PostgreSQL context instead. A recent X post about using PostgreSQL with Django was noted but not directly relevant.
- **Verification**: If you confirm the repository URL or share its contents, I can verify and tailor the guide further (e.g., specific settings, custom migrations, or additional setup steps).

