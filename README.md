# PeerView – Anonymous Peer Review Platform 🎓

PeerView is a full-stack web application designed to foster honest, constructive feedback among students and peers. By enforcing strict anonymity for reviews while maintaining a secure, role-based moderation backend, PeerView creates a safe space for academic and project collaboration.

## Key Features

* **Secure Authentication:** JWT-based user login and registration with secure password hashing.
* **Role-Based Access Control (RBAC):** Distinct privileges for standard 'Students' and administrative 'Admins'.
* **Anonymity Engine:** Backend data-masking ensures reviews appear as "Anonymous Peer" to the public, while preserving true identities in the database for moderation.
* **Multimedia Feed:** Support for rich text posts, image uploads, and PDF document attachments.
* **Interactive Engagement:** Real-time upvoting, downvoting, and asynchronous feed updates.
* **Moderation Dashboard:** Admins can view flagged content, unmask true identities, and permanently remove inappropriate reviews.
* **Optimized Data Loading:** Integrated server-side pagination to efficiently handle large data sets.

## Technology Stack

**Frontend (Client)**
* HTML5 / CSS3 (Custom Responsive UI, Dark/Light Mode)
* Vanilla JavaScript (ES6+, asynchronous `fetch` API, DOM manipulation)

**Backend (Server)**
* Python 3
* Flask (RESTful API architecture)
* Werkzeug (Secure file handling and cryptographic hashing)
* PyJWT (Stateless token authentication)

**Database**
* SQLite3 (Relational database management)

## Project Structure

```text
PeerView/
├── backend/
│   ├── app.py                 # Main Flask server application
│   ├── database.py            # SQLite connection and table creation
│   └── api/
│       ├── auth.py            # Login, registration, and profile routes
│       ├── posts.py           # Feed generation, pagination, and file uploads
│       ├── interactions.py    # Voting, comments, and moderation logic
│       └── middleware.py      # JWT security and token verification
├── frontend/
│   ├── index.html             # Main application interface
│   ├── style.css              # Global styles and theme variables
│   └── app.js                 # Frontend logic, API calls, and state management
└── uploads/                   # Secure local storage for user media