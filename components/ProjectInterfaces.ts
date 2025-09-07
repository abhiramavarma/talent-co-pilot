export interface ProjectPhase {
  id: string;
  name: string;
  description: string;
  status: 'To Do' | 'Completed';
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'Not Started' | 'In Progress' | 'Completed';
  skills: string[];
  assignedTo: string[];
  startDate?: string;
  endDate?: string;
  phases?: ProjectPhase[];
}

export interface User {
  id: string;
  name: string;
  role: string;
  skills: string[];
  experience: number;
}

export interface PredictionResult {
    bestMatches: {
        userId: string;
        matchPercentage: number;
        justification: string;
        missingSkills: string[];
    }[];
    trainingRecommendations: {
        userId: string;
        missingSkills: string[];
        reason: string;
    }[];
}