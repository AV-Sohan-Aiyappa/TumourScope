const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Create a database connection
const dbPath = path.join(__dirname, '..', 'instance', 'tumorscope.db');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error connecting to database:', err.message);
  } else {
    console.log('Connected to the SQLite database for results');
    // Create results table if it doesn't exist
    db.run(`CREATE TABLE IF NOT EXISTS results (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      prediction TEXT NOT NULL,
      confidence REAL NOT NULL,
      timestamp INTEGER NOT NULL,
      original TEXT,
      binary TEXT,
      contours TEXT,
      overlay TEXT,
      is_normal BOOLEAN,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id)
    )`, (err) => {
      if (err) {
        console.error('Error creating results table:', err.message);
      } else {
        console.log('Results table ready');
      }
    });
  }
});

class Result {
  static create(resultData) {
    const { user_id, prediction, confidence, timestamp, original, binary, contours, overlay, is_normal } = resultData;
    
    return new Promise((resolve, reject) => {
      db.run(
        `INSERT INTO results 
        (user_id, prediction, confidence, timestamp, original, binary, contours, overlay, is_normal) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [user_id, prediction, confidence, timestamp, original, binary, contours, overlay, is_normal ? 1 : 0],
        function(err) {
          if (err) {
            reject(err);
          } else {
            resolve({
              id: this.lastID,
              user_id,
              prediction,
              confidence,
              timestamp,
              is_normal
            });
          }
        }
      );
    });
  }

  static findByUserId(userId) {
    return new Promise((resolve, reject) => {
      db.all('SELECT * FROM results WHERE user_id = ? ORDER BY timestamp DESC', [userId], (err, rows) => {
        if (err) {
          reject(err);
        } else {
          // Convert SQLite boolean (0/1) to JavaScript boolean
          const results = rows.map(row => ({
            ...row,
            is_normal: row.is_normal === 1
          }));
          resolve(results);
        }
      });
    });
  }

  static findById(id) {
    return new Promise((resolve, reject) => {
      db.get('SELECT * FROM results WHERE id = ?', [id], (err, row) => {
        if (err) {
          reject(err);
        } else if (row) {
          // Convert SQLite boolean (0/1) to JavaScript boolean
          row.is_normal = row.is_normal === 1;
          resolve(row);
        } else {
          resolve(null);
        }
      });
    });
  }

  static deleteById(id, userId) {
    return new Promise((resolve, reject) => {
      db.run('DELETE FROM results WHERE id = ? AND user_id = ?', [id, userId], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({ deleted: this.changes > 0 });
        }
      });
    });
  }
}

module.exports = Result;