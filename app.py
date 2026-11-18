
import os
import json
from datetime import date

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from database import get_db_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-secret")


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def dashboard():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT COUNT(*) AS total FROM companies")
        company_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM jobs")
        job_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM applications")
        application_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM contacts")
        contact_count = cursor.fetchone()["total"]

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "dashboard.html",
        company_count=company_count,
        job_count=job_count,
        application_count=application_count,
        contact_count=contact_count
    )


# ==========================================
# COMPANIES CRUD
# ==========================================

COMPANY_FIELDS = (
    "company_name", "industry", "website",
    "city", "state", "notes"
)


def get_company_form_data():
    return {
        field: request.form.get(field, "").strip()
        for field in COMPANY_FIELDS
    }


# READ - Display all companies
@app.route("/companies")
def companies():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM companies ORDER BY company_name"
        )
        all_companies = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "companies.html",
        companies=all_companies
    )


# CREATE - Add a company
@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    company = {}

    if request.method == "POST":
        company = get_company_form_data()

        if not company["company_name"]:
            flash("Company name is required.")

        elif len(company["company_name"]) > 100:
            flash("Company name must be at most 100 characters.")

        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO companies
                    (company_name, industry, website, city, state, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, tuple(
                    company[field] for field in COMPANY_FIELDS
                ))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

            flash("Company added successfully!")
            return redirect(url_for("companies"))

    return render_template(
        "company_form.html",
        company=company,
        editing=False
    )


# UPDATE - Edit a company
@app.route("/companies/<int:company_id>/edit",
           methods=["GET", "POST"])
def edit_company(company_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM companies WHERE company_id = %s",
            (company_id,)
        )

        company = cursor.fetchone()

        if company is None:
            abort(404)

        if request.method == "POST":
            company = get_company_form_data()

            if not company["company_name"]:
                flash("Company name is required.")

            elif len(company["company_name"]) > 100:
                flash("Company name must be at most 100 characters.")

            else:
                cursor.execute("""
                    UPDATE companies
                    SET company_name = %s,
                        industry = %s,
                        website = %s,
                        city = %s,
                        state = %s,
                        notes = %s
                    WHERE company_id = %s
                """, tuple(
                    company[field] for field in COMPANY_FIELDS
                ) + (company_id,))

                conn.commit()

                flash("Company updated successfully!")
                return redirect(url_for("companies"))

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "company_form.html",
        company=company,
        editing=True
    )


# DELETE - Remove a company
@app.route("/companies/<int:company_id>/delete",
           methods=["POST"])
def delete_company(company_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM companies WHERE company_id = %s",
            (company_id,)
        )

        deleted = cursor.rowcount
        conn.commit()

    finally:
        cursor.close()
        conn.close()

    if deleted:
        flash("Company deleted successfully!")
    else:
        flash("Company not found.")

    return redirect(url_for("companies"))


# ==========================================
# JOBS CRUD
# ==========================================

JOB_TYPES = (
    "Full-time",
    "Part-time",
    "Contract",
    "Internship"
)

JOB_FIELDS = (
    "company_id",
    "job_title",
    "job_type",
    "salary_min",
    "salary_max",
    "job_url",
    "date_posted",
    "requirements"
)


def get_job_form_data():
    return {
        field: request.form.get(field, "").strip()
        for field in JOB_FIELDS
    }


# Get companies for job dropdown
def get_company_options():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT company_id, company_name
            FROM companies
            ORDER BY company_name
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


# Convert JSON requirements into a Python list
def get_job_skills(raw):
    if not raw:
        return []

    try:
        skills = (
            json.loads(raw)
            if isinstance(raw, str)
            else raw
        )

        return skills if isinstance(skills, list) else []

    except (ValueError, TypeError):
        return []


# Validate job form data
def validate_job(job, companies):
    if not job["job_title"]:
        return "Job title is required."

    if len(job["job_title"]) > 100:
        return "Job title must be at most 100 characters."

    valid_ids = {
        str(c["company_id"])
        for c in companies
    }

    if job["company_id"] not in valid_ids:
        return "Please select a valid company."

    if job["job_type"] and job["job_type"] not in JOB_TYPES:
        return "Invalid job type."

    for field in ("salary_min", "salary_max"):
        if job[field]:
            if not job[field].isdigit():
                return "Salary must be a nonnegative whole number."

            if int(job[field]) > 2147483647:
                return "Salary is too large."

    if job["salary_min"] and job["salary_max"]:
        if int(job["salary_min"]) > int(job["salary_max"]):
            return "Minimum salary cannot exceed maximum salary."

    if job["date_posted"]:
        try:
            date.fromisoformat(job["date_posted"])

        except ValueError:
            return "Please enter a valid posting date."

    if len(job["job_url"]) > 300:
        return "Job URL is too long."

    return None


# Prepare job values for MySQL
def job_sql_values(job):
    skills = list(dict.fromkeys(
        s.strip()
        for s in job["requirements"].split(",")
        if s.strip()
    ))

    return (
        int(job["company_id"]),
        job["job_title"],
        job["job_type"] or None,
        int(job["salary_min"]) if job["salary_min"] else None,
        int(job["salary_max"]) if job["salary_max"] else None,
        job["job_url"] or None,
        job["date_posted"] or None,
        json.dumps(skills)
    )


# READ - Display all jobs
@app.route("/jobs")
def jobs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT j.*, c.company_name
            FROM jobs j
            JOIN companies c
                ON j.company_id = c.company_id
            ORDER BY j.job_id DESC
        """)

        all_jobs = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    for job in all_jobs:
        job["skills_text"] = ", ".join(
            str(skill)
            for skill in get_job_skills(job["requirements"])
        )

    return render_template(
        "jobs.html",
        jobs=all_jobs
    )


# CREATE - Add a job
@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    companies_list = get_company_options()
    job = {}

    if request.method == "POST":
        job = get_job_form_data()

        error = validate_job(job, companies_list)

        if error:
            flash(error)

        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO jobs
                    (
                        company_id,
                        job_title,
                        job_type,
                        salary_min,
                        salary_max,
                        job_url,
                        date_posted,
                        requirements
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, job_sql_values(job))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

            flash("Job added successfully!")
            return redirect(url_for("jobs"))

    return render_template(
        "job_form.html",
        job=job,
        companies=companies_list,
        editing=False
    )


# UPDATE - Edit an existing job
@app.route("/jobs/<int:job_id>/edit",
           methods=["GET", "POST"])
def edit_job(job_id):
    companies_list = get_company_options()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM jobs WHERE job_id = %s",
            (job_id,)
        )

        job = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if job is None:
        abort(404)

    if request.method == "POST":
        job = get_job_form_data()

        error = validate_job(job, companies_list)

        if error:
            flash(error)

        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    UPDATE jobs
                    SET company_id = %s,
                        job_title = %s,
                        job_type = %s,
                        salary_min = %s,
                        salary_max = %s,
                        job_url = %s,
                        date_posted = %s,
                        requirements = %s
                    WHERE job_id = %s
                """, job_sql_values(job) + (job_id,))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

            flash("Job updated successfully!")
            return redirect(url_for("jobs"))

    else:
        job["requirements"] = ", ".join(
            str(skill)
            for skill in get_job_skills(job["requirements"])
        )

        job["date_posted"] = (
            job["date_posted"].isoformat()
            if job["date_posted"]
            else ""
        )

    return render_template(
        "job_form.html",
        job=job,
        companies=companies_list,
        editing=True
    )


# DELETE - Remove a job
@app.route("/jobs/<int:job_id>/delete",
           methods=["POST"])
def delete_job(job_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM jobs WHERE job_id = %s",
            (job_id,)
        )

        deleted = cursor.rowcount
        conn.commit()

    finally:
        cursor.close()
        conn.close()

    if deleted:
        flash("Job deleted successfully!")
    else:
        flash("Job not found.")

    return redirect(url_for("jobs"))


# ==========================================
# APPLICATIONS CRUD
# ==========================================

APPLICATION_STATUSES = (
    "Applied",
    "Screening",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn"
)


# Get available jobs for the application form
def get_application_job_options():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT j.job_id, j.job_title, c.company_name
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY c.company_name, j.job_title
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# Read application form inputs
def get_application_form_data():
    return {
        "job_id": request.form.get("job_id", "").strip(),
        "application_date": request.form.get(
            "application_date", ""
        ).strip(),
        "status": request.form.get("status", "Applied").strip(),
        "resume_version": request.form.get(
            "resume_version", ""
        ).strip(),
        "cover_letter_sent": (
            request.form.get("cover_letter_sent") == "on"
        ),
        "interview_date": request.form.get(
            "interview_date", ""
        ).strip(),
        "interview_notes": request.form.get(
            "interview_notes", ""
        ).strip()
    }


# Convert interview JSON into a dictionary
def parse_interview_data(raw):
    if not raw:
        return {}

    if isinstance(raw, dict):
        return raw

    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else {}
    except (TypeError, ValueError):
        return {}


# Validate application inputs
def validate_application(application, available_jobs):
    valid_ids = {
        str(job["job_id"]) for job in available_jobs
    }

    if application["job_id"] not in valid_ids:
        return "Please select a valid job."

    if not application["application_date"]:
        return "Application date is required."

    try:
        date.fromisoformat(application["application_date"])
    except ValueError:
        return "Please enter a valid application date."

    if application["status"] not in APPLICATION_STATUSES:
        return "Please select a valid application status."

    if len(application["resume_version"]) > 50:
        return "Resume version must be at most 50 characters."

    if application["interview_date"]:
        try:
            date.fromisoformat(application["interview_date"])
        except ValueError:
            return "Please enter a valid interview date."

    return None


