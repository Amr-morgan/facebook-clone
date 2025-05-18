# Facebook Clone

A social media web application inspired by Facebook, built with Django and Django Channels for real-time messaging.

## Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

- Python 3.8+
- PostgreSQL (or SQLite for development)
- Redis (for production)
- Node.js (for frontend assets if using webpack)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Amr-morgan/facebook-clone.git
   cd facebook-clone
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   - For PostgreSQL:
     ```bash
     createdb facebook_clone
     ```
   - Or for SQLite (development only):
     ```bash
     touch db.sqlite3
     ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

### Running the Application

1. **Development server**:
   ```bash
   python manage.py runserver
   ```
   The app will be available at `http://localhost:8000/`

2. **Admin Pannel**:     
   Type in your browser search bar `http://localhost:8000/admin/`


### Project Structure

```
facebook-clone/
├── core/               # Main Django app
│   ├── models.py       # Database models
│   ├── views.py        # View functions
│   ├── consumers.py    # WebSocket handlers
│   └── ...
├── facebook_clone/     # Project settings
├── static/             # Static files
├── templates/          # HTML templates
├── requirements.txt    # Python dependencies
└── manage.py           # Django management script
```

### Features

- User authentication (login, registration)
- Friend system
- Real-time chat using WebSockets
- News feed
- Profile customization