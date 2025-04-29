"use client";
import React from 'react';
import { useChatStore } from '@/services/chatApi';
import { AGENT_ENDPOINTS, LABELS } from '@/config';

export default function ActionButtons() {
  const { runAgent, loading } = useChatStore();

  return (
    <div className="flex flex-wrap gap-4">
      <button
        onClick={() => runAgent(AGENT_ENDPOINTS.productAgent)}
        disabled={loading}
        className="border p-2 rounded bg-blue-500 text-white disabled:opacity-50"
      >
        {LABELS.generateProductIdea}
      </button>
      <button
        onClick={() => runAgent(AGENT_ENDPOINTS.researchAgent)}
        disabled={loading}
        className="border p-2 rounded bg-blue-500 text-white disabled:opacity-50"
      >
        {LABELS.getResearchReport}
      </button>
      <button
        onClick={() => runAgent(AGENT_ENDPOINTS.marketingAgent)}
        disabled={loading}
        className="border p-2 rounded bg-blue-500 text-white disabled:opacity-50"
      >
        {LABELS.generateMarketingPlan}
      </button>
      <button
        onClick={() => runAgent(AGENT_ENDPOINTS.runPipeline)}
        disabled={loading}
        className="border p-2 rounded bg-green-600 text-white disabled:opacity-50"
      >
        {LABELS.runFullPipeline}
      </button>
    </div>
  );
}
