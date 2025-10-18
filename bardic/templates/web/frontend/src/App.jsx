import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import remarkGfm from 'remark-gfm'
import './App.css'
import componentRegistry from './extensions/componentRegistry'

function App() {
  const [passage, setPassage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substring(7))
  const [stories, setStories] = useState([])
  const [selectedStory, setSelectedStory] = useState(null)
  const [showStorySelect, setShowStorySelect] = useState(true)
  const [storiesError, setStoriesError] = useState(null)
  const [showSaveMenu, setShowSaveMenu] = useState(false)
  const [showLoadMenu, setShowLoadMenu] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saves, setSaves] = useState([])
  const [saveMessage, setSaveMessage] = useState(null)

  useEffect(() => {
    loadStories()
  }, [])

  const loadStories = async () => {
    try {
      setStoriesError(null)
      const response = await fetch('http://127.0.0.1:8000/api/stories')

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('Loaded stories:', data.stories.length)
      setStories(data.stories)
    } catch (err) {
      console.error('Failed to load stories:', err)
      setStoriesError(err.message)
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
      console.log('Story started:', data)
      console.log('Render directives:', data.render_directives)
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
      console.log('Choice made:', data)
      console.log('Render directives:', data.render_directives)
      setPassage(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const saveGame = async () => {
    if (!saveName.trim()) {
      setSaveMessage({ type: 'error', text: 'Please enter a save name' })
      return
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/story/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          save_name: saveName
        })
      })

      if (!response.ok) throw new Error('Failed to save game')

      const data = await response.json()
      console.log('Game saved:', data)

      setSaveMessage({ type: 'success', text: `Saved: ${saveName}` })
      setSaveName('')

      // Hide message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000)
    } catch (err) {
      console.error('Save failed', err)
      setSaveMessage({ type: 'error', text: 'Failed to save game' })
    }
  }

  const loadSaves = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/saves/list')

      if (!response.ok) throw new Error('Failed to load saves')

      const data = await response.json()
      console.log('Saves loaded:', data.saves)
      setSaves(data.saves)
    } catch (err) {
      console.error('Failed to load saves:', err)
    }
  }

  const loadGame = async (saveId, storyId) => {
    setLoading(true)
    setShowLoadMenu(false)
    setShowStorySelect(false)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/story/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          save_id: saveId,
          story_id: storyId
        })
      })

      if (!response.ok) throw new Error('Failed to load game')

      const data = await response.json()
      console.log('Game loaded:', data)
      setPassage(data)
      setSaveMessage({ type: 'success', text: `Loaded: ${data.metadata.save_name}` })
      setTimeout(() => setSaveMessage(null), 3000)
    } catch (err) {
      console.error('Load failed:', err)
      setError(err.message)
      setShowStorySelect(true)
    } finally {
      setLoading(false)
    }
  }

  const deleteSave = async (saveId) => {
    if (!confirm('Delete this save?')) return

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/saves/delete/${saveId}`, {
        method: 'DELETE'
      })

      if (!response.ok) throw new Error('Failed to delete save')

      // Refresh save list
      loadSaves()
      setSaveMessage({ type: 'success', text: 'Save deleted' })
      setTimeout(() => setSaveMessage(null), 3000)
    } catch (err) {
      console.error('Delete failed:', err)
      setSaveMessage({ type: 'error', text: 'Failed to delete save' })
    }
  }

  const openSaveMenu = () => {
    setShowSaveMenu(true)
    setSaveName('')
    setSaveMessage(null)
  }

  const openLoadMenu = async () => {
    setShowLoadMenu(true)
    await loadSaves()
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
            {storiesError ? (
              <div className="error">
                <p>Failed to load stories: {storiesError}</p>
                <button onClick={loadStories} className="retry-button">
                  Retry
                </button>
              </div>
            ) : stories.length === 0 ? (
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
              <>
                <button onClick={startStory} className="start-button">
                  Start Story
                </button>
                <button onClick={openLoadMenu} className="load-from-menu-button">
                  Load Saved Game
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (showSaveMenu && passage) {
    return (
      <div className="app">
        <div className="container">
          <header className="app-header">
            <h1>Save Game</h1>
          </header>

          <div className="save-menu">
            <div className="save-form">
              <label htmlFor="saveName">Save Name:</label>
              <input
                id="saveName"
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="e.g., Before boss fight"
                className="save-input"
                autoFocus
              />

              <div className="save-buttons">
                <button onClick={saveGame} className="save-button">
                  Save Game
                </button>
                <button onClick={() => setShowSaveMenu(false)} className="cancel-button">
                  Cancel
                </button>
              </div>
            </div>

            {saveMessage && (
              <div className={`save-message ${saveMessage.type}`}>
                {saveMessage.text}
              </div>
            )}

            <div className="save-info">
              <p><strong>Current Passage:</strong> {passage.passage_id}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Load menu
  if (showLoadMenu) {
    return (
      <div className="app">
        <div className="container">
          <header className="app-header">
            <h1>Load Game</h1>
          </header>

          <div className="load-menu">
            {saves.length === 0 ? (
              <p className="no-saves">No saved games found</p>
            ) : (
              <div className="save-list">
                {saves.map((save) => (
                  <div key={save.save_id} className="save-slot">
                    <div className="save-slot-info">
                      <h3>{save.save_name}</h3>
                      <p className="save-detail">Story: {save.story_name}</p>
                      <p className="save-detail">Passage: {save.passage}</p>
                      <p className="save-date">{save.date_display}</p>
                    </div>
                    <div className="save-slot-actions">
                      <button
                        onClick={() => loadGame(save.save_id, save.story_id)}
                        className="load-button"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => deleteSave(save.save_id)}
                        className="delete-button"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button onClick={() => setShowLoadMenu(false)} className="back-button">
              Back
            </button>

            {saveMessage && (
              <div className={`save-message ${saveMessage.type}`}>
                {saveMessage.text}
              </div>
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

        {/* Render Directives - Custom Components */}
        {passage.render_directives && passage.render_directives.length > 0 && (
          <div className="render-directives">
            {passage.render_directives.map((directive, i) => {
              // Check if there's a React-specific hint
              if (directive.react) {
                const Component = componentRegistry[directive.react.componentName]
                  || componentRegistry.default

                return (
                  <Component
                    key={directive.react.key}
                    {...directive.react.props}
                  />
                )
              }

              // Fallback to generic directive format
              const Component = componentRegistry[directive.name]
                || componentRegistry.default

              return (
                <Component
                  key={i}
                  data={directive.data}
                  name={directive.name}
                />
              )
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
          <div className='footer-buttons'>
            <button onClick={openSaveMenu} className="small-button">
              💾 Save Game
            </button>
            <button onClick={openLoadMenu} className="small-button">
              📁 Load Game
            </button>
            <button onClick={startStory} className="small-button">
              Restart Story
            </button>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
