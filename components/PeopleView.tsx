import React from 'react';
import { User, Project } from './ProjectInterfaces';

interface PeopleViewProps {
  users: User[];
  projects: Project[];
  selectedUser: User | null;
  setSelectedUser: (user: User | null) => void;
  isAddPersonModalOpen: boolean;
  setIsAddPersonModalOpen: (isOpen: boolean) => void;
  seniorityFilter: 'All' | 'Experienced' | 'Intermediate' | 'Freshers';
  setSeniorityFilter: (filter: 'All' | 'Experienced' | 'Intermediate' | 'Freshers') => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  skillFilter: string;
  setSkillFilter: (skill: string) => void;
  handleAddPersonClick: () => void;
}

const PeopleView: React.FC<PeopleViewProps> = ({
  users,
  projects,
  selectedUser,
  setSelectedUser,
  seniorityFilter,
  setSeniorityFilter,
  searchQuery,
  setSearchQuery,
  skillFilter,
  setSkillFilter,
  handleAddPersonClick,
}) => {
  const allSkills = [...new Set(users.flatMap(user => user.skills))].sort();

  const getSeniorityButtonClass = (level: 'All' | 'Experienced' | 'Intermediate' | 'Freshers') => {
    const base = "px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 flex-grow text-center";
    if (seniorityFilter === level) {
      return `${base} bg-gray-800 text-white shadow-sm`;
    }
    return `${base} bg-white text-gray-700 border border-gray-200 hover:bg-gray-100`;
  };
  
  const filteredUsers = users.filter(user => {
      const matchesSearch = user.name.toLowerCase().includes(searchQuery.toLowerCase()) || user.role.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesSkill = skillFilter === 'All' || user.skills.includes(skillFilter);
      return matchesSearch && matchesSkill;
  });

  const experiencedUsers = filteredUsers.filter(user => user.experience >= 6);
  const intermediateUsers = filteredUsers.filter(user => user.experience >= 3 && user.experience < 6);
  const freshers = filteredUsers.filter(user => user.experience < 3);

  const getStatusBadge = (status: Project['status']) => {
    switch (status) {
      case 'Completed': return 'bg-green-100 text-green-800';
      case 'In Progress': return 'bg-yellow-100 text-yellow-800';
      case 'Not Started': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  if (selectedUser) {
    const userProjects = projects.filter(p => p.assignedTo.includes(selectedUser.id));
    return (
      <div>
           <button onClick={() => setSelectedUser(null)} className="mb-6 inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-900">
              <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path></svg>
              Back to People
          </button>
          <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
              <h1 className="text-3xl font-bold text-gray-900">{selectedUser.name}</h1>
              <p className="text-lg text-gray-500 mb-2">{selectedUser.role}</p>
              <p className="text-md text-gray-600 mb-6"><strong>{selectedUser.experience}</strong> years of experience</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                      <h2 className="text-xl font-semibold text-gray-800 mb-4">Skills</h2>
                      <div className="flex flex-wrap gap-3">
                          {selectedUser.skills.map(skill => (
                              <span key={skill} className="px-3 py-1 text-sm font-medium rounded-full bg-gray-200 text-gray-800">
                                  {skill}
                              </span>
                          ))}
                      </div>
                  </div>
                  <div>
                      <h2 className="text-xl font-semibold text-gray-800 mb-4">Project History</h2>
                      {userProjects.length > 0 ? (
                          <ul className="space-y-3">
                              {userProjects.map(project => (
                                  <li key={project.id} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                                      <div className="flex justify-between items-center">
                                          <span className="font-semibold text-gray-800">{project.name}</span>
                                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(project.status)}`}>{project.status}</span>
                                      </div>
                                      {project.startDate && (
                                          <p className="text-xs text-gray-500 mt-1">
                                              {formatDate(project.startDate)} - {project.endDate ? formatDate(project.endDate) : 'Present'}
                                          </p>
                                      )}
                                  </li>
                              ))}
                          </ul>
                      ) : (
                          <p className="text-gray-500">No projects assigned yet.</p>
                      )}
                  </div>
              </div>
          </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">People</h1>
          <button onClick={handleAddPersonClick} className="px-4 py-2 bg-gray-800 text-white font-semibold rounded-md shadow-sm hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-all duration-300">
            + Add Person
          </button>
      </div>

      {/* Filter Controls */}
      <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label htmlFor="search-people" className="sr-only">Search</label>
                <input id="search-people" type="text" placeholder="Search by name or role..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" />
            </div>
            <div>
                <label htmlFor="skill-filter" className="sr-only">Filter by skill</label>
                <select id="skill-filter" value={skillFilter} onChange={e => setSkillFilter(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm bg-white">
                    <option value="All">Filter by skill...</option>
                    {allSkills.map(skill => <option key={skill} value={skill}>{skill}</option>)}
                </select>
            </div>
        </div>
        <div className="flex space-x-2">
            <button onClick={() => setSeniorityFilter('All')} className={getSeniorityButtonClass('All')}>All</button>
            <button onClick={() => setSeniorityFilter('Experienced')} className={getSeniorityButtonClass('Experienced')}>Experienced</button>
            <button onClick={() => setSeniorityFilter('Intermediate')} className={getSeniorityButtonClass('Intermediate')}>Intermediate</button>
            <button onClick={() => setSeniorityFilter('Freshers')} className={getSeniorityButtonClass('Freshers')}>Freshers</button>
        </div>
      </div>
      
      {filteredUsers.length === 0 ? (
           <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
              <p className="text-gray-500">No people found matching your criteria.</p>
          </div>
      ) : (
          <div className="space-y-12">
              {(seniorityFilter === 'All' || seniorityFilter === 'Experienced') && experiencedUsers.length > 0 && (
                  <div>
                      <h2 className="text-2xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">Experienced ({experiencedUsers.length})</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          {experiencedUsers.map(user => (
                              <div key={user.id} onClick={() => setSelectedUser(user)} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:shadow-md transition-shadow">
                                  <h3 className="text-lg font-bold text-gray-900">{user.name}</h3>
                                  <p className="text-gray-600">{user.role}</p>
                              </div>
                          ))}
                      </div>
                  </div>
              )}

              {(seniorityFilter === 'All' || seniorityFilter === 'Intermediate') && intermediateUsers.length > 0 && (
                  <div>
                      <h2 className="text-2xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">Intermediate ({intermediateUsers.length})</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          {intermediateUsers.map(user => (
                              <div key={user.id} onClick={() => setSelectedUser(user)} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:shadow-md transition-shadow">
                                  <h3 className="text-lg font-bold text-gray-900">{user.name}</h3>
                                  <p className="text-gray-600">{user.role}</p>
                              </div>
                          ))}
                      </div>
                  </div>
              )}

              {(seniorityFilter === 'All' || seniorityFilter === 'Freshers') && freshers.length > 0 && (
                  <div>
                      <h2 className="text-2xl font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">Freshers ({freshers.length})</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          {freshers.map(user => (
                              <div key={user.id} onClick={() => setSelectedUser(user)} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:shadow-md transition-shadow">
                                  <h3 className="text-lg font-bold text-gray-900">{user.name}</h3>
                                  <p className="text-gray-600">{user.role}</p>
                              </div>
                          ))}
                      </div>
                  </div>
              )}
          </div>
      )}
    </div>
  );
};

export default PeopleView;