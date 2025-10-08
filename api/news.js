let NEWS = [];

export default async function handler(req, res) {
  if (req.method === 'GET') {
    res.status(200).json(NEWS.slice().reverse());
    return;
  }

  if (req.method === 'POST') {
    try {
      const { text, date } = req.body;
      if (!text) return res.status(400).json({ error: 'No text' });
      NEWS.push({
        text,
        date: date || new Date().toISOString(),
      });
      res.status(201).json({ ok: true });
    } catch (e) {
      res.status(400).json({ error: 'Invalid request' });
    }
    return;
  }

  res.status(405).json({ error: 'Method Not Allowed' });
}
