// A small in-memory Task API — a real application, not just a static page.
const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

let tasks = [
  { id: 1, title: 'Learn Docker', done: true },
  { id: 2, title: 'Write a multi-stage Dockerfile', done: true },
  { id: 3, title: 'Deploy three applications', done: false },
];
let nextId = 4;

app.get('/', (req, res) => {
  res.send(`<!doctype html>
<html><head><title>Node.js Task API</title></head>
<body style="font-family: system-ui, sans-serif; padding: 40px; max-width: 640px; margin: auto;">
  <h1>Node.js Task API</h1>
  <p>Deployed with Docker. Node ${process.version}</p>
  <ul>
    <li><code>GET    /tasks</code> — list all tasks</li>
    <li><code>GET    /tasks/:id</code> — one task</li>
    <li><code>POST   /tasks</code> — create <code>{"title":"..."}</code></li>
    <li><code>DELETE /tasks/:id</code> — delete</li>
    <li><code>GET    /health</code> — health check</li>
  </ul>
</body></html>`);
});

app.get('/tasks', (req, res) => res.json(tasks));

app.get('/tasks/:id', (req, res) => {
  const task = tasks.find((t) => t.id === Number(req.params.id));
  if (!task) return res.status(404).json({ error: 'not found' });
  res.json(task);
});

app.post('/tasks', (req, res) => {
  const { title } = req.body || {};
  if (!title) return res.status(400).json({ error: 'title is required' });
  const task = { id: nextId++, title, done: false };
  tasks.push(task);
  res.status(201).json(task);
});

app.delete('/tasks/:id', (req, res) => {
  const before = tasks.length;
  tasks = tasks.filter((t) => t.id !== Number(req.params.id));
  if (tasks.length === before) return res.status(404).json({ error: 'not found' });
  res.status(204).end();
});

app.get('/health', (req, res) => res.json({ status: 'ok', uptime: process.uptime() }));

app.listen(PORT, '0.0.0.0', () => console.log(`Task API listening on ${PORT}`));
