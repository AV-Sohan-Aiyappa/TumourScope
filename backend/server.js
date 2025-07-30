const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3002;

// Enable CORS
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

// Create permanent storage directory for processed images
const processedDir = path.join(__dirname, 'processed_images');
if (!fs.existsSync(processedDir)) {
  fs.mkdirSync(processedDir);
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'uploads/');
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ storage: storage });

// Serve static files from the processed_images directory
app.use('/processed_images', express.static(path.join(__dirname, 'processed_images')));

// Process image endpoint
app.post('/api/process-image', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image file provided' });
    }

    // Ensure uploads directory exists
    if (!fs.existsSync('uploads')) {
      fs.mkdirSync('uploads', { recursive: true });
    }

    const inputPath = path.resolve(req.file.path);
    const timestamp = Date.now();
    const outputFileName = `processed_${timestamp}.jpg`;
    const outputPath = path.join(processedDir, outputFileName);
    const scriptPath = path.resolve(path.join(__dirname, 'smiley_overlay.py'));

    console.log('Input path:', inputPath);
    console.log('Output path:', outputPath);
    console.log('Script path:', scriptPath);

    // Verify files exist
    if (!fs.existsSync(inputPath)) {
      throw new Error('Input file not found');
    }
    if (!fs.existsSync(scriptPath)) {
      throw new Error('Python script not found');
    }

    // Run the Python script
    await new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', [scriptPath, inputPath, outputPath]);
      
      let errorOutput = '';
      let standardOutput = '';

      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error('Python error:', data.toString());
      });

      pythonProcess.stdout.on('data', (data) => {
        standardOutput += data.toString();
        console.log('Python output:', data.toString());
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script exited with code ${code}\nError: ${errorOutput}`));
        } else {
          resolve(standardOutput);
        }
      });
    });

    // Verify output file exists
    if (!fs.existsSync(outputPath)) {
      throw new Error('Output file was not created');
    }

    // Clean up input file
    try {
      fs.unlinkSync(inputPath);
    } catch (err) {
      console.error('Error cleaning up input file:', err);
    }

    res.json({
      processedImageUrl: `/processed_images/${outputFileName}`,
      timestamp: timestamp
    });
  } catch (error) {
    console.error('Error processing image:', error);
    res.status(500).json({ error: 'Failed to process image', details: error.message });
  }
});

// Get all processed images endpoint
app.get('/api/get-processed-images', (req, res) => {
  try {
    fs.readdir(processedDir, (err, files) => {
      if (err) {
        console.error('Error reading processed images directory:', err);
        return res.status(500).json({ error: 'Failed to fetch processed images' });
      }

      const images = files
        .filter(file => file.startsWith('processed_') && file.endsWith('.jpg'))
        .map(file => {
          const timestamp = parseInt(file.split('_')[1].split('.')[0]);
          return {
            url: `/processed_images/${file}`,
            timestamp: timestamp
          };
        })
        .sort((a, b) => b.timestamp - a.timestamp); // Sort by newest first

      res.json({ images });
    });
  } catch (error) {
    console.error('Error fetching processed images:', error);
    res.status(500).json({ error: 'Failed to fetch processed images' });
  }
});

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

// Start server with error handling
const startServer = () => {
  const server = app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
  }).on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.log(`Port ${port} is busy, trying ${port + 1}`);
      app.listen(port + 1);
    } else {
      console.error('Server error:', err);
    }
  });
};

startServer(); 