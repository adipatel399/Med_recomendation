import React from 'react';
import './LandingPage.css';
import symptomChecker from './image/symptom_checker.png';


function LandingPage({ onStart }) {
  return (
    <div className="landing-bg">
      <nav className="landing-nav">
        <span className="nav-logo">🩺 Health AI</span>
      </nav>
      <div className="landing-hero">
        <div className="hero-content">
          <h1>
            Your Personalized <span className="highlight">Health Assistant</span>
          </h1>
          <p>
            Get instant AI-powered health recommendations, a smart calendar, and nearby pharmacy info—all in one place.
          </p>
          <button className="hero-btn" onClick={onStart}>
            Start Health Check
          </button>
        </div>
        <img
          src="https://img.icons8.com/fluency/240/medical-doctor.png"
          alt="Doctor"
          className="hero-img"
        />
      </div>
      <section className="features">
      <div className="feature-card">
        <img
        src={symptomChecker}
        alt="Symptom Checker"
        />
        <h3>Symptom Checker</h3>
        <p>Describe your symptoms and get quick, AI-driven insights.</p>
        </div>

        <div className="feature-card">
          <img src="https://img.icons8.com/color/48/pill.png" alt="Medication" />
          <h3>Personalized Plans</h3>
          <p>Receive tailored medication, diet, and workout suggestions.</p>
        </div>
        <div className="feature-card">
          <img src="https://img.icons8.com/color/48/calendar.png" alt="Calendar" />
          <h3>Health Calendar</h3>
          <p>Visualize your health journey and set daily reminders.</p>
        </div>
        <div className="feature-card">
          <img src="https://img.icons8.com/color/48/pharmacy-shop.png" alt="Pharmacies" />
          <h3>Nearby Pharmacies</h3>
          <p>Find trusted medical stores close to your location.</p>
        </div>
      </section>
      <footer className="landing-footer">
        <p>&copy; {new Date().getFullYear()} Health AI. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default LandingPage;
