const express = require('express');
const router = express.Router();
const Result = require('../models/Result');
const auth = require('../middleware/auth');

// @route   GET /api/results
// @desc    Get all results for the authenticated user
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    const results = await Result.findByUserId(req.userId);
    res.json(results);
  } catch (error) {
    console.error('Error fetching results:', error);
    res.status(500).json({ error: 'Server error while fetching results' });
  }
});

// @route   GET /api/results/:id
// @desc    Get a specific result by ID
// @access  Private
router.get('/:id', auth, async (req, res) => {
  try {
    const result = await Result.findById(req.params.id);
    
    if (!result) {
      return res.status(404).json({ error: 'Result not found' });
    }
    
    // Check if the result belongs to the authenticated user
    if (result.user_id !== req.userId) {
      return res.status(403).json({ error: 'Not authorized to access this result' });
    }
    
    res.json(result);
  } catch (error) {
    console.error('Error fetching result:', error);
    res.status(500).json({ error: 'Server error while fetching result' });
  }
});

// @route   DELETE /api/results/:id
// @desc    Delete a result
// @access  Private
router.delete('/:id', auth, async (req, res) => {
  try {
    const result = await Result.deleteById(req.params.id, req.userId);
    
    if (!result.deleted) {
      return res.status(404).json({ error: 'Result not found or not authorized to delete' });
    }
    
    res.json({ success: true, message: 'Result deleted successfully' });
  } catch (error) {
    console.error('Error deleting result:', error);
    res.status(500).json({ error: 'Server error while deleting result' });
  }
});

// @route   POST /api/results/save
// @desc    Save a result from the Python backend
// @access  Public (but requires API key for security)
router.post('/save', async (req, res) => {
  try {
    // Check for API key (simple security measure)
    const apiKey = req.headers['x-api-key'];
    if (!apiKey || apiKey !== process.env.PYTHON_API_KEY) {
      return res.status(401).json({ error: 'Unauthorized: Invalid API key' });
    }

    // Validate required fields
    const { user_id, prediction, confidence, timestamp, original, binary, contours, overlay, is_normal } = req.body;
    
    if (!user_id || !prediction || confidence === undefined || !timestamp) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Create the result in the database
    const result = await Result.create({
      user_id,
      prediction,
      confidence,
      timestamp,
      original,
      binary,
      contours,
      overlay,
      is_normal
    });

    res.status(201).json({
      success: true,
      message: 'Result saved successfully',
      result_id: result.id
    });
  } catch (error) {
    console.error('Error saving result:', error);
    res.status(500).json({ error: 'Server error while saving result' });
  }
});

module.exports = router;