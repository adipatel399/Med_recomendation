import React, { useState } from 'react';
import LandingPage from './LandingPage';
import MainApp from './MainApp';
import './App.css';


function App() {
  const [started, setStarted] = useState(false);

  return (
    <>
      {started
        ? <MainApp onBack={() => setStarted(false)} />
        : <LandingPage onStart={() => setStarted(true)} />}
    </>
  );
}

export default App;

