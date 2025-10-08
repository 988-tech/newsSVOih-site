const fs = require('fs').promises;
const path = require('path');
const FILE = path.join('/tmp', 'news.json');

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).end();
  try {
    let body = req.body || {};
    if (typeof body === 'string') { try { body = JSON.parse(body); } catch(e){ body = {}; } }
    const msg = body.message || body.channel_post || body.edited_message || body.edited_channel_post;
    if (!msg) return res.status(200).json({ ok: true, note: 'no message' });

    const post = {
      text: msg.text || msg.caption || '',
      date: new Date((msg.date || Math.floor(Date.now()/1000)) * 1000).toISOString(),
      message_id: msg.message_id || null
    };

    let arr = [];
    try {
      const raw = await fs.readFile(FILE, 'utf8');
      arr = JSON.parse(raw || '[]');
      if (!Array.isArray(arr)) arr = [];
    } catch (_) { arr = []; }

    arr.unshift(post);
    if (arr.length > 500) arr = arr.slice(0, 500);
    await fs.writeFile(FILE, JSON.stringify(arr, null, 2), 'utf8');

    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error('telegram handler error', err);
    return res.status(500).json({ error: 'internal' });
  }
};