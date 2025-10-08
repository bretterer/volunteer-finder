# Volunteer Match

A web application to connect volunteers with organizations seeking volunteer support. Built for CIS 553 at University of Michigan - Dearborn.

## Team Members
- Abigail Gujuluva
- Brian Retterer
- Stayner Rodriguez
- Matthew Sheaffer

## Project Overview

Volunteer Match is a Django-based platform that facilitates connections between volunteers (primarily students) and organizations. The system features:

- **Search & Browse**: Volunteers can search and browse opportunities
- **Opportunity Posting**: Organizations can post volunteer positions with requirements
- **Smart Matching**: Skills and availability-based recommendation engine
- **Notifications**: Email alerts for applications and confirmations
- **Admin Dashboard**: Analytics and system monitoring

## Tech Stack

- **Language**: Python 3.9+
- **Framework**: Django 4.2
- **Database**: SQLite (development), PostgreSQL (production)
- **Version Control**: Git with GitHub Flow

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd volunteer-finder
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

```
volunteer-finder/
├── volunteer_finder/       # Project settings
├── core/                   # Core functionality app
├── accounts/               # User authentication and profiles
├── opportunities/          # Volunteer opportunity management
├── matching/               # Recommendation engine
├── notifications/          # Email/alert system
├── manage.py
├── requirements.txt
└── README.md
```

## Development Workflow

We use GitHub Flow for version control:
1. Create a feature branch from `main`
2. Make your changes
3. Submit a pull request
4. After review and approval, merge to `main`

## Contributing

Please see the team agreement in our project proposal for communication protocols, meeting schedules, and division of work.

## License

This project is for educational purposes as part of CIS 553 coursework.
