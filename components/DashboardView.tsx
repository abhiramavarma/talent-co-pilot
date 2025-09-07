import React from 'react';
import { Project, User } from './ProjectInterfaces';

interface DashboardViewProps {
  projects: Project[];
  users: User[];
}

const DashboardView: React.FC<DashboardViewProps> = ({ projects, users }) => {
  const DashboardStatCard = ({ title, value, icon }: { title: string; value: string | number; icon: React.ReactNode }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center">
        <div className="flex-shrink-0 bg-gray-100 rounded-md p-3 text-gray-600">{icon}</div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  // --- Data Calculations ---
  const totalProjects = projects.length;
  const inProgressCount = projects.filter(p => p.status === 'In Progress').length;
  const totalUsers = users.length;

  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const completedLast30Days = projects.filter(
    p => p.status === 'Completed' && p.endDate && new Date(p.endDate) > thirtyDaysAgo
  ).length;

  const inProgressProjects = projects.filter(p => p.status === 'In Progress');

  const workload = users.map(user => {
    const activeProjects = projects.filter(p => p.status === 'In Progress' && p.assignedTo.includes(user.id)).length;
    return { name: user.name, projectCount: activeProjects };
  }).sort((a, b) => b.projectCount - a.projectCount);

  const allSkills = users.flatMap(u => u.skills);
  const skillCounts: Record<string, number> = allSkills.reduce((acc, skill) => {
    acc[skill] = (acc[skill] || 0) + 1;
    return acc;
  }, {});

  const topSkills = Object.entries(skillCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([skill]) => skill);

  return (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-6">Dashboard Overview</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <DashboardStatCard title="Total Projects" value={totalProjects} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" /></svg>} />
        <DashboardStatCard title="In Progress" value={inProgressCount} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>} />
        <DashboardStatCard title="Completed (Last 30 Days)" value={completedLast30Days} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>} />
        <DashboardStatCard title="Team Members" value={totalUsers} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Active Projects</h2>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {inProgressProjects.length > 0 ? (
              inProgressProjects.map(project => {
                const assigned = project.assignedTo.map(id => users.find(u => u.id === id)?.name).filter(Boolean);
                return (
                  <div key={project.id} className="p-4 rounded-md border border-gray-200 hover:bg-gray-50 transition-colors">
                    <p className="font-bold text-gray-900">{project.name}</p>
                    <p className="text-sm text-gray-500 mt-1">{assigned.join(', ')}</p>
                    <p className="text-xs text-gray-400 mt-2">Started: {formatDate(project.startDate)}</p>
                  </div>
                );
              })
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p>No projects are currently in progress.</p>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Team Workload</h2>
            <ul className="space-y-3">
              {workload.map(member => (
                <li key={member.name} className="flex justify-between items-center text-sm">
                  <span className="text-gray-700">{member.name}</span>
                  <span className={`font-medium text-gray-900 ${member.projectCount > 2 ? 'bg-red-100 text-red-800' : 'bg-gray-100'} px-2 py-1 rounded-md`}>
                    {member.projectCount} {member.projectCount === 1 ? 'project' : 'projects'}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Top 5 Skills</h2>
            <div className="flex flex-wrap gap-2">
              {topSkills.map(skill => (
                <span key={skill} className="px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;