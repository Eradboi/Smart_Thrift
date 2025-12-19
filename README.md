# Smart Thrift 🐷💰

**Smart Thrift** is an online piggy bank application designed to help users save money digitally. Built with Django, it allows users to manage their savings, track transactions, and generate account statements.

## 🚀 Features

* **User Authentication**: Secure signup and login for users to access their personal accounts.
* **Dashboard**: A centralized view of account balance and recent activities.
* **Deposits & Withdrawals**: Functionality to manage funds within the thrift account.
* **Account Statements**: Generate and view detailed account statements (PDF format).
* **Transaction History**: Keep track of all financial movements.

## 🛠️ Technologies Used

* **Backend**: Python, Django
* **Frontend**: HTML, CSS, JavaScript (Static files)
* **Database**: SQLite (Default)
* **PDF Generation**: (Likely *ReportLab* or *WeasyPrint* based on the PDF files in the repo)

## 📂 Project Structure

* `SmartThrift/`: Main project configuration directory.
* `accounts/`: Django app handling user authentication, profiles, and account logic.
* `static/`: Contains static assets like CSS, JavaScript, and images.
* `db.sqlite3`: The local SQLite database file.
* `manage.py`: Django's command-line utility.
