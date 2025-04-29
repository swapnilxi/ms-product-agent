import { create } from 'zustand';
import axios from 'axios';

// 1. Axios instance inside chatApi.js itself
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
});

// 2. Zustand store
export const useChatStore = create((set, get) => ({
  company1: '',
  company2: '',
  userInput: '',
  messages: [],
  loading: false,
  error: null,

  setCompany1: (company) => set({ company1: company }),
  setCompany2: (company) => set({ company2: company }),
  setUserInput: (input) => set({ userInput: input }),

  clearMessages: () => set({ messages: [] }),

  runAgent: async (endpoint) => {
    set({ loading: true, error: null });

    try {
      const { company1, company2, userInput } = get();
      const payload = { company1, company2, userInput };

      const response = await apiClient.post(endpoint, payload);

      if (response?.data?.messages) {
        set((state) => ({
          messages: [...state.messages, ...response.data.messages],
          loading: false,
        }));
      } else {
        set({ loading: false, error: "No messages received." });
      }
    } catch (error) {
      console.error("Agent run failed:", error);
      set({ loading: false, error: "Failed to run agent" });
    }
  }
}));
