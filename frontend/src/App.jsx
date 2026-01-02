import { useState } from 'react';
import axios from 'axios';
import './index.css';

function App() {
  // --- STATE ---
  const [appMode, setAppMode] = useState('landing');
  const [topicInput, setTopicInput] = useState('');
  const [fullCurriculum, setFullCurriculum] = useState(null);
  const [activeModules, setActiveModules] = useState([]);
  const [currentModuleIndex, setCurrentModuleIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  // --- HANDLERS ---

  // Handle topic search submission
  const handleTopicSubmit = async (e) => {
    e.preventDefault();
    if (!topicInput.trim()) return;

    setLoading(true);
    try {
      const response = await axios.get(`http://127.0.0.1:8000/generate_course?topic=${encodeURIComponent(topicInput)}`);
      setFullCurriculum(response.data);
      // By default, ALL modules are selected
      setActiveModules(response.data.modules);
      setAppMode('setup');
      setLoading(false);
    } catch (error) {
      console.error('Error generating course:', error);
      setLoading(false);
    }
  };

  // Toggle a module ON or OFF during setup
  const toggleModule = (module) => {
    if (activeModules.find(m => m.id === module.id)) {
      setActiveModules(activeModules.filter(m => m.id !== module.id));
    } else {
      // Add it back in the correct order (by ID)
      const newList = [...activeModules, module].sort((a, b) => a.id - b.id);
      setActiveModules(newList);
    }
  };

  // Start the Course
  const startCourse = () => {
    if (activeModules.length === 0) return alert("Select at least one module!");
    setAppMode('learning');
    setCurrentModuleIndex(0);
    setActiveIndex(0);
  };

  // Move to next module
  const handleNextModule = () => {
    const container = document.querySelector('.app-container');
    if (container) container.scrollTop = 0; // Reset scroll
    
    // Increment to next module (or beyond to trigger completion)
    setCurrentModuleIndex((prev) => prev + 1);
    setActiveIndex(0);
  };

  // Handle scroll to track active video
  const handleScroll = (e) => {
    const index = Math.round(e.target.scrollTop / window.innerHeight);
    if (index !== activeIndex) setActiveIndex(index);
  };

  // Reset to landing mode
  const resetToLanding = () => {
    setAppMode('landing');
    setTopicInput('');
    setFullCurriculum(null);
    setActiveModules([]);
    setCurrentModuleIndex(0);
    setActiveIndex(0);
  };

  // --- RENDER: LANDING MODE ---
  if (appMode === 'landing') {
    return (
      <div className="landing-container">
        <h1>MicroLearn</h1>
        <form onSubmit={handleTopicSubmit}>
          <input
            type="text"
            value={topicInput}
            onChange={(e) => setTopicInput(e.target.value)}
            placeholder="Enter a topic to learn..."
            disabled={loading}
            className="topic-input"
          />
          <button type="submit" disabled={loading} className="search-btn">
            {loading ? 'Generating...' : 'Start Learning'}
          </button>
        </form>
      </div>
    );
  }

  // --- RENDER: SETUP MODE ---
  if (appMode === 'setup') {
    if (loading) {
      return <div className="status-msg">Designing Curriculum...</div>;
    }

    return (
      <div className="setup-container">
        <h1>Curriculum Builder</h1>
        <p className="subtitle">Topic: <strong>{fullCurriculum?.topic}</strong></p>
        <p className="instruction">Uncheck topics you already know:</p>

        <div className="module-list">
          {fullCurriculum?.modules.map((mod) => {
            const isSelected = activeModules.find(m => m.id === mod.id);
            return (
              <div
                key={mod.id}
                className={`module-item ${isSelected ? 'selected' : 'ignored'}`}
                onClick={() => toggleModule(mod)}
              >
                <div className="checkbox">{isSelected ? '✔' : ''}</div>
                <div className="module-info">
                  <h3>{mod.title}</h3>
                  <p>{mod.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="footer-bar">
          <p>{activeModules.length} Modules Selected</p>
          <button className="start-btn" onClick={startCourse}>Let's Go →</button>
        </div>
      </div>
    );
  }

  // --- RENDER: LEARNING MODE ---

  // Check if course is finished
  if (currentModuleIndex >= activeModules.length) {
    return (
      <div className="status-msg">
        <h1>🎉 Course Complete!</h1>
        <div className="completion-recap">
          <h2>What You Learned:</h2>
          <div className="recap-modules">
            {activeModules.map((module, index) => (
              <div key={module.id} className="recap-module-item">
                <span className="recap-number">{index + 1}</span>
                <div className="recap-module-info">
                  <h3>{module.title}</h3>
                  {module.description && <p>{module.description}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
        <form onSubmit={handleTopicSubmit} className="completion-form">
          <input
            type="text"
            value={topicInput}
            onChange={(e) => setTopicInput(e.target.value)}
            placeholder="Enter a topic to learn..."
            disabled={loading}
            className="topic-input"
          />
          <button type="submit" disabled={loading} className="search-btn">
            {loading ? 'Generating...' : 'Start Learning'}
          </button>
        </form>
      </div>
    );
  }

  const currentModule = activeModules[currentModuleIndex];
  const progressPercent = ((currentModuleIndex + 1) / activeModules.length) * 100;

  return (
    <div className="app-container" onScroll={handleScroll}>
      {/* --- PROGRESS HEADER (FIXED) --- */}
      <div className="module-header">
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progressPercent}%` }}></div>
        </div>
        <div className="header-text">
          <span className="step-count">Step {currentModuleIndex + 1} of {activeModules.length}</span>
          <h3>{currentModule.title}</h3>
        </div>
      </div>

      {/* --- VIDEOS --- */}
      {currentModule.videos.map((videoId, index) => {
        const shouldPlay = index === activeIndex;
        return (
          <div key={index} className="video-card">
            <iframe
              src={`https://www.youtube.com/embed/${videoId}?autoplay=${shouldPlay ? 1 : 0}&mute=0&controls=1&playsinline=1&rel=0&loop=1&playlist=${videoId}`}
              width="100%"
              height="100%"
              title={`video-${index}`}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        );
      })}

      {/* --- NEXT BUTTON --- */}
      <button className="next-level-btn" onClick={handleNextModule}>
        Mark as Understood →
      </button>
    </div>
  );
}

export default App;
