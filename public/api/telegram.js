const fs = require('fs');
const path = require('path');

const FILE = path.join('/tmp', 'news.json');

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).end();

  // тело уже распарсено Vercel (JSON)
  const body = req.body || {};
  const msg = body.message || body.channel_post || body.edited_message || body.edited_channel_post;
  if (!msg) return res.status(200).json({ ok: true, note: 'no message' });

  // принимаем посты из канала (если нужно — измените условие)
  const chatType = (msg.chat && msg.chat.type) || '';
  if (chatType !== 'channel' && !(msg.sender_chat && msg.sender_chat.type === 'channel')) {
    return res.status(200).json({ ok: true, note: 'ignored non-channel' });
  }

  const post = {
    text: msg.text || msg.caption || '',
    date: new Date((msg.date || Math.floor(Date.now()/1000)) * 1000).toISOString(),
    message_id: msg.message_id || null
  };

  try {
    let arr = [];
    if (fs.existsSync(FILE)) {
      try { arr = JSON.parse(fs.readFileSync(FILE, 'utf8') || '[]'); } catch (e) { arr = []; }
    }
    arr.unshift(post);
    if (arr.length > 500) arr = arr.slice(0, 500);
    fs.writeFileSync(FILE, JSON.stringify(arr, null, 2), 'utf8');
    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error('telegram handler error', err);
    return res.status(500).json({ error: 'internal' });
  }
};
