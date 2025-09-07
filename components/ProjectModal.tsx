import React, { useState, FormEvent } from 'react';
import { GoogleGenAI, Type } from "@google/genai";
import { Project, ProjectPhase, User, PredictionResult } from './ProjectInterfaces';
import { trainingLinks } from './TrainingLinks';

interface ProjectModalProps {
  isModalOpen: boolean;
  currentProject: Partial<Project> | null;
  setCurrentProject: (project: Partial<Project> | null) => void;
  handleSaveProject: (e: FormEvent<HTMLFormElement>) => void;
  handleModalClose: () => void;
  projects: Project[];
  users: User[];
  generateProjectPhases: (project: Project) => void;
}

const ProjectModal: React.FC<ProjectModalProps> = ({
  isModalOpen,
  currentProject,
  setCurrentProject,
  handleSaveProject,
  handleModalClose,
  projects,
  users,
  generateProjectPhases,
}) => {
  const [documentImage, setDocumentImage] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [predictionResults, setPredictionResults] = useState<PredictionResult | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [numPeopleToFind, setNumPeopleToFind] = useState<number>(3);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  if (!isModalOpen || !currentProject) return null;

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files) {
        const file = e.target.files;
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
        const base64Data = (reader.result as string).split(','); // Get the actual base64 string
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

  return (
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
  );
};

export default ProjectModal;