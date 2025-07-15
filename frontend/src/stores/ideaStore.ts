import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '../utils/api'

export interface Idea {
  id: string
  content: string
  source_type: 'voice' | 'text' | 'dream' | 'image'
  category?: string
  urgency_score: number
  novelty_score: number
  created_at: string
  updated_at: string
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  tags: string[]
  expansions?: string[]
  visuals?: Array<{
    path: string
    prompt: string
  }>
}

interface IdeaFilter {
  category?: string
  source_type?: string
  min_urgency?: number
  search?: string
  tags?: string[]
}

interface IdeaState {
  ideas: Idea[]
  currentIdea: Idea | null
  isLoading: boolean
  error: string | null
  filter: IdeaFilter
  pendingIdeas: Idea[] // For offline mode
  
  // Actions
  fetchIdeas: (filter?: IdeaFilter) => Promise<void>
  fetchIdeaById: (id: string) => Promise<void>
  createIdea: (content: string, type: 'voice' | 'text' | 'dream', options?: any) => Promise<string | null>
  updateIdea: (id: string, updates: Partial<Idea>) => Promise<void>
  deleteIdea: (id: string) => Promise<void>
  setFilter: (filter: IdeaFilter) => void
  clearError: () => void
  
  // Offline support
  addPendingIdea: (idea: Omit<Idea, 'id'>) => void
  syncPendingIdeas: () => Promise<void>
}

export const useIdeaStore = create<IdeaState>()(
  persist(
    (set, get) => ({
      ideas: [],
      currentIdea: null,
      isLoading: false,
      error: null,
      filter: {},
      pendingIdeas: [],

      fetchIdeas: async (filter?: IdeaFilter) => {
        set({ isLoading: true, error: null })
        
        try {
          const params = new URLSearchParams()
          
          if (filter?.category) params.append('category', filter.category)
          if (filter?.source_type) params.append('source_type', filter.source_type)
          if (filter?.min_urgency) params.append('min_urgency', filter.min_urgency.toString())
          if (filter?.search) params.append('search', filter.search)
          
          const response = await apiClient.get(`/ideas?${params}`)
          
          set({ 
            ideas: response.data,
            isLoading: false,
            filter: filter || {}
          })
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to fetch ideas',
            isLoading: false
          })
        }
      },

      fetchIdeaById: async (id: string) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await apiClient.get(`/ideas/${id}`)
          set({ 
            currentIdea: response.data,
            isLoading: false
          })
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to fetch idea',
            isLoading: false
          })
        }
      },

      createIdea: async (content: string, type: 'voice' | 'text' | 'dream', options = {}) => {
        set({ isLoading: true, error: null })
        
        try {
          let response
          
          if (type === 'voice') {
            const formData = new FormData()
            formData.append('audio_file', options.audioFile)
            formData.append('urgency', options.urgency || 'normal')
            if (options.location) formData.append('location', options.location)
            
            response = await apiClient.post('/capture/voice', formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            })
          } else if (type === 'text') {
            response = await apiClient.post('/capture/text', {
              content,
              urgency: options.urgency || 'normal',
              location: options.location
            })
          } else if (type === 'dream') {
            const formData = new FormData()
            formData.append('content', content)
            formData.append('dream_type', options.dreamType || 'regular')
            formData.append('sleep_stage', options.sleepStage || 'unknown')
            
            response = await apiClient.post('/capture/dream', formData)
          }
          
          if (response?.data.success) {
            // Refresh ideas list
            await get().fetchIdeas(get().filter)
            
            set({ isLoading: false })
            return response.data.idea_id
          } else {
            throw new Error(response?.data.error || 'Failed to create idea')
          }
        } catch (error: any) {
          // If offline, add to pending ideas
          if (!navigator.onLine) {
            const pendingIdea: Omit<Idea, 'id'> = {
              content,
              source_type: type,
              urgency_score: options.urgency === 'high' ? 80 : options.urgency === 'low' ? 30 : 50,
              novelty_score: 50,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              processing_status: 'pending',
              tags: []
            }
            
            get().addPendingIdea(pendingIdea)
            set({ isLoading: false })
            return 'pending-' + Date.now().toString()
          }
          
          set({ 
            error: error.response?.data?.detail || 'Failed to create idea',
            isLoading: false
          })
          return null
        }
      },

      updateIdea: async (id: string, updates: Partial<Idea>) => {
        set({ isLoading: true, error: null })
        
        try {
          await apiClient.put(`/ideas/${id}`, updates)
          
          // Update local state
          set(state => ({
            ideas: state.ideas.map(idea => 
              idea.id === id ? { ...idea, ...updates } : idea
            ),
            currentIdea: state.currentIdea?.id === id 
              ? { ...state.currentIdea, ...updates }
              : state.currentIdea,
            isLoading: false
          }))
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to update idea',
            isLoading: false
          })
        }
      },

      deleteIdea: async (id: string) => {
        set({ isLoading: true, error: null })
        
        try {
          await apiClient.delete(`/ideas/${id}`)
          
          // Remove from local state
          set(state => ({
            ideas: state.ideas.filter(idea => idea.id !== id),
            currentIdea: state.currentIdea?.id === id ? null : state.currentIdea,
            isLoading: false
          }))
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to delete idea',
            isLoading: false
          })
        }
      },

      setFilter: (filter: IdeaFilter) => {
        set({ filter })
      },

      clearError: () => {
        set({ error: null })
      },

      addPendingIdea: (idea: Omit<Idea, 'id'>) => {
        const pendingIdea: Idea = {
          ...idea,
          id: 'pending-' + Date.now().toString()
        }
        
        set(state => ({
          pendingIdeas: [...state.pendingIdeas, pendingIdea],
          ideas: [...state.ideas, pendingIdea]
        }))
      },

      syncPendingIdeas: async () => {
        const { pendingIdeas } = get()
        
        if (pendingIdeas.length === 0) return
        
        for (const pendingIdea of pendingIdeas) {
          try {
            await get().createIdea(
              pendingIdea.content,
              pendingIdea.source_type,
              { urgency: pendingIdea.urgency_score > 70 ? 'high' : 'normal' }
            )
          } catch (error) {
            console.error('Failed to sync pending idea:', error)
          }
        }
        
        // Clear pending ideas after successful sync
        set({ pendingIdeas: [] })
      }
    }),
    {
      name: 'dreamcatcher-ideas',
      partialize: (state) => ({
        pendingIdeas: state.pendingIdeas,
        filter: state.filter
      })
    }
  )
)