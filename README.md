# MavTourneyBracket
MavLab's Tournament Bracket Repository. 

# MavTourneyBracket  
*A Modern, Open-Source Tournament Bracket System for Student Organizations*

---

## Overview

**MavTourneyBracket** is an open-source tournament bracket management system developed by **MavLabs** to support student organizations, academic competitions, esports events, and research-driven experimentation in software engineering and cybersecurity.

The project is designed to serve three primary purposes:

1. **A real-world software engineering portfolio project**
2. **A teaching and learning platform for student developers**
3. **A research and experimentation environment for system design and security**

MavTourneyBracket aims to demonstrate professional-grade development practices while remaining accessible to student contributors.

---

## Key Features

- Create and manage tournaments
- Support for multiple bracket types:
  - Single elimination
  - Double elimination (planned)
  - Round-robin (planned)
- Team and participant management
- Administrative dashboard
- Role-based access control (planned)
- Responsive web interface
- API-first architecture (in progress)

---

## Tech Stack

| Layer | Technology |
|------|------------|
| Backend | Django (Python) |
| Frontend | HTML, CSS, JavaScript (React optional) |
| Database | SQLite (development), PostgreSQL (planned) |
| Auth | Django Auth / AllAuth |
| Hosting | Docker / Cloud (planned) |

---

## Intended Use

This project is designed for:

- Student organizations running events
- Faculty hosting classroom competitions
- Esports clubs and hackathons
- Research teams exploring system design
- Developers building portfolio projects

It is intentionally built to be:
- readable
- extensible
- well-documented
- safe for experimentation

---

## Screenshots / Demo

*(Coming soon — deployment and demo instances planned)*

---

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- Virtual environment tool (`venv`, `pipenv`, or `poetry`)

### Installation

```bash
git clone https://github.com/UNO-MavLabs/MavTourneyBracket.git
cd MavTourneyBracket
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
