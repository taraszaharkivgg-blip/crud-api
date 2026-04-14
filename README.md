Trello Clone API (FastAPI)

🚀 Features

* User Authentication: Secure signup and login using JWT (JSON Web Tokens) and password hashing (Passlib/Bcrypt).
* Hierarchical Structure: Complete management of Boards, Lists, and Cards.
* Data Validation: Strict input validation using Pydantic schemas (length constraints, email formatting, and custom validators).
* Smart Description Handling: Custom logic to handle empty or whitespace-only descriptions, converting them to `null` for database consistency.
* Relational Integrity: Cascading deletions (deleting a board removes all associated lists and cards).
* Automated Documentation: Fully interactive API documentation via Swagger UI and ReDoc.
* Positioning System: Support for custom ordering of Lists and Cards using a position attribute.
* Database Migrations: Managed database schema evolutions using Alembic.
* Automated Testing: Comprehensive test suite with automatic database cleanup for reliable development.
* CORS Enabled: Ready to be connected with frontend frameworks like React, Vue, or Angular.

🛠 Tech Stack

* Framework: [FastAPI](https://fastapi.tiangolo.com/)
* ORM: [SQLAlchemy](https://www.sqlalchemy.org/)
* Database: [PostgreSQL](https://www.postgresql.org/)/[Sqlite](https://sqlite.org/)
* Testing: Pytest & HTTPX
* Validation: [Pydantic v2](https://docs.pydantic.dev/)
* Security: JWT, OAuth2, Bcrypt

📁 Database Schema

The project uses a one-to-many relationship hierarchy:
- User 1 ➔ N * Boards
- Board 1 ➔ N * Lists
- List 1 ➔ N * Cards

🛡 Validation Examples

* Passwords: Minimum 8 characters.
* Titles: Required, 1-50 characters.
* Empty Strings: The API automatically detects if a description contains only whitespace and stores it as None to maintain clean data.

🔧 Installation & Setup

1. Clone the repository:
    bash
    git clone [https://github.com/YOUR_USERNAME/your-repo-name.git](https://github.com/YOUR_USERNAME/your-repo-name.git)
    cd your-repo-name

2. Create and activate a virtual environment:
    python -m venv venv
    Windows:
    venv\Scripts\activate
    Linux/macOS:
    source venv/bin/activate
   
3. Install dependencies:
    pip install -r requirements.txt

4. Database Setup:
Apply migrations to create the database schema: alembic upgrade head

5. Run the application through your IDE by running main.py

6. Go to http://localhost:8000/docs and enjoy;)
