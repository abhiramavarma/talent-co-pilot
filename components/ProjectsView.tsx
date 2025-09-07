import React from 'react';
import { Project, User } from './ProjectInterfaces';

interface ProjectsViewProps {
  projects: Project[];
  users: User[];
  filterStatus: 'All' | Project['status'];
  setFilterStatus: (status: 'All' | Project['status']) => void;
  projectSearchQuery: string;
  setProjectSearchQuery: (query: string) => void;
  handleAddProjectClick: () => void;
  handleEditProjectClick: (project: Project) => void;
  handleDeleteProject: (projectId: string) => void;
}

const ProjectsView: React.FC<ProjectsViewProps> = ({
  projects,
  users,
  filterStatus,
  setFilterStatus,
  projectSearchQuery,
  setProjectSearchQuery,
  handleAddProjectClick,
  handleEditProjectClick,
  handleDeleteProject,
}) => {
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

  const statusOrder: { [key in Project['status']]: number } = {
    'In Progress': 1, 'Not Started': 2, 'Completed': 3,
  };

  const filteredProjects = projects
    .filter(project => {
      const matchesStatus = filterStatus === 'All' || project.status === filterStatus;
      const matchesSearch = project.name.toLowerCase().includes(projectSearchQuery.toLowerCase()) ||
                            project.description.toLowerCase().includes(projectSearchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    })
    .sort((a, b) => {
      const statusComparison = statusOrder[a.status] - statusOrder[b.status];
      if (statusComparison !== 0) return statusComparison;
      return a.name.localeCompare(b.name);
    });

  const getFilterButtonClass = (status: 'All' | Project['status']) => {
    const base = "px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200";
    if (filterStatus === status) {
        if (status === 'All') return `${base} bg-gray-800 text-white`;
        if (status === 'Not Started') return `${base} bg-red-600 text-white`;
        if (status === 'In Progress') return `${base} bg-yellow-500 text-white`;
        if (status === 'Completed') return `${base} bg-green-600 text-white`;
    }
    return `${base} bg-white text-gray-700 border border-gray-200 hover:bg-gray-100`;
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Projects</h1>
          <button onClick={handleAddProjectClick} className="px-4 py-2 bg-gray-800 text-white font-semibold rounded-md shadow-sm hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-all duration-300">
          + Add Project
          </button>
      </div>
      <div className="mb-6">
          <label htmlFor="search-projects" className="sr-only">Search Projects</label>
          <input id="search-projects" type="text" placeholder="Search by name or description..." value={projectSearchQuery} onChange={e => setProjectSearchQuery(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" />
      </div>
      <div className="flex space-x-2 mb-6 border-b border-gray-200 pb-4">
        <button onClick={() => setFilterStatus('All')} className={getFilterButtonClass('All')}>All</button>
        <button onClick={() => setFilterStatus('Not Started')} className={getFilterButtonClass('Not Started')}>Not Started</button>
        <button onClick={() => setFilterStatus('In Progress')} className={getFilterButtonClass('In Progress')}>In Progress</button>
        <button onClick={() => setFilterStatus('Completed')} className={getFilterButtonClass('Completed')}>Completed</button>
      </div>
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map(project => {
              const totalPhases = project.phases?.length || 0;
              const completedPhases = project.phases?.filter(p => p.status === 'Completed').length || 0;
              const progress = totalPhases > 0 ? (completedPhases / totalPhases) * 100 : 0;
              
              return (
                <div key={project.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2">
                        <h2 className="text-lg font-bold text-gray-900">{project.name}</h2>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(project.status)}`}>{project.status}</span>
                    </div>
                    <p className="text-gray-600 text-sm mb-4">{project.description}</p>
                    {project.startDate && (
                        <div className="text-xs text-gray-500 mb-4 space-y-1">
                          {project.status === 'In Progress' && <p><strong>Started:</strong> {formatDate(project.startDate)}</p>}
                          {project.status === 'Completed' && <p><strong>Duration:</strong> {formatDate(project.startDate)} - {formatDate(project.endDate)}</p>}
                        </div>
                    )}
                     {totalPhases > 0 && (
                      <div className="mb-4">
                          <div className="flex justify-between items-center mb-1">
                              <h3 className="text-sm font-semibold text-gray-800">Progress</h3>
                              <span className="text-xs text-gray-500">{completedPhases} / {totalPhases} phases</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${progress}%` }}></div>
                          </div>
                      </div>
                     )}
                    <div className="mb-4">
                      <h3 className="text-sm font-semibold text-gray-800 mb-2">Required Skills</h3>
                      <div className="flex flex-wrap gap-2">
                        {project.skills.map(skill => (
                          <span key={skill} className="px-2 py-1 text-xs font-medium rounded-full bg-gray-200 text-gray-700">{skill}</span>
                        ))}
                      </div>
                    </div>
                     <div className="mb-4">
                      <h3 className="text-sm font-semibold text-gray-800 mb-2">Assigned Team</h3>
                      <div className="flex flex-wrap gap-1">
                        {project.assignedTo.length > 0 ? (
                          project.assignedTo.map(userId => {
                            const user = users.find(u => u.id === userId);
                            return user ? <span key={userId} className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">{user.name}</span> : null;
                          })
                        ) : (
                          <span className="text-xs text-gray-500 italic">No one assigned</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-end space-x-3 mt-4 border-t border-gray-100 pt-4">
                    <button 
                      onClick={() => handleEditProjectClick(project)} 
                      className={`text-sm font-medium ${project.status === 'Completed' ? 'text-gray-400 cursor-not-allowed' : 'text-gray-600 hover:text-gray-900'}`}
                      disabled={project.status === 'Completed'}
                    >
                      Edit
                    </button>
                    <button onClick={() => handleDeleteProject(project.id)} className="text-sm font-medium text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </div>
              )
          })}
        </div>
      ) : (
        <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">No projects found matching your criteria.</p>
        </div>
      )}
    </div>
  );
};

export default ProjectsView;