
# JobTrack — Job Application Tracker

A full-stack web application built with Python, Flask, MySQL, HTML, and CSS for the COP4751 Course Project at Florida International University.

## Project Overview

JobTrack helps users organize and manage their job search in one place. Users can track companies, job opportunities, applications, and professional contacts.

The application also includes a Job Match feature that compares a user's skills with job requirements and calculates match percentages.

## Technologies Used

- Python 3
- Flask
- MySQL
- HTML5
- CSS3
- Jinja2
- Git and GitHub
- python-dotenv
- mysql-connector-python

## Features

### Dashboard
Displays an overview of the total number of companies, jobs, applications, and contacts.

### Company Management
- Add new companies
- View company information
- Edit company details
- Delete companies

### Job Management
- Add job listings associated with companies
- Track job titles, employment types, and salaries
- Store job requirements using MySQL JSON
- Edit and delete job listings

### Application Tracking
- Track application dates and statuses
- Record resume versions
- Track whether a cover letter was submitted
- Store interview dates and notes using JSON
- Edit and delete applications

### Contact Management
- Store recruiter and hiring manager information
- Associate contacts with companies
- Track emails, phone numbers, and LinkedIn profiles
- Edit and delete contacts

### Job Match
Users enter their skills as a comma-separated list.

The application compares these skills against the requirements stored for each job.

Results include:
- Match percentage
- Number of matched skills
- Missing required skills
- Jobs ranked by match percentage

## Database Design

The MySQL database is named `job_tracker`.

It contains four tables:

1. `companies`
2. `jobs`
3. `applications`
4. `contacts`

### Relationships

- One company can have multiple jobs.
- One company can have multiple contacts.
- One job can have multiple applications.

Foreign keys connect the tables and maintain referential integrity.

The `jobs` table uses a JSON column for required skills.

The `applications` table uses a JSON column for interview information.

## Installation Instructions

### 1. Prerequisites

Install the following software:

- Python 3
- MySQL Server
- Git

MySQL Workbench is recommended for managing the database.

### 2. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/N-Sanchez8661/job-application-tracker.git
cd job-application-tracker
```

Replace `YOUR-USERNAME` with the repository owner's GitHub username.

### 3. Create a Virtual Environment

For macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

For Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Set Up MySQL

Start your local MySQL server.

Open MySQL Workbench and connect to the server.

Open the provided `schema.sql` file and execute the SQL script.

The script creates the `job_tracker` database and the four required tables.

### 6. Configure Environment Variables

Create a `.env` file in the project's root directory.

Copy the following configuration:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=job_tracker
SECRET_KEY=YOUR_RANDOM_SECRET_KEY
```

Replace the placeholder values with your local MySQL credentials and a random secret key.

The `.env` file is excluded from GitHub for security.

### 7. Run the Flask Application

In the project directory, run:

```bash
python app.py
```

Alternatively, use `python3 app.py` if required by your system.

Open your browser and navigate to:

http://127.0.0.1:5000

The JobTrack dashboard should now appear.

## How to Use

1. Open the dashboard to view application statistics.
2. Add a company using the Companies page.
3. Create job listings associated with companies.
4. Add applications to track your progress.
5. Add recruiter or hiring manager information under Contacts.
6. Use the Job Match page to compare your skills against job requirements.
7. Edit or delete records when necessary.

## Job Match Algorithm

The application uses a skill-based matching algorithm.

The user enters a comma-separated list of skills.

These are compared with each job's required skills stored in the database.

The match percentage is calculated as:

Match Percentage = (Matched Skills / Total Required Skills) × 100

Example:

Required skills:
Python, SQL, Flask, Git, REST APIs

User skills:
Python, SQL, Flask

Result:
3 of 5 skills matched = 60%

The comparison is case-insensitive and ignores duplicate skills.

Jobs are sorted by match percentage, with the highest matches displayed first.

## Project Structure

```text
job-application-tracker/
│
├── app.py
├── database.py
├── schema.sql
├── requirements.txt
├── README.md
├── AI_USAGE.md
├── .env.example
├── .gitignore
│
├── templates/
│   ├── _nav.html
│   ├── dashboard.html
│   ├── companies.html
│   ├── company_form.html
│   ├── jobs.html
│   ├── job_form.html
│   ├── applications.html
│   ├── application_form.html
│   ├── contacts.html
│   ├── contact_form.html
│   └── job_match.html
│
└── static/
    └── style.css
```

## AI Usage

Generative AI tools were used during development to assist with coding, debugging, and documentation.

AI-generated suggestions were integrated into the project and tested through the running Flask application and MySQL database.

Detailed documentation is available in `AI_USAGE.md`.


## Project Demonstration

A video demonstration of the JobTrack application is available below.

🎥 [Watch JobTrack Project Demonstration](https://youtu.be/7qZ1qVSs7gQ)

The video demonstrates the dashboard, CRUD operations,
Job Match feature, and application functionality.

The demonstration covers:
- User interface and navigation
- CRUD operations
- Job Match functionality
- Flask application execution
- MySQL database

## Course Information

COP4751 — Database Management

Florida International University
