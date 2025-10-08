const fs = require('fs').promises;
const path = require('path');
const FILE = path.join('/tmp', 'news.json');

module.exports = async (req, res) => {
  try {
    try {
      const raw = await fs.readFile(FILE, 'utf8');
      const data = JSON.parse(raw || '[]');
      return res.status(200).json(Array.isArray(data) ? data : []);
    } catch (e) {
      return res.status(200).json([]);
    }
  } catch (err) {
    console.error('news handler error', err);
    return res.status(200).json([]);
  }
};
