import React, { useState } from 'react';

const Upload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
      const response = await fetch('http://localhost:3002/api/process-image', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.details || 'Failed to process image');
      }

      const data = await response.json();
      setProcessedImage(`http://localhost:3002${data.processedImageUrl}`);
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div>
      <h1>Upload Image</h1>
      <div style={{ marginBottom: '20px' }}>
        <input 
          type="file" 
          accept="image/*" 
          onChange={handleFileSelect}
          style={{ marginBottom: '10px' }}
        />
        <br />
        <button onClick={handleUpload} disabled={!selectedFile}>
          Process Image
        </button>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          Error: {error}
        </div>
      )}

      {processedImage && (
        <div>
          <h2>Processed Image</h2>
          <img 
            src={processedImage} 
            alt="Processed" 
            style={{ 
              maxWidth: '100%', 
              marginTop: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }} 
          />
        </div>
      )}
    </div>
  );
};

export default Upload; 