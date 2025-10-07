import { useState, useEffect } from 'react'
import './App.css'

function App() {
  // State holds data that can change
  const [passage, setPassage] = useState(null) // Current passage's content
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Generate a random session id
  // In a real app, this would be smarter
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substring(7))

  // This runs when the component first loads
  useEffect(() => {
    startStory()
  }, [])

  // Function to start the story
  const startStory = async () => {
    setLoading(true)
    setError(null)

    try {
      // Make a POST request to your API
      const response = await fetch('http://127.0.0.1:8000/api/story/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          story_id: 'test_adventure', // We will make this dynamic later
          session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start story')
      }

      const data = await response.json()
      setPassage(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const makeChoice = async (choiceIndex) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/story/choose', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          choice_index: choiceIndex
        })
      })

      if (!response.ok) {
        throw new Error('Failed to make choice')
      }

      const data = await response.json()
      setPassage(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Show loading state
  if (loading && !passage) {
    return (
      <div className="app">
        <div className="loading">Loading story...</div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="app">
        <div className="error">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={startStory}>Try Again</button>
        </div>
      </div>
    )
  }

  // Show passage
  if (!passage) {
    return (
      <div className="app">
        <div className="loading">Starting...</div>
      </div>
    )
  }

  return (
    <div className='app'>
      <header className='app-header'>
        <h1>Bardic Story Player</h1>
        <p className='passage-id'>Current: {passage.passage_id}</p>
      </header>
      <main className='story-content'>
        <div className='passage'>
          {/* Split content by newlines and render as paragraphs */}
          {passage.content.split('\n\n').map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
        </div>
        {passage.is_end ? (
          <div className="ending">
            <h2>The End</h2>
            <button onClick={startStory} className="restart-button">
              Start Over
            </button>
          </div>
        ) : (
          <div className="choices">
            <h3>What do you do?</h3>
            {passage.choices.map((choice) => (
              <button
                key={choice.index}
                onClick={() => makeChoice(choice.index)}
                disabled={loading}
                className="choice-button"
              >
                {choice.text}
              </button>
            ))}
          </div>
        )}
      </main>
      <footer className="app-footer">
        <button onClick={startStory} className="small-button">
          Restart Story
        </button>
      </footer>
    </div>
  )
}

export default App
