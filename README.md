# TumourScope

A web application for breast cancer detection using image analysis. This project consists of a React frontend, Node.js backend, and Python image processing.

## Prerequisites

- Node.js (v14 or higher)
- Python (v3.6 or higher)
- npm or yarn package manager

## Python Dependencies

```bash
pip install opencv-python numpy
```

## Project Structure

```
TumourScope/
├── frontend/          # React frontend
├── backend/           # Node.js backend and API
│   ├── models/        # Database models
│   ├── routes/        # API routes
│   ├── middleware/    # Authentication middleware
│   ├── instance/      # SQLite database
│   └── app.py         # Python backend for image processing
├── smiley_overlay.py  # Python image processing script
└── README.md
```

## Data Flow

1. User uploads an image through the React frontend
2. The image is sent to the Python backend (`/api/detect`) for processing
3. The Python backend analyzes the image using machine learning
4. The Python backend saves the results to the Node.js database via the `/api/results/save` endpoint
5. The frontend displays the results to the user
6. Users can view their history of analyzed images from the database

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd TumourScope
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Install backend dependencies:
```bash
cd ../backend
npm install
```

## Running the Application

1. Start the backend server:
```bash
cd backend
npm run dev
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Start the Python backend:
```bash
cd backend
python app.py
```

4. Open your browser and navigate to `http://localhost:5173`


```

## Features

- Home page with breast cancer information and statistics
- Image upload for analysis
- View analysis history
- Real-time image processing
- Responsive design with smooth animations
- Persistent storage of analysis results in database
- Secure communication between Python and Node.js backends

## Tech Stack

- Frontend:
  - React
  - TypeScript
  - Chakra UI
  - Framer Motion
  - Axios

- Backend:
  - Node.js
  - Express
  - Python (OpenCV, NumPy)
  - SQLite database
  - Multer for file uploads
  - JWT for authentication

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request