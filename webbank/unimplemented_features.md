# Unimplemented Features and Placeholders

This document lists features, UI elements, and logic that are currently using placeholders or are not fully implemented.

## Amor108 App (`amor108`)

The `amor108` app, which seems to be the main user-facing application, contains a significant number of placeholders for various dashboard sections.

### Placeholder Views

The following dashboard pages are currently routed to a generic `dashboard_placeholder` view in `amor108/views.py`:
-   `/dashboard/investments/`
-   `/dashboard/pools/`
-   `/dashboard/voting/`
-   `/dashboard/notifications/`
-   `/dashboard/documents/`
-   `/dashboard/exit/`
-   `/dashboard/support/`
-   `/dashboard/security/`
-   `/dashboard/transparency/`

### Dummy Data in Views

The `amor108/views.py` file uses dummy data to populate several dashboard pages. This data needs to be replaced with dynamic data from the database.
-   `dashboard_voting`: `active_votes`, `voting_history`
-   `dashboard_transparency`: `financial_statements`, `pool_performance_reports`, `admin_decisions`, `audit_logs`
-   `dashboard_investments`: `active_investments`, `investment_history`
-   `dashboard_documents`: `available_documents`, `member_reports`
-   `dashboard_security`: `security_settings`
-   `dashboard_support`: `support_tickets`, `faqs`
-   `dashboard_exit`: `can_exit`, `exit_requirements`, `withdrawal_options`

### Placeholder UI Elements and Logic in Templates

-   **`_contributions.html`**: The status of a contribution is hardcoded as "Paid".
-   **`_loans.html`**: The outstanding balance for a loan is a placeholder.
-   **`_shares.html`**: Contains a `TODO` to implement a share growth chart.
-   **`dashboard_exit.html`**: The "Proceed" and "Request Exit" buttons are placeholders.
-   **`dashboard_investments.html`**: The "Explore Investment Opportunities" button is a placeholder.
-   **`dashboard_loans.html`**: The link to view the full repayment schedule is a placeholder.
-   **`dashboard_notifications.html`**: The "Mark All as Read" button is a placeholder.
-   **`dashboard_pools.html`**: A section for admin notices is commented out as a placeholder.
-   **`dashboard_security.html`**: Buttons to "Disable/Enable" 2FA and links to "Change Email/Phone" are placeholders.
-   **`dashboard_shares.html`**: "Buy More Shares" and "Withdraw Shares" buttons are placeholders.
-   **`dashboard_support.html`**: "View" and "Open New Ticket" buttons are placeholders.
-   **`dashboard_voting.html`**: A section for "Resolutions and Governance Documents" and a "View All Documents" button are placeholders.

## Loans App (`loans`)

-   **`views.py`**: The `is_webbank_member` variable is hardcoded to `True` in the `webbank_loan_request` view. This logic needs to be refined based on the actual WebBank member model.

## Accounts App (`accounts` & `accounts_amor108`)

-   **`accounts/models.py`**: The `two_factor_enabled` field in the `User` model is a placeholder and not actively implemented.
-   **`accounts_amor108/views.py`**: A `profile_setup` view is mentioned as a placeholder.
-   **`accounts_amor108/templates/accounts_amor108/profile_setup.html`**: This template is a placeholder page.

## Profits App (`profits`)

-   **`utils.py`**: A comment indicates that the governance integration for profit distribution is a placeholder.

## Other Apps

-   **`audit/views.py`**: The "Financial Summaries" and "Pool Performance Reports" in the audit dashboard are placeholders.
-   **`pools/views.py`**: The logic for `can_upgrade` and `next_pool_requirements` in the pools dashboard is placeholder logic.
-   **`admin_panel/views.py`**: A placeholder exists for real-time dividend calculations.
-   **`templates/index.html`**: Member photos are placeholders.
-   **`templates/guarantees/guarantees.html`** and **`templates/members/members.html`**: Search inputs are present but the backend search logic might not be fully implemented.
-   **Various `forms.py` files**: Many form fields have `placeholder` attributes in their widgets. While this is a UI feature, it's worth noting that the forms are designed with these placeholders.
-   **`loans/management/commands/check_loan_defaults.py`**: `TODO` comments exist for creating an audit log and notifying governance, although the main logic is now implemented.

This list provides a comprehensive overview of the areas in the codebase that require further development.
