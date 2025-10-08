const fs = require('fs');
const path = require('path');
const FILE = path.join('/tmp', 'news.json');

module.exports = async (req, res) => {
  try {
    if (!fs.existsSync(FILE)) return res.status(200).json([]);
    const text = fs.readFileSync(FILE, 'utf8');
    try {
      const data = JSON.parse(text || '[]');
      return res.status(200).json(data);
    } catch (e) {
      console.error('Invalid JSON in /tmp/news.json', e);
      return res.status(200).json([]);
    }
  } catch (err) {
    console.error('news handler error', err);
    return res.status(200).json([]);
  }
};