# Prepare values for MySQL
def application_sql_values(application):
    interview_data = {
        "date": application["interview_date"],
        "notes": application["interview_notes"]
    }

    return (
        int(application["job_id"]),
        application["application_date"],
        application["status"],
        application["resume_version"] or None,
        int(application["cover_letter_sent"]),
        json.dumps(interview_data)
    )


# READ - Display all applications
@app.route("/applications")
def applications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT a.*, j.job_title, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.application_date DESC,
                     a.application_id DESC
        """)

        all_applications = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    for application in all_applications:
        interview = parse_interview_data(
            application["interview_data"]
        )

        application["interview_date"] = interview.get("date", "")
        application["interview_notes"] = interview.get("notes", "")

    return render_template(
        "applications.html",
        applications=all_applications
    )


# CREATE - Add an application
@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    available_jobs = get_application_job_options()

    application = {
        "application_date": date.today().isoformat(),
        "status": "Applied",
        "cover_letter_sent": False
    }

    if request.method == "POST":
        application = get_application_form_data()

        error = validate_application(
            application, available_jobs
        )

        if error:
            flash(error)
        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO applications
                    (job_id, application_date, status,
                     resume_version, cover_letter_sent,
                     interview_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, application_sql_values(application))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

            flash("Application added successfully!")
            return redirect(url_for("applications"))

    return render_template(
        "application_form.html",
        application=application,
        jobs=available_jobs,
        statuses=APPLICATION_STATUSES,
        editing=False
    )


# UPDATE - Edit an application
@app.route("/applications/<int:application_id>/edit",
           methods=["GET", "POST"])
def edit_application(application_id):
    available_jobs = get_application_job_options()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT * FROM applications
            WHERE application_id = %s
        """, (application_id,))

        application = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if application is None:
        abort(404)

    if request.method == "POST":
        application = get_application_form_data()

        error = validate_application(
            application, available_jobs
        )

        if error:
            flash(error)
        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    UPDATE applications
                    SET job_id = %s,
                        application_date = %s,
                        status = %s,
                        resume_version = %s,
                        cover_letter_sent = %s,
                        interview_data = %s
                    WHERE application_id = %s
                """, application_sql_values(application)
                     + (application_id,))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

            flash("Application updated successfully!")
            return redirect(url_for("applications"))

    else:
        interview = parse_interview_data(
            application["interview_data"]
        )

        application["interview_date"] = interview.get("date", "")
        application["interview_notes"] = interview.get("notes", "")

        application["application_date"] = (
            application["application_date"].isoformat()
            if application["application_date"]
            else ""
        )

    return render_template(
        "application_form.html",
        application=application,
        jobs=available_jobs,
        statuses=APPLICATION_STATUSES,
        editing=True
    )


# DELETE - Remove an application
@app.route("/applications/<int:application_id>/delete",
           methods=["POST"])
def delete_application(application_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM applications
            WHERE application_id = %s
        """, (application_id,))

        deleted = cursor.rowcount
        conn.commit()

    finally:
        cursor.close()
        conn.close()

    if deleted:
        flash("Application deleted successfully!")
    else:
        flash("Application not found.")

    return redirect(url_for("applications"))


# ==========================================
# RUN FLASK APPLICATION
# ==========================================

# ==========================================
# CONTACTS CRUD
# ==========================================

CONTACT_FIELDS = (
    "company_id",
    "contact_name",
    "title",
    "email",
    "phone",
    "linkedin_url",
    "notes"
)


# Read form data
def get_contact_form_data():
    return {
        field: request.form.get(field, "").strip()
        for field in CONTACT_FIELDS
    }


# Validate contact information
def validate_contact(contact, companies_list):
    valid_company_ids = {
        str(company["company_id"])
        for company in companies_list
    }

    if contact["company_id"] not in valid_company_ids:
        return "Please select a valid company."

    if not contact["contact_name"]:
        return "Contact name is required."

    field_limits = {
        "contact_name": 100,
        "title": 100,
        "email": 100,
        "phone": 20,
        "linkedin_url": 200
    }

    for field, limit in field_limits.items():
        if len(contact[field]) > limit:
            return f"{field.replace('_', ' ').title()} is too long."

    if contact["email"]:
        if "@" not in contact["email"]:
            return "Please enter a valid email address."

    return None


# Prepare values for SQL
def contact_sql_values(contact):
    return (
        int(contact["company_id"]),
        contact["contact_name"],
        contact["title"] or None,
        contact["email"] or None,
        contact["phone"] or None,
        contact["linkedin_url"] or None,
        contact["notes"] or None
    )


