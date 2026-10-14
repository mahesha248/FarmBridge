# 🌱 FarmBridge — Connecting Farmers and Customers

FarmBridge is a Django-based web application that connects farmers directly with customers. Farmers can manage their products and orders, while customers can browse products, add items to their cart, place orders, and view their bills.

The goal is to make the agricultural shopping process simpler and more convenient through a single online platform.

## ✨ Features

### 👨‍🌾 Farmer Portal
- Farmer dashboard
- Add and manage agricultural products
- View listed products
- View customer orders
- Update order statuses
- View sales information
- Manage profile details

### 🛒 Customer Portal
- Customer dashboard
- Browse available products
- Add products to the shopping cart
- Increase or decrease product quantities
- Remove products from the cart
- Checkout and place orders
- View order history and bills
- Track order status
- View payment details
- Manage profile information

### 🔐 Additional Features
- Separate farmer and customer portals
- Database-backed product, cart, and order management
- Email configuration using Gmail SMTP
- Environment-based configuration for sensitive settings

## 🛠️ Technologies Used

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Email:** Gmail SMTP
- **Version Control:** Git and GitHub

## ⚙️ Installation and Setup

### Prerequisites

Install the following before running the project:

- Python
- Git
- Visual Studio Code or another code editor

### 1. Clone the repository

git clone -b Mahesha https://github.com/mahesha248/FarmBridge.git

### 2. Navigate to the project folder

cd FarmBridge

### 3. Create a virtual environment

python -m venv venv

### 4. Activate the virtual environment

**Windows PowerShell:**

.\venv\Scripts\Activate.ps1

### 5. Install dependencies

pip install -r requirements.txt

### 6. Configure environment variables

Create a `.env` file in the project root, alongside `manage.py`.

Add the following configuration using your own local credentials:

SECRET_KEY=your_generated_django_secret_key
DEBUG=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password

Keep `.env` private. Never commit it to GitHub or share its secret values.

### 7. Apply database migrations

python manage.py migrate

### 8. Start the development server

python manage.py runserver

Open the following address in your browser:

http://127.0.0.1:8000/


## 🎯 Project Objective

FarmBridge aims to provide a convenient platform for farmers to showcase their products and for customers to purchase agricultural products through an organized online ordering system.

## 🚀 Future Enhancements

- Complete and test secure online payment gateway integration
- Improve product search and filtering
- Add product image uploads
- Enhance order notifications
- Deploy the application to a production server

## 👨‍💻 Developer

**Mahesha N**

GitHub: [mahesha248](https://github.com/mahesha248)

---

*FarmBridge — Bridging the gap between farmers and customers.*