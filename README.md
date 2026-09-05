#  Ocular AI - Disease Screening System

An AI-powered ocular disease screening platform built with Django and PyTorch. This system utilizes a trained EfficientNet-B3 machine learning model to analyze fundus images, featuring Explainable AI (XAI) Grad-CAM heatmaps, a Gemini-powered medical chatbot, and automated PDF reporting.

---

##  Key Features
*   **AI Disease Screening:** Multi-class classification of ocular diseases using PyTorch.
*   **Explainable AI (XAI):** Visualizes model attention using Grad-CAM heatmaps to assist clinicians.
*   **Medical Chatbot:** Integrated with Google Gemini API for contextual patient and clinician support.
*   **PDF Reporting:** Automated generation of downloadable diagnostic reports.
*   **Feedback Module:** Integrated user feedback system for continuous improvement.

##  Prerequisites
Before installing, ensure your system meets the following requirements:
*   [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.
*   [Git](https://git-scm.com/) installed.
*   At least **4GB of available RAM** allocated to Docker (required for loading the PyTorch tensor models into memory).

---

##  Installation & Setup Guide

### Step 1: Clone the Repository
Open your terminal and clone this project to your local machine:
```bash
git clone [https://github.com/Xeeshan-23/ocular_project.git](https://github.com/Xeeshan-23/ocular_project.git)
cd ocular_project

Step 2: Configure Environment Variables
The system requires secure API keys to run. Create a file named .env in the root directory (at the same level as manage.py) and add the following secure variables:
# .env file
DEBUG=True
SECRET_KEY=your_django_secret_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here

Step 3: Build and Launch the Containers
This project uses Docker Compose to orchestrate the Python environment, install heavy ML dependencies (PyTorch, torchvision), and link the PostgreSQL database seamlessly.

Run this command in your terminal:
docker compose up --build -d

Step 4: Database Migrations
Once the containers are running, you must apply the database schema (including Patient Profiles, Screening Results, and the Feedback Module) to the PostgreSQL container:
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

Step 5: Create an Administrator Account
To access the Admin Dashboard and review system feedback, create a superuser account:
docker compose exec web python manage.py createsuperuser

Accessing the Application
The system is now fully deployed and running locally in your Docker containers!

* **Main Application Dashboard: Open your browser and navigate to http://localhost:8000**
* **Admin Control Panel: Navigate to http://localhost:8000/admin**

Running Automated Tests
To verify system integrity and validate the MVT architecture and security protocols, run the automated test suite:
Bash
docker compose exec web python manage.py test core

###
``` Email: mzeeshansadiq@outlook.com | to get the model file.
###


