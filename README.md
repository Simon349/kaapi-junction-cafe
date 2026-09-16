# Kaapi Junction — Coffee Cafe Website

A full coffee-cafe website with a public front-end and an admin panel,
built with **Flask** (Python) + SQLite. Every important action (page
visits, form submissions, admin logins, menu edits) is also printed to
the terminal so you can watch the app work while it runs.

## What's included

- **Public site**: Home (hero + specials + story + testimonials), Menu
  (pulled live from the database, grouped by category), Our Story,
  and Contact (with a working reservation/message form).
- **Admin panel** (`/admin/login`): dashboard with stats, full CRUD for
  menu items (add / edit / delete / mark available / mark as special),
  and an inbox for messages submitted through the contact form.
- **SQLite database** (`cafe.db`), created automatically on first run
  and seeded with a starter menu.
- **Terminal logging**: every page view, form submission, login, and
  admin action prints a timestamped line to your terminal.

## Setup

1. Make sure you have Python 3.9+ installed.
2. Open a terminal in this folder and create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open your browser:
   - Website: http://127.0.0.1:5000/
   - Admin panel: http://127.0.0.1:5000/admin/login

## Default admin login

```
Username: admin
Password: kaapi123
```

The account is created automatically the first time you run the app.
**Change this password** (or edit the `seed_data()` function in
`app.py`) before putting this anywhere public.

## Project structure

```
cafe-website/
├── app.py                  # Flask app: routes, models, admin logic
├── requirements.txt
├── cafe.db                 # created automatically on first run
├── templates/
│   ├── base.html            # shared header/nav/footer for public pages
│   ├── index.html           # home page
│   ├── menu.html            # menu page (reads from DB)
│   ├── about.html           # our story page
│   ├── contact.html         # contact / reservation form
│   └── admin/
│       ├── login.html
│       ├── admin_base.html  # shared admin sidebar layout
│       ├── dashboard.html
│       ├── menu_list.html
│       ├── item_form.html   # shared add/edit form
│       └── messages.html
└── static/
    ├── css/style.css        # full design system
    └── js/script.js         # nav toggle, flash auto-dismiss, confirm dialogs
```

## Customizing

- **Menu items**: manage them entirely from the admin panel — no code
  changes needed. Categories are free text, so typing a new category
  name in the form creates it.
- **Cafe name, address, phone, hours**: edit the text directly in
  `templates/base.html` (footer) and `templates/contact.html`.
- **Colors and fonts**: all design tokens are CSS variables at the top
  of `static/css/style.css` (`:root { ... }`).
- **Reset the database**: stop the server, delete `cafe.db`, and
  restart — it will be recreated and reseeded automatically.

## Notes

- This uses Flask's built-in development server, which is fine for
  local use and demos. For a real deployment, run it behind a
  production WSGI server (e.g. gunicorn) and set a proper
  `SECRET_KEY` in `app.py`.
