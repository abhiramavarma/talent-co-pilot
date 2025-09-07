
import React, { useState, useEffect, FormEvent } from 'react';
import { GoogleGenAI, Type } from "@google/genai";
import { ProjectPhase, Project, User, PredictionResult } from './ProjectInterfaces';
import { trainingLinks } from './TrainingLinks';


const MainPage: React.FC = () => {
  // Page state
  const [activeView, setActiveView] = useState<'dashboard' | 'projects' | 'people' | 'training'>('dashboard');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Project state
  const [projects, setProjects] = useState<Project[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentProject, setCurrentProject] = useState<Partial<Project> | null>(null);
  const [filterStatus, setFilterStatus] = useState<'All' | Project['status']>('All');
  const [projectSearchQuery, setProjectSearchQuery] = useState('');

  // User state
  const [users, setUsers] = useState<User[]>([]);
  const [isAddPersonModalOpen, setIsAddPersonModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<Partial<User> | null>(null);
  
  // People Filter State
  const [seniorityFilter, setSeniorityFilter] = useState<'All' | 'Experienced' | 'Intermediate' | 'Freshers'>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [skillFilter, setSkillFilter] = useState<string>('All');

  // Training State
  const [trainingSearchQuery, setTrainingSearchQuery] = useState('');

  // AI Prediction State
  const [predictionResults, setPredictionResults] = useState<PredictionResult | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [numPeopleToFind, setNumPeopleToFind] = useState<number>(3);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  // Document Extraction State
  const [documentImage, setDocumentImage] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);

  // Load data on initial render
  useEffect(() => {
    const loadData = async () => {
      try {
        const storedProjects = localStorage.getItem('projects');
        const storedUsers = localStorage.getItem('users');
        
        if (storedProjects && storedUsers) {
          setProjects(JSON.parse(storedProjects));
          setUsers(JSON.parse(storedUsers));
        } else {
          // Fetch from the new data.json file
          const response = await fetch('/data.json');
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          setProjects(data.projects || []);
          setUsers(data.users || []);
        }
      } catch (error) {
        console.error("Failed to load initial data:", error);
        // Fallback to empty arrays if both localStorage and fetch fail
        setProjects([]);
        setUsers([]);
      }
    };
    
    loadData();
  }, []); // Empty dependency array ensures this runs only once on mount

  // Save projects to localStorage whenever the projects list changes
  useEffect(() => {
    if (projects.length > 0) {
        localStorage.setItem('projects', JSON.stringify(projects));
    }
  }, [projects]);

  // Save users to localStorage whenever the users list changes
  useEffect(() => {
     if (users.length > 0) {
        localStorage.setItem('users', JSON.stringify(users));
     }
  }, [users]);

  const generateProjectPhases = async (project: Project) => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY as string });
    const prompt = `
        Based on the project named "${project.name}" with the description "${project.description}", 
        please generate a list of logical project phases. Each phase should be an object with a 'name', 
        a 'description', and a 'status' which should be set to 'To Do'.
        Provide the output as a JSON array of these objects.
    `;
    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.ARRAY,
                    items: {
                        type: Type.OBJECT,
                        properties: {
                            name: { type: Type.STRING },
                            description: { type: Type.STRING },
                            status: { type: Type.STRING },
                        },
                        required: ['name', 'description', 'status'],
                    },
                },
            },
        });

        const resultText = response.text.trim();
        // FIX: Replaced object spread on an 'any' type with explicit property assignment.
        // This resolves a TypeScript error where the 'status' property was inferred as 'string'
        // instead of the literal type 'To Do', making it incompatible with the ProjectPhase type.
        const generatedPhases: ProjectPhase[] = JSON.parse(resultText).map((phase: any) => ({
            name: phase.name,
            description: phase.description,
            id: `phase-${Date.now()}-${Math.random()}`, // Add unique ID
            status: 'To Do', // Ensure status is set correctly
        }));

        setProjects(prevProjects =>
            prevProjects.map(p =>
                p.id === project.id ? { ...p, phases: generatedPhases } : p
            )
        );
    } catch (error) {
        console.error("Failed to generate project phases:", error);
        // If AI fails, the project is still created, just without phases.
    }
  };
  
  const handleAddProjectClick = () => {
    setCurrentProject({ name: '', description: '', status: 'Not Started', skills: [], assignedTo: [], phases: [] });
    setIsModalOpen(true);
    setDocumentImage(null);
    setExtractionError(null);
  };

  const handleEditProjectClick = (project: Project) => {
    setCurrentProject(project);
    setIsModalOpen(true);
    setDocumentImage(null);
    setExtractionError(null);
  };
  
  const handleDeleteProject = (projectId: string) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      setProjects(projects.filter(p => p.id !== projectId));
    }
  };

  const handleSaveProject = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!currentProject?.name || !currentProject?.description || !currentProject.status) {
        alert("Please fill all fields.");
        return;
    }
    
    let projectToSave = {
        ...currentProject,
        skills: currentProject.skills?.filter(s => s.trim() !== '') || [],
        assignedTo: currentProject.assignedTo || [],
        phases: currentProject.phases || []
    };

    // Auto-set start/end dates based on status change
    if (projectToSave.id) { // Editing an existing project
      const originalProject = projects.find(p => p.id === projectToSave.id);
      if (originalProject && originalProject.status !== projectToSave.status) {
        if (projectToSave.status === 'In Progress' && !projectToSave.startDate) {
          projectToSave.startDate = new Date().toISOString();
        } else if (projectToSave.status === 'Completed' && !projectToSave.endDate) {
          projectToSave.endDate = new Date().toISOString();
           if (!projectToSave.startDate) { // If it was moved directly from Not Started
              projectToSave.startDate = new Date().toISOString();
          }
        }
      }
    }

    if (projectToSave.id) {
      setProjects(projects.map(p => p.id === projectToSave.id ? (projectToSave as Project) : p));
    } else {
      const newProject: Project = {
        ...projectToSave,
        id: new Date().toISOString(),
      } as Project;
      setProjects(prevProjects => [...prevProjects, newProject]);
      // Immediately call AI to generate phases for the new project
      generateProjectPhases(newProject);
    }
    handleModalClose();
  };
  
  const handleStatusChange = (newStatus: Project['status']) => {
    if (currentProject) {
        const updatedProject = { ...currentProject, status: newStatus };

        const originalProject = currentProject.id ? projects.find(p => p.id === currentProject.id) : null;
        const previousStatus = originalProject ? originalProject.status : 'Not Started';

        // Set start date if moving to "In Progress" for the first time
        if (newStatus === 'In Progress' && previousStatus === 'Not Started' && !updatedProject.startDate) {
            updatedProject.startDate = new Date().toISOString();
        }
        // Set end date if moving to "Completed"
        if (newStatus === 'Completed' && !updatedProject.endDate) {
            updatedProject.endDate = new Date().toISOString();
            // Also set start date if it was somehow skipped (e.g., moved from Not Started to Completed)
            if (!updatedProject.startDate) {
                updatedProject.startDate = new Date().toISOString();
            }
        }
        setCurrentProject(updatedProject);
    }
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setCurrentProject(null);
    setPredictionResults(null);
    setPredictionError(null);
    setIsPredicting(false);
    setDocumentImage(null);
    setIsExtracting(false);
    setExtractionError(null);
  };
  
  const handleAddPersonClick = () => {
    setCurrentUser({ name: '', role: '', skills: [], experience: 0 });
    setIsAddPersonModalOpen(true);
  };

  const handlePersonModalClose = () => {
    setIsAddPersonModalOpen(false);
    setCurrentUser(null);
  };

  const handleSavePerson = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!currentUser?.name || !currentUser?.role || currentUser.experience === undefined) {
        alert("Please fill all required fields.");
        return;
    }

    const newUser: User = {
        id: new Date().toISOString(),
        name: currentUser.name,
        role: currentUser.role,
        skills: currentUser.skills || [],
        experience: currentUser.experience
    };

    setUsers([...users, newUser]);
    handlePersonModalClose();
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
        const file = e.target.files[0];
        const allowedTypes = [
            'image/jpeg',
            'image/png',
            'image/webp',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        if (allowedTypes.includes(file.type)) {
            setDocumentImage(file);
            setExtractionError(null);
        } else {
            setExtractionError("Please upload a valid file (Image, PDF, or Word doc).");
            setDocumentImage(null);
        }
    }
  };

  const handleExtractFromDocument = async () => {
    if (!documentImage) {
        setExtractionError("Please select a file first.");
        return;
    }

    setIsExtracting(true);
    setExtractionError(null);

    const reader = new FileReader();
    reader.readAsDataURL(documentImage);
    reader.onload = async () => {
        const base64Data = (reader.result as string).split(',')[1];
        const mimeType = documentImage.type;

        const ai = new GoogleGenAI({ apiKey: process.env.API_KEY as string });

        const filePart = { inlineData: { mimeType, data: base64Data } };
        const textPart = { text: `Analyze the attached project document (which could be an image, PDF, or Word document). Extract the project name, a concise project description, and a list of required technical and soft skills. Provide the output in a JSON object with keys: 'projectName', 'projectDescription', and 'projectSkills' (as an array of strings). If you cannot find a value for a field, return an empty string or empty array for it.` };

        try {
            const response = await ai.models.generateContent({
                model: 'gemini-2.5-flash',
                contents: { parts: [filePart, textPart] },
                config: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: Type.OBJECT,
                        properties: {
                            projectName: { type: Type.STRING },
                            projectDescription: { type: Type.STRING },
                            projectSkills: { type: Type.ARRAY, items: { type: Type.STRING } },
                        },
                        required: ['projectName', 'projectDescription', 'projectSkills'],
                    }
                }
            });
            
            const resultText = response.text.trim();
            const extractedData = JSON.parse(resultText);

            setCurrentProject(prev => ({
                ...prev,
                name: extractedData.projectName || prev?.name,
                description: extractedData.projectDescription || prev?.description,
                skills: extractedData.projectSkills || prev?.skills,
            }));

        } catch (error) {
            console.error("AI extraction failed:", error);
            setExtractionError("Failed to extract details from the document. The file might be corrupted or the model is unavailable.");
        } finally {
            setIsExtracting(false);
        }
    };

    reader.onerror = () => {
        setExtractionError("Failed to read the file.");
        setIsExtracting(false);
    };
  };

  const handleFindMatches = async () => {
    if (!currentProject?.description || !currentProject?.skills || currentProject.skills.length === 0) {
        setPredictionError("Please provide a project description and at least one skill to find matches.");
        return;
    }
    setIsPredicting(true);
    setPredictionResults(null);
    setPredictionError(null);

    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY as string });

    const userProfiles = users.map(u => 
        `User ID: ${u.id}, Name: ${u.name}, Role: ${u.role}, Experience: ${u.experience} years, Skills: ${u.skills.join(', ')}`
    ).join('\n');

    const prompt = `
        Project Name: "${currentProject.name}"
        Project Description: "${currentProject.description}"
        Required Skills: ${currentProject.skills.join(', ')}
        Available Users:
        ${userProfiles}

        Based on the project requirements and the list of available users, analyze each user's suitability for this project. 
        Your analysis for 'matchPercentage' should consider direct skill matches, related skills, years of experience, and role alignment.
        Provide a JSON response containing:
        1. 'bestMatches': A ranked list of the top ${numPeopleToFind} users. For each match, include their userId, matchPercentage, a brief justification, and a list of 'missingSkills' from the project requirements (can be empty).
        2. 'trainingRecommendations': A list of users not in the top matches but with potential. For each, list 'missingSkills' and a 'reason'. Users with a match score below 50% are good candidates for this list.
    `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        bestMatches: {
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    userId: { type: Type.STRING },
                                    matchPercentage: { type: Type.NUMBER },
                                    justification: { type: Type.STRING },
                                    missingSkills: { type: Type.ARRAY, items: { type: Type.STRING } },
                                },
                                required: ['userId', 'matchPercentage', 'justification', 'missingSkills'],
                            }
                        },
                        trainingRecommendations: {
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    userId: { type: Type.STRING },
                                    missingSkills: { type: Type.ARRAY, items: { type: Type.STRING } },
                                    reason: { type: Type.STRING }
                                },
                                required: ['userId', 'missingSkills', 'reason'],
                            }
                        }
                    },
                    required: ['bestMatches', 'trainingRecommendations'],
                },
            },
        });
        
        const resultText = response.text.trim();
        const resultJson = JSON.parse(resultText);
        setPredictionResults(resultJson);

    } catch (error) {
        console.error("AI prediction failed:", error);
        setPredictionError("Failed to get AI predictions. The model may be unavailable or the request failed. Please try again later.");
    } finally {
        setIsPredicting(false);
    }
  };
  
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

  const getNavLinkClass = (view: typeof activeView) => {
    const base = "px-3 py-2 rounded-md text-sm font-medium transition-colors duration-300";
    if (activeView === view) {
      return `${base} bg-slate-600 text-white`;
    }
    return `${base} text-slate-200 hover:bg-slate-700 hover:text-white`;
  };

  const handleAssignUserToggle = (userId: string) => {
    if (currentProject) {
        const currentAssigned = currentProject.assignedTo || [];
        const newAssigned = currentAssigned.includes(userId)
            ? currentAssigned.filter(id => id !== userId)
            : [...currentAssigned, userId];
        setCurrentProject({ ...currentProject, assignedTo: newAssigned });
    }
  }
  
  const handleSelectRecommendedUser = (userId: string) => {
    if (currentProject) {
        const currentAssigned = currentProject.assignedTo || [];
        if (!currentAssigned.includes(userId)) {
            const newAssigned = [...currentAssigned, userId];
            setCurrentProject({ ...currentProject, assignedTo: newAssigned });
        }
    }
  };

  const handlePhaseChange = (phaseId: string, field: 'name' | 'description', value: string) => {
    if (currentProject?.phases) {
        const updatedPhases = currentProject.phases.map(phase =>
            phase.id === phaseId ? { ...phase, [field]: value } : phase
        );
        setCurrentProject({ ...currentProject, phases: updatedPhases });
    }
  };

  const handlePhaseStatusToggle = (phaseId: string) => {
    if (currentProject?.phases) {
        const updatedPhases = currentProject.phases.map(phase =>
            phase.id === phaseId ? { ...phase, status: phase.status === 'To Do' ? 'Completed' : 'To Do' } : phase
        );
        setCurrentProject({ ...currentProject, phases: updatedPhases });
    }
  };

  const renderContent = () => {
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

    switch (activeView) {
      case 'dashboard': {
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
        }
      case 'people': {
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
      }
       case 'training': {
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
        )
       }
      case 'projects':
      default:
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
    }
  };

  return (
    <div className="relative min-h-screen w-full flex flex-col font-sans text-gray-700 bg-gray-50">
      <header className="w-full bg-gradient-to-r from-slate-700 to-slate-900 shadow-lg sticky top-0 z-10">
        <nav className="flex justify-between items-center max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <span className="text-xl font-semibold text-white">Talent Co-Pilot</span>
          <ul className="flex items-center space-x-2 md:space-x-4">
            <li><button onClick={() => { setActiveView('dashboard'); setSelectedUser(null); }} className={getNavLinkClass('dashboard')}>Dashboard</button></li>
            <li><button onClick={() => { setActiveView('projects'); setSelectedUser(null); }} className={getNavLinkClass('projects')}>Projects</button></li>
            <li><button onClick={() => { setActiveView('people'); setSelectedUser(null); }} className={getNavLinkClass('people')}>People</button></li>
            <li><button onClick={() => { setActiveView('training'); setSelectedUser(null); }} className={getNavLinkClass('training')}>Training</button></li>
          </ul>
        </nav>
      </header>

      <main className="flex-grow w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>
      
      {isAddPersonModalOpen && currentUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Add New Person</h3>
            <form onSubmit={handleSavePerson}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="personName" className="block text-sm font-medium text-gray-700">Full Name</label>
                  <input type="text" id="personName" value={currentUser.name || ''} onChange={(e) => setCurrentUser({ ...currentUser, name: e.target.value })} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" required />
                </div>
                <div>
                  <label htmlFor="personRole" className="block text-sm font-medium text-gray-700">Role</label>
                  <input type="text" id="personRole" value={currentUser.role || ''} onChange={(e) => setCurrentUser({ ...currentUser, role: e.target.value })} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" required />
                </div>
                <div>
                  <label htmlFor="personExperience" className="block text-sm font-medium text-gray-700">Years of Experience</label>
                  <input type="number" id="personExperience" value={currentUser.experience ?? ''} onChange={(e) => setCurrentUser({ ...currentUser, experience: Number(e.target.value) })} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" required min="0" />
                </div>
                <div>
                  <label htmlFor="personSkills" className="block text-sm font-medium text-gray-700">Skills (comma-separated)</label>
                  <input type="text" id="personSkills" value={Array.isArray(currentUser.skills) ? currentUser.skills.join(', ') : ''} onChange={(e) => setCurrentUser({ ...currentUser, skills: e.target.value.split(',').map(s => s.trim()) })} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" placeholder="e.g. React, Python, Figma" />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button type="button" onClick={handlePersonModalClose} className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md shadow-sm hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-gray-800 text-white font-semibold rounded-md shadow-sm hover:bg-gray-900">Save Person</button>
              </div>
            </form>
          </div>
        </div>
      )}

       {isModalOpen && currentProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true">
          <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-2xl">
            <h3 className="text-xl font-medium leading-6 text-gray-900 mb-6">{currentProject.id ? 'Edit Project' : 'Add New Project'}</h3>
            <form onSubmit={handleSaveProject}>
              <div className="space-y-5 max-h-[75vh] overflow-y-auto pr-4">
                
                {/* Document Upload Section */}
                <div className="border-b border-gray-200 pb-5 mb-5">
                    <h4 className="text-md font-semibold text-gray-800 mb-3">📄 Auto-fill from File</h4>
                    <p className="text-xs text-gray-500 mb-3">Upload a project brief (Image, PDF, or Word document) to let the AI fill in the details below. This is optional.</p>
                    <div className="flex items-center space-x-3">
                        <label htmlFor="doc-upload" className="cursor-pointer px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 text-sm">
                            Choose File
                        </label>
                        <input id="doc-upload" type="file" className="hidden" onChange={handleFileChange} accept="image/*,application/pdf,.doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" />
                        {documentImage && <span className="text-sm text-gray-600 truncate">{documentImage.name}</span>}
                        <button 
                            type="button" 
                            onClick={handleExtractFromDocument} 
                            disabled={!documentImage || isExtracting} 
                            className="ml-auto px-4 py-2 bg-gray-600 text-white font-semibold rounded-md shadow-sm hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                        >
                            {isExtracting ? 'Extracting...' : 'Extract Details'}
                        </button>
                    </div>
                    {isExtracting && <div className="text-center p-4"> <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-700 mx-auto"></div> <p className="mt-2 text-sm text-gray-500">Reading document...</p></div>}
                    {extractionError && <div className="mt-3 p-2 bg-red-100 text-red-800 rounded-md text-sm">{extractionError}</div>}
                </div>

                {/* Project Details Section */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">Project Name</label>
                  <input type="text" id="name" value={currentProject.name || ''} onChange={(e) => setCurrentProject({ ...currentProject, name: e.target.value })} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" required />
                </div>
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea id="description" rows={3} value={currentProject.description || ''} onChange={(e) => setCurrentProject({ ...currentProject, description: e.target.value })} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" required></textarea>
                </div>
                <div>
                    <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
                    <select id="status" value={currentProject.status || 'Not Started'} onChange={(e) => handleStatusChange(e.target.value as Project['status'])} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm rounded-md" required>
                        <option>Not Started</option>
                        <option>In Progress</option>
                        <option>Completed</option>
                    </select>
                </div>
                <div>
                  <label htmlFor="skills" className="block text-sm font-medium text-gray-700">Required Skills (comma-separated)</label>
                  <input type="text" id="skills" value={Array.isArray(currentProject.skills) ? currentProject.skills.join(', ') : ''} onChange={(e) => setCurrentProject({ ...currentProject, skills: e.target.value.split(',').map(s => s.trim()) })} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm" placeholder="e.g. React, Node.js, Figma" />
                </div>
                 
                 {/* Project Phases Section */}
                {currentProject.phases && currentProject.phases.length > 0 && (
                    <div className="border-t border-gray-200 pt-5">
                        <h4 className="text-md font-semibold text-gray-800 mb-3">Project Phases</h4>
                        <div className="space-y-4">
                            {currentProject.phases.map(phase => (
                                <div key={phase.id} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                                    <div className="flex items-center justify-between">
                                        <input
                                            type="text"
                                            value={phase.name}
                                            onChange={(e) => handlePhaseChange(phase.id, 'name', e.target.value)}
                                            className="font-semibold text-gray-800 bg-transparent border-none focus:ring-0 w-full"
                                        />
                                        <div className="flex items-center">
                                            <label htmlFor={`phase-status-${phase.id}`} className="sr-only">Mark as completed</label>
                                            <input
                                                id={`phase-status-${phase.id}`}
                                                type="checkbox"
                                                checked={phase.status === 'Completed'}
                                                onChange={() => handlePhaseStatusToggle(phase.id)}
                                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                            />
                                        </div>
                                    </div>
                                    <textarea
                                        value={phase.description}
                                        onChange={(e) => handlePhaseChange(phase.id, 'description', e.target.value)}
                                        rows={2}
                                        className="mt-1 text-sm text-gray-600 bg-transparent border-none focus:ring-0 w-full resize-none"
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                
                {/* AI Team Finder Section */}
                <div className="border-t border-gray-200 pt-5">
                    <h4 className="text-md font-semibold text-gray-800 mb-3">✨ AI Team Recommendations</h4>
                    <div className="flex items-center space-x-3 bg-gray-50 p-3 rounded-md">
                        <label htmlFor="numPeople" className="text-sm font-medium text-gray-700">Find top</label>
                        <input type="number" id="numPeople" value={numPeopleToFind} onChange={e => setNumPeopleToFind(Number(e.target.value))} min="1" max="10" className="w-20 px-2 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm"/>
                        <label htmlFor="numPeople" className="text-sm font-medium text-gray-700">candidates</label>
                        <button type="button" onClick={handleFindMatches} disabled={isPredicting} className="ml-auto px-4 py-2 bg-gray-800 text-white font-semibold rounded-md shadow-sm hover:bg-gray-900 disabled:bg-gray-400 disabled:cursor-wait transition-colors">
                            {isPredicting ? 'Analyzing...' : 'Find Matches'}
                        </button>
                    </div>

                    {isPredicting && <div className="text-center p-6"> <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div> <p className="mt-2 text-sm text-gray-600">AI is thinking...</p></div>}
                    {predictionError && <div className="mt-3 p-3 bg-red-100 text-red-800 rounded-md text-sm">{predictionError}</div>}
                    
                    {predictionResults && (
                        <div className="mt-4 space-y-4">
                            <div>
                                <h5 className="text-sm font-semibold text-gray-800 mb-2">Top Matches</h5>
                                <ul className="space-y-2">
                                    {predictionResults.bestMatches.map(match => {
                                        const user = users.find(u => u.id === match.userId);
                                        if (!user) return null;
                                        return (
                                            <li key={match.userId} className="p-3 bg-white rounded-md border border-gray-200">
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <p className="font-bold text-gray-900">{user.name} <span className="text-sm font-normal text-gray-500">- {user.role}</span></p>
                                                        <p className="text-xs text-gray-600 italic mt-1">"{match.justification}"</p>
                                                    </div>
                                                    <div className="text-right ml-4 flex-shrink-0">
                                                        <p className="text-lg font-bold text-green-600">{match.matchPercentage}%</p>
                                                        <p className="text-xs text-gray-500">Match</p>
                                                    </div>
                                                </div>
                                                {match.matchPercentage < 50 && (
                                                    <div className="mt-2 p-2 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">
                                                        Highly Recommended Training
                                                    </div>
                                                )}
                                                {match.missingSkills && match.missingSkills.length > 0 && (
                                                    <div className="mt-2 pt-2 border-t border-gray-100">
                                                        <p className="text-xs font-semibold text-gray-700">Missing Skills:</p>
                                                        <div className="flex flex-wrap gap-2 mt-1">
                                                            {match.missingSkills.map(skill => (
                                                                <div key={skill} className="flex items-center gap-2 text-xs text-red-700 bg-red-100 px-2 py-1 rounded-full">
                                                                    <span>{skill}</span>
                                                                    {trainingLinks[skill] && (
                                                                        <a href={trainingLinks[skill]} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-bold">Learn</a>
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                <button type="button" onClick={() => handleSelectRecommendedUser(user.id)} className="mt-3 w-full text-center px-3 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded hover:bg-gray-200">
                                                    Select {user.name}
                                                </button>
                                            </li>
                                        );
                                    })}
                                </ul>
                            </div>
                            {predictionResults.trainingRecommendations.length > 0 && (
                                <div>
                                    <h5 className="text-sm font-semibold text-gray-800 mb-2">Further Training Recommendations</h5>
                                    <ul className="space-y-2">
                                        {predictionResults.trainingRecommendations.map(rec => {
                                            const user = users.find(u => u.id === rec.userId);
                                            if (!user) return null;
                                            return (
                                                <li key={rec.userId} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                                                    <p className="font-bold text-gray-900">{user.name}</p>
                                                    <p className="text-xs text-gray-600 italic mt-1">"{rec.reason}"</p>
                                                    <div className="mt-2 pt-2 border-t border-gray-100">
                                                      <div className="flex flex-wrap gap-2 mt-1">
                                                        {rec.missingSkills.map(skill => (
                                                          <div key={skill} className="flex items-center gap-2 text-xs text-red-700 bg-red-100 px-2 py-1 rounded-full">
                                                            <span>{skill}</span>
                                                            {trainingLinks[skill] && (
                                                              <a href={trainingLinks[skill]} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-bold">Learn</a>
                                                            )}
                                                          </div>
                                                        ))}
                                                      </div>
                                                    </div>
                                                </li>
                                            )
                                        })}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Assign Team Members Section */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Assign Team Members</label>
                   <div className="mt-2 border border-gray-200 rounded-md max-h-48 overflow-y-auto">
                        {users.map(user => (
                            <div key={user.id} className="flex items-center justify-between p-3 border-b last:border-b-0 hover:bg-gray-50">
                                <span>{user.name} <span className="text-xs text-gray-500">- {user.role}</span></span>
                                <input
                                    type="checkbox"
                                    checked={currentProject.assignedTo?.includes(user.id) || false}
                                    onChange={() => handleAssignUserToggle(user.id)}
                                    className="h-4 w-4 text-gray-600 border-gray-300 rounded focus:ring-gray-500"
                                />
                            </div>
                        ))}
                   </div>
                </div>
              </div>
              <div className="mt-8 flex justify-end space-x-4 border-t pt-6">
                <button type="button" onClick={handleModalClose} className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md shadow-sm hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-gray-800 text-white font-semibold rounded-md shadow-sm hover:bg-gray-900">Save Project</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MainPage;
