import React from 'react';
import { trainingLinks } from './TrainingLinks';

interface TrainingViewProps {
  trainingSearchQuery: string;
  setTrainingSearchQuery: (query: string) => void;
}

const TrainingView: React.FC<TrainingViewProps> = ({ trainingSearchQuery, setTrainingSearchQuery }) => {
  const filteredTrainingLinks = Object.entries(trainingLinks).filter(([skill, url]) =>
    skill.toLowerCase().includes(trainingSearchQuery.toLowerCase())
  );

  return (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-6">Training Resources</h1>
      <div className="mb-6">
        <label htmlFor="search-training" className="sr-only">Search Training</label>
        <input id="search-training" type="text" placeholder="Search for a skill..." value={trainingSearchQuery} onChange={e => setTrainingSearchQuery(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" />
      </div>
      {filteredTrainingLinks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTrainingLinks.map(([skill, url]) => (
            <a href={url} key={skill} target="_blank" rel="noopener noreferrer" className="block bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow group">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center bg-gray-200 rounded-full">
                  <svg className="h-6 w-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">{skill}</h2>
                  <p className="text-sm text-gray-500 group-hover:text-gray-700">Watch tutorial on YouTube</p>
                </div>
              </div>
            </a>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">No training resources found for "{trainingSearchQuery}".</p>
        </div>
      )}
    </div>
  );
};

export default TrainingView;