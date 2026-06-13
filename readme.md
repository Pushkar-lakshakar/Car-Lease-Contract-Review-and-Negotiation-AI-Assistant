# 🚗 Car Lease Analyzer

An AI-powered platform designed to provide intelligence, transparency, and verification for car lease contracts. The system uses OCR to extract data from lease documents, Gemini AI for risk analysis and market price estimation, and a real-time WebSocket-based negotiation system.

## 🌟 Features

- **AI Analysis**: Extracts over 40 fields from lease contracts using OCR and Gemini AI.
- **Market Price Estimation**: Generates accurate market price ranges for vehicles based on VIN and lease signals.
- **Risk Assessment**: Automatically identifies red flags, hidden fees, and unfair lease terms.
- **Negotiation Rooms**: Real-time chat (WebSockets) between Clients and Dealers for lease negotiations.
- **AI Advisor**: Provides context-aware negotiation tips using the Gemini 2.5 Flash model.
- **Vehicle Verification**: Real-time VIN decoding and blacklist status checking via NHTSA integration.
- **Multi-Role Support**: Tailored dashboards for **Clients** and **Dealers**.

## 🛠️ Tech Stack

### Backend

- **Framework**: FastAPI (Python)
- **AI/ML**: Google Gemini 2.5 Flash, GenAI SDK
- **OCR**: Pytesseract & pdf2image
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Communication**: WebSockets (Real-time Messaging)

### Frontend

- **Framework**: Flutter
- **State Management**: Stateful Widgets & API Service
- **Real-time**: web_socket_channel

---

## 🚀 Setup & Installation

### 1. Prerequisites

- Python 3.10+
- Flutter SDK
- PostgreSQL
- Tesseract OCR (System install)
- Poppler (System install for pdf2image)

### 2. Backend Setup

1. Navigate to the Backend folder:
   ```bash
   cd Backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```
3. Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn Backend.main:app --reload --port 8001
   ```

### 3. Frontend Setup

1. Navigate to the Flutter folder:
   ```bash
   cd frontend_flutter
   ```
2. Install dependencies:
   ```bash
   flutter pub get
   ```
3. Run the application:
   ```bash
   flutter run
   ```

---

## 📂 Project Structure

- `Backend/`: FastAPI implementation, AI logic, and DB models.
- `frontend_flutter/`: Multi-platform Flutter UI (Android, iOS, Web).
- `requirements.txt`: Python package requirements.
- `.env`: Environment variables (excluded from Git).

## 🔒 Security Note

This project uses **PostgreSQL** for secure data storage. Ensure your `.env` file is never uploaded to production or version control.

---

## 📝 License

This project is developed as part of the Infosys Springboard internship program.
