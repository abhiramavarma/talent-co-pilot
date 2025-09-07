import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import MainPage from './components/MainPage';

const App: React.FC = () => {
  const [page, setPage] = useState<'landing' | 'main'>('landing');

  const navigateToMain = () => {
    setPage('main');
  };

  return (
    <div className="bg-white">
      {page === 'landing' ? (
        <LandingPage onNavigate={navigateToMain} />
      ) : (
        <MainPage />
      )}
    </div>
  );
};

export default App;
