import { useState } from 'react'

export default function App() {
  const [count, setCount] = useState(0)

  return (
    <main className="app">
      <h1>Hello World from React!</h1>
      <p>This React app was built and served from a Docker container.</p>
      <button onClick={() => setCount((c) => c + 1)}>
        Clicked {count} {count === 1 ? 'time' : 'times'}
      </button>
      <p className="hint">
        The counter proves the JavaScript bundle loaded and React is running,
        not just that a static HTML file was served.
      </p>
    </main>
  )
}
