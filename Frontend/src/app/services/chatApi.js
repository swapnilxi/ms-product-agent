import { create } from 'zustand';
import axios from 'axios';
import { AGENT_ENDPOINTS } from '@/config';

// 1. Axios instance inside chatApi.js itself
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  // baseURL:'https://ms-product-backend.politedesert-4d05d312.eastus2.azurecontainerapps.io/',
  timeout: 70000,
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
  setLoading: (val) => set({ loading: val }),

  clearMessages: () => set({ messages: [] }),

  runAgent: async (endpoint) => {
    set({ loading: true, error: null });

    try {
      const { company1, company2, userInput } = get();
      const payload = { 
        companyName1: company1, 
        companyName2: company2, 
        textInstruction: userInput 
      };
      const response = await apiClient.post(endpoint, payload);

      if (response?.data?.messages) {
        // Normalize messages here: map 'source' → 'role'
        const normalizedMessages = response.data.messages.map((msg) => ({
          role: msg.source,
          content: msg.content,
        }));
  
        set((state) => ({
          messages: [...state.messages, ...normalizedMessages],
          loading: false,
        }));
      } else {
        set({ loading: false, error: "No messages received." });
      }

      if (response?.data?.pdf_report) {
        const pdfFile = response.data.pdf_report;
        const link = document.createElement('a');
        link.href = `${process.env.NEXT_PUBLIC_API_URL}/download-report-pdf/${pdfFile}`;
        link.download = pdfFile;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      

    } catch (error) {
      console.error("Agent run failed:", error);
      set({ loading: false, error: "Failed to run agent" });
    }
  },
  sendMessage: async () => {
    await get().runAgent(AGENT_ENDPOINTS.runPipeline);
    // will add more logic here in the future if needed
  },


}));