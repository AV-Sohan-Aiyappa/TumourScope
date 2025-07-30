const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const { PythonShell } = require('python-shell');
const fs = require('fs');
const bodyParser = require('body-parser');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Ensure required environment variables are set
if (!process.env.PYTHON_API_KEY) {
  console.warn('Warning: PYTHON_API_KEY environment variable is not set. Using default value.');
  process.env.PYTHON_API_KEY = 'tumorscope_secure_api_key_2023';
}

// Import routes
const authRoutes = require('./backend/routes/auth');
const resultsRoutes = require('./backend/routes/results');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.use(cors());
app.use(express.json());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files
app.use('/uploads', express.static('uploads'));
app.use('/processed', express.static('processed'));

// Use routes
app.use('/api/auth', authRoutes);
app.use('/api/results', resultsRoutes);

app.post('/api/process-image', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image file uploaded' });
    }

    const inputPath = path.resolve(req.file.path);
    const outputPath = path.resolve(path.join('uploads', `processed_${req.file.filename}.jpg`));
    const scriptPath = path.resolve(path.join(__dirname, 'smiley_overlay.py'));

    console.log('Input path:', inputPath);
    console.log('Output path:', outputPath);
    console.log('Script path:', scriptPath);

    // Run the Python script
    let options = {
      mode: 'text',
      pythonPath: 'python',
      pythonOptions: ['-u'],
      scriptPath: scriptPath,
      args: [inputPath, outputPath]
    };

    await new Promise((resolve, reject) => {
      PythonShell.run(scriptPath, options, function (err, output) {
        if (err) {
          console.error('Python error:', err);
          reject(err);
        } else {
          console.log('Python output:', output);
          resolve();
        }
      });
    });

    res.json({
      processedImageUrl: `/uploads/${path.basename(outputPath)}`
    });
  } catch (error) {
    console.error('Error processing image:', error);
    res.status(500).json({ error: 'Failed to process image', details: error.message });
  }
});

// Create necessary directories if they don't exist
const directories = ['uploads', 'processed', 'backend/instance'];
directories.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`Created directory: ${dir}`);
  }
});

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});