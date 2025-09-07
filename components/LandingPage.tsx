import React, { useState } from 'react';

interface LandingPageProps {
  onNavigate: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const [isAboutModalOpen, setAboutModalOpen] = useState(false);
  const [isFeaturesModalOpen, setFeaturesModalOpen] = useState(false);

  const Modal: React.FC<{ title: string; children: React.ReactNode; onClose: () => void }> = ({ title, children, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-2xl transform transition-all" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-2xl font-bold text-gray-900">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="text-gray-600 space-y-4 max-h-[70vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="relative min-h-screen w-full flex flex-col items-center justify-between font-sans text-gray-700 overflow-x-hidden">
        {/* Abstract Background */}
        <div className="absolute inset-0 -z-10 h-full w-full bg-white bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]">
          <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-gray-200 opacity-20 blur-[100px]"></div>
        </div>

        {/* Navigation Bar */}
        <header className="w-full py-6 px-4 sm:px-6 lg:px-8">
          <nav className="flex justify-between items-center">
            <span className="text-xl font-semibold text-gray-800">Talent Co-Pilot</span>
            <ul className="flex items-center space-x-6 md:space-x-10">
              <li>
                <button
                  onClick={onNavigate}
                  aria-label="Navigate to main page"
                  className="p-0 bg-transparent border-none cursor-pointer text-gray-600 hover:text-gray-900 transition-colors duration-300"
                >
                  Home
                </button>
              </li>
              <li>
                <button onClick={() => setAboutModalOpen(true)} aria-label="Show About Us information" className="text-gray-600 hover:text-gray-900 transition-colors duration-300">
                  About Us
                </button>
              </li>
              <li>
                <button onClick={() => setFeaturesModalOpen(true)} aria-label="Show Features information" className="text-gray-600 hover:text-gray-900 transition-colors duration-300">
                  Features
                </button>
              </li>
              <li>
                <a href="https://techolution.com" target="_blank" rel="noopener noreferrer" aria-label="Navigate to Contact page" className="text-gray-600 hover:text-gray-900 transition-colors duration-300">
                  Contact
                </a>
              </li>
            </ul>
          </nav>
        </header>

        {/* Hero Section */}
        <main className="flex-grow flex flex-col justify-center items-center text-center px-4">
          <div className="flex flex-col items-center space-y-6">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-gray-900">
              AI-Powered Project–Resource Matching
            </h1>
            <p className="max-w-2xl text-lg md:text-xl text-gray-600">
              Smarter staffing with explainable AI
            </p>
            <button
              onClick={onNavigate}
              className="mt-4 px-8 py-3 bg-gray-800 text-white font-semibold rounded-md shadow-sm hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-all duration-300"
            >
              Get Started
            </button>
          </div>
        </main>

        {/* Empty footer for spacing */}
        <footer className="w-full py-8"></footer>
      </div>

      {isAboutModalOpen && (
        <Modal title="About Us" onClose={() => setAboutModalOpen(false)}>
          <p>
            Welcome to <strong>Talent Co-Pilot</strong>, an intelligent platform designed to bridge the gap between complex projects and the skilled professionals who can bring them to life. Our mission is to eliminate the guesswork in talent allocation by leveraging the power of explainable AI.
          </p>
          <p>
            We believe that the success of any project hinges on having the right people with the right skills at the right time. Traditional resource management is often reactive and fraught with biases. Talent Co-Pilot provides a data-driven, proactive approach, ensuring that every staffing decision is optimal, transparent, and fair.
          </p>
          <p>
            Built by a team passionate about the intersection of technology and human potential, our tool is more than just a database—it's an active partner in your strategic planning, helping you build stronger teams, deliver projects faster, and foster a culture of growth by identifying and addressing skill gaps.
          </p>
        </Modal>
      )}

      {isFeaturesModalOpen && (
        <Modal title="Our Unique Features" onClose={() => setFeaturesModalOpen(false)}>
            <ul className="list-disc list-inside space-y-3">
              <li>
                <strong>AI-Powered Team Recommendations:</strong> Our core feature. The AI analyzes project descriptions and required skills to suggest the best-suited candidates from your talent pool, complete with a match percentage and a clear justification.
              </li>
              <li>
                <strong>Dynamic Dashboard & Analytics:</strong> Get a real-time, visual overview of your entire operation. Track project statuses, team workload, skill distributions, and project velocity with interactive charts and graphs.
              </li>
              <li>
                <strong>Proactive Skill Gap Analysis:</strong> The AI doesn't just find matches; it identifies skill gaps in promising candidates and recommends specific training modules, linking directly to learning resources.
              </li>
               <li>
                <strong>Automated Project Detailing:</strong> Streamline project creation by uploading a document (PDF, DOC, or image). Our AI will parse the content and automatically populate the project name, description, and required skills.
              </li>
              <li>
                <strong>Integrated Talent & Project Management:</strong> A single source of truth for your projects and people. Track project assignments, view individual career histories, and manage your team's skills and experience all in one place.
              </li>
              <li>
                <strong>Persistent & Secure:</strong> All your data is saved securely in your browser's local storage, ensuring your work is always there when you return, with no need for a backend server.
              </li>
            </ul>
        </Modal>
      )}
    </>
  );
};

export default LandingPage;
