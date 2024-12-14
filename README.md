<<<<<<< HEAD
# Church Visitor Management System

A comprehensive church visitor management system designed to streamline administrative processes and enhance visitor engagement through modern web technologies.

## Features

- Visitor registration with multi-step form
- Child registration capabilities
- Email notifications via SendGrid
- Admin dashboard for visitor management
- Secure authentication system
- Responsive design

## Tech Stack

- Flask web application
- PostgreSQL database
- SendGrid email integration
- Bootstrap for frontend
- Advanced security with CSRF protection

## Prerequisites

- Python 3.7+
- PostgreSQL
- SendGrid API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/church-visitor-management.git
cd church-visitor-management
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Database configuration
export DATABASE_URL=postgresql://username:password@localhost:5432/your_database
export PGUSER=your_username
export PGPASSWORD=your_password
export PGDATABASE=your_database
export PGHOST=localhost
export PGPORT=5432

# SendGrid configuration
export SENDGRID_API_KEY=your_sendgrid_api_key
export SENDGRID_VERIFIED_SENDER=your_verified_email@domain.com
```

4. Initialize the database:
```bash
python create_admin.py
```

5. Run the application:
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
=======
# refreshkc
>>>>>>> 3f926398aa9a5fbfe6cca09558d72b6b72215da1
