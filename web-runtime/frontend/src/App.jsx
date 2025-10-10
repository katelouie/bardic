import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import remarkGfm from 'remark-gfm'
import './App.css'

function App() {
  const [passage, setPassage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substring(7))
  const [stories, setStories] = useState([])
  const [selectedStory, setSelectedStory] = useState(null)
  const [showStorySelect, setShowStorySelect] = useState(true)

  useEffect(() => {
    loadStories()
  }, [])

  const loadStories = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/stories')
      const data = await response.json()
      setStories(data.stories)
    } catch (err) {
      console.error('Failed to load stories', err)
    }
  }

  const startStory = async () => {
    if (!selectedStory) return

    setLoading(true)
    setError(null)
    setShowStorySelect(false)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/story/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_id: selectedStory,
          session_id: sessionId
        })
      })

      if (!response.ok) throw new Error('Failed to start story')

      const data = await response.json()
      setPassage(data)
    } catch (err) {
      setError(err.message)
      setShowStorySelect(true)
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          choice_index: choiceIndex
        })
      })

      if (!response.ok) throw new Error('Failed to make choice')

      const data = await response.json()
      setPassage(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Loading state
  if (loading && !passage) {
    return (
      <div className="app">
        <div className="loading">Loading story...</div>
      </div>
    )
  }

  // Error state
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

  // Story selection screen
  if (showStorySelect) {
    return (
      <div className="app">
        <div className="container">
          <header className="app-header">
            <h1>Bardic Story Player</h1>
            <p>Choose a story to begin</p>
          </header>

          <div className="story-select">
            <h2>Available Stories</h2>
            {stories.length === 0 ? (
              <p>Loading stories...</p>
            ) : (
              <div className="story-list">
                {stories.map((story) => (
                  <button
                    key={story.id}
                    onClick={() => setSelectedStory(story.id)}
                    className={`story-button ${selectedStory === story.id ? 'selected' : ''}`}
                  >
                    {story.name}
                  </button>
                ))}
              </div>
            )}
            {selectedStory && (
              <button onClick={startStory} className="start-button">
                Start Story
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Starting state
  if (!passage) {
    return (
      <div className="app">
        <div className="loading">Starting...</div>
      </div>
    )
  }

  // Story playthrough
  return (
    <div className="app">
      <div className="container">
        <header className="app-header">
          <h1>Bardic Story Player</h1>
          <p className="passage-id">Current: {passage.passage_id}</p>
        </header>

        <div className="passage">
          <ReactMarkdown rehypePlugins={[rehypeRaw]} remarkPlugins={[remarkGfm]}>
            {passage.content}
          </ReactMarkdown>
        </div>

        {passage.render_directives && passage.render_directives.length > 0 && (
          <div className="render-directives">
            {passage.render_directives.map((directive, i) => {
              const Component = componentRegistry[directive.component] || componentRegistry.default
              return <Component key={i} {...directive.props} />
            })}
          </div>
        )}

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

        <footer className="app-footer">
          <button onClick={startStory} className="small-button">
            Restart Story
          </button>
        </footer>
      </div>
    </div>
  )
}

export default App
