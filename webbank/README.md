# WebBank: A Comprehensive Digital Cooperative Banking Platform

## Project Overview
WebBank is a sophisticated digital cooperative banking platform designed to empower individuals and communities to grow their finances through shared resources and collective investment. Founded in 2018, WebBank aims to provide a secure, transparent, and user-friendly environment for managing loans, shares, and member activities. The platform supports a diverse range of user types, including Members, Directors, System Admins, Guarantors, and Founders, each with tailored access and functionalities.

## Key Features

*   **User Authentication & Authorization**: Secure sign-up, sign-in, and logout functionalities with distinct user roles (Member, Director, Admin, Guarantor, Founder).
*   **Member Management**: Administration panel for managing user accounts, approving new members, deactivating users, and resetting passwords.
*   **Loan Management System**:
    *   Apply for various loan types.
    *   Loan approval workflow involving Manager and Director roles.
    *   Loan configuration panel for defining loan products (interest rates, terms).
    *   Loan performance reporting.
*   **Share Management System**:
    *   Purchase and manage shares.
    *   Share configuration panel for setting share prices and other parameters.
    *   Share value trends reporting.
*   **Admin & Founder Panels**: Dedicated dashboards with statistics and administrative controls for system administrators and founders.
*   **Reporting & Analytics**:
    *   Loan Performance Report.
    *   Member Growth Report.
    *   Share Value Trends Report.
    *   Financial Statements Report (Balance Sheet, Income Statement) with CSV export functionality.
*   **Notification System**:
    *   Real-time notifications displayed in a dedicated modal.
    *   Configurable notification settings and templates.
    *   Email notifications for significant events (e.g., account registration, loan approval).
*   **Audit Log**: Comprehensive logging of administrative actions for compliance and security.
*   **Partner Integration**: Information pages for valued partners (e.g., Prolink Network, AMOR 108 INV).
*   **Client-Side Search**: Search functionality on the landing page to easily find information within the displayed content.
*   **Responsive Design**: Built with Bootstrap 5 for a mobile-first, responsive user experience.

## Technologies Used

*   **Backend**: Python, Django 5.2
*   **Database**: SQLite (default, configurable for PostgreSQL/MySQL)
*   **Frontend**: HTML5, CSS3, JavaScript
*   **Styling/Framework**: Bootstrap 5
*   **Charting**: Chart.js
*   **Icons**: Bootstrap Icons, Font Awesome, Boxicons

## Getting Started

Follow these steps to set up and run the WebBank application on your local machine.

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/webbank.git
    cd webbank
    ```
    (Replace `https://github.com/your-username/webbank.git` with the actual repository URL)

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (You may need to create a `requirements.txt` file first if it doesn't exist by running `pip freeze > requirements.txt`)

### Database Setup

1.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```

2.  **Create a superuser (admin account):**
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to create an administrator account. This account will have access to the Django admin panel and the founder/admin dashboards.

### Email Configuration (Crucial for welcome emails and other notifications)

The application is configured to send emails using a Gmail SMTP server. For this to work, you must set an environment variable for the email password.

1.  **Generate an App Password for your Gmail account:**
    *   Go to your Google Account.
    *   Navigate to "Security".
    *   Under "How you sign in to Google," select "2-Step Verification" (ensure it's turned on).
    *   Scroll down to "App passwords" and generate a new one.
    *   Copy the generated 16-character password.

2.  **Set the `EMAIL_HOST_PASSWORD` environment variable:**
    *   **Windows (Command Prompt):**
        ```bash
        set EMAIL_HOST_PASSWORD="your_app_password"
        ```
    *   **Windows (PowerShell):**
        ```powershell
        $env:EMAIL_HOST_PASSWORD="your_app_password"
        ```
    *   **macOS/Linux:**
        ```bash
        export EMAIL_HOST_PASSWORD="your_app_password"
        ```
    *   **Using a `.env` file (recommended for development):**
        Create a file named `.env` in the root of your project with the following content:
        ```
        EMAIL_HOST_PASSWORD="your_app_password"
        ```
        Then, ensure you have `python-dotenv` installed (`pip install python-dotenv`) and load it in your `settings.py` (if not already done).

    *Replace `"your_app_password"` with the 16-character app password you generated.*

### Running the Application

1.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```

2.  **Access the application:**
    Open your web browser and go to `http://127.0.0.1:8000/`

## Usage

*   **Landing Page**: Explore the public features and information.
*   **Register**: Create a new user account (awaiting admin approval by default).
*   **Sign In**: Access your dashboard based on your user type.
*   **Admin/Founder Dashboards**: Navigate to `/admin-panel/` (or specific founder/admin URLs) after logging in with appropriate credentials to access administrative features.

## Contributing
Contributions are welcome! Please fork the repository and submit pull requests.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