# READ - Display all contacts
@app.route("/contacts")
def contacts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT c.*, co.company_name
            FROM contacts c
            JOIN companies co
                ON c.company_id = co.company_id
            ORDER BY c.contact_name
        """)

        all_contacts = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "contacts.html",
        contacts=all_contacts
    )


# CREATE - Add a new contact
@app.route("/contacts/add", methods=["GET", "POST"])
def add_contact():
    companies_list = get_company_options()
    contact = {}

    if request.method == "POST":
        contact = get_contact_form_data()

        error = validate_contact(contact, companies_list)

        if error:
            flash(error)

        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO contacts
                    (
                        company_id,
                        contact_name,
                        title,
                        email,
                        phone,
                        linkedin_url,
                        notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, contact_sql_values(contact))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

            flash("Contact added successfully!")
            return redirect(url_for("contacts"))

    return render_template(
        "contact_form.html",
        contact=contact,
        companies=companies_list,
        editing=False
    )


# UPDATE - Edit an existing contact
@app.route("/contacts/<int:contact_id>/edit",
           methods=["GET", "POST"])
def edit_contact(contact_id):
    companies_list = get_company_options()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM contacts
            WHERE contact_id = %s
        """, (contact_id,))

        contact = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if contact is None:
        abort(404)

    if request.method == "POST":
        contact = get_contact_form_data()

        error = validate_contact(contact, companies_list)

        if error:
            flash(error)

        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    UPDATE contacts
                    SET company_id = %s,
                        contact_name = %s,
                        title = %s,
                        email = %s,
                        phone = %s,
                        linkedin_url = %s,
                        notes = %s
                    WHERE contact_id = %s
                """, contact_sql_values(contact)
                     + (contact_id,))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

            flash("Contact updated successfully!")
            return redirect(url_for("contacts"))

    return render_template(
        "contact_form.html",
        contact=contact,
        companies=companies_list,
        editing=True
    )


# DELETE - Remove a contact
@app.route("/contacts/<int:contact_id>/delete",
           methods=["POST"])
def delete_contact(contact_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM contacts
            WHERE contact_id = %s
        """, (contact_id,))

        deleted = cursor.rowcount
        conn.commit()

    finally:
        cursor.close()
        conn.close()

    if deleted:
        flash("Contact deleted successfully!")
    else:
        flash("Contact not found.")

    return redirect(url_for("contacts"))


# ==========================================
# JOB MATCH FEATURE
# ==========================================

@app.route("/job-match", methods=["GET", "POST"])
def job_match():
    skills_input = ""
    matches = []
    searched = False

    if request.method == "POST":
        skills_input = request.form.get("skills", "").strip()

        # Convert entered skills into a normalized set
        user_skills = {
            skill.strip().casefold()
            for skill in skills_input.split(",")
            if skill.strip()
        }

        if not user_skills:
            flash("Please enter at least one skill.")

        else:
            searched = True

            # Retrieve jobs and their required skills
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            try:
                cursor.execute("""
                    SELECT
                        j.job_id,
                        j.job_title,
                        j.job_type,
                        j.requirements,
                        c.company_name
                    FROM jobs j
                    JOIN companies c
                        ON j.company_id = c.company_id
                """)

                all_jobs = cursor.fetchall()

            finally:
                cursor.close()
                conn.close()

            # Calculate match percentage for each job
            for job in all_jobs:

                required_skills = get_job_skills(
                    job["requirements"]
                )

                # Normalize skills and remove duplicates
                normalized_requirements = {
                    skill.strip().casefold(): skill.strip()
                    for skill in required_skills
                    if isinstance(skill, str) and skill.strip()
                }

                matched_skills = []
                missing_skills = []

                for normalized, original in normalized_requirements.items():
                    if normalized in user_skills:
                        matched_skills.append(original)
                    else:
                        missing_skills.append(original)

                total_required = len(normalized_requirements)
                matched_count = len(matched_skills)

                if total_required > 0:
                    match_percentage = round(
                        (matched_count / total_required) * 100
                    )
                else:
                    match_percentage = 0

                matches.append({
                    "job_id": job["job_id"],
                    "job_title": job["job_title"],
                    "company_name": job["company_name"],
                    "job_type": job["job_type"],
                    "match_percentage": match_percentage,
                    "matched_count": matched_count,
                    "total_required": total_required,
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills
                })

            # Rank jobs by highest match percentage
            matches.sort(
                key=lambda job: (
                    -job["match_percentage"],
                    -job["matched_count"],
                    job["company_name"].casefold()
                )
            )

    return render_template(
        "job_match.html",
        skills_input=skills_input,
        matches=matches,
        searched=searched
    )

if __name__ == "__main__":
    app.run(debug=True)
