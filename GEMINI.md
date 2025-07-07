# Project Overview: Payment Gateway

This project is a payment gateway system built with Django. It appears to handle various aspects of online payments, including integrations with different banks, transaction processing, payouts, and user management.

## Key Technologies

*   **Backend:** Django, Python
*   **Frontend:** Django Templates, HTML, CSS, JavaScript
*   **Databases:** MySQL (primary), potentially MongoDB and SQLite for specific purposes.
*   **Key Libraries:**
    *   `djangorestframework`: For building REST APIs.
    *   `django-two-factor-auth`: For two-factor authentication.
    *   `pandas`, `numpy`: For data manipulation and analysis.
    *   `openpyxl`: For working with Excel files.
    *   `requests`: For making HTTP requests to external services.

## Project Structure

The project is organized into several Django applications, each responsible for a specific set of features:

*   **`payment_gateway`**: The main project directory containing the settings and root URL configuration.
*   **`acb`, `mb`, `vietin`**: These applications likely handle integrations with specific banks (ACB, MB Bank, VietinBank).
*   **`bank`**: A general application for managing bank-related information.
*   **`payout`**: Manages the process of sending payments to users.
*   **`settle_payout`**: Handles the settlement of payouts.
*   **`transaction`**: Manages transaction records.
*   **`partner`**: Manages partner information.
*   **`employee`**: Manages employee information and access.
*   **`cms`**: A content management system.
*   **`two_factor_auth`**: Implements two-factor authentication.
*   **`config`**: For application configuration.
*   **`worker`**: Likely contains background tasks or asynchronous processes.
*   **`mongodb`, `mysql`**: These applications might contain models and logic specific to these databases.

## Setup and Running the Project

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables:**
    *   Create a `.env` file by copying `.env.example`.
    *   Fill in the required environment variables, such as database credentials.

3.  **Run Database Migrations:**
    ```bash
    python manage.py migrate
    ```

4.  **Run the Development Server:**
    ```bash
    python manage.py runserver
    ```
