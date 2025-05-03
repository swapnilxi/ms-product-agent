"use client";

import { useChatStore } from '@/services/chatApi';
import { AGENT_ENDPOINTS, LABELS } from '@/config'; // correct import path!
import { RocketLaunchIcon, LightBulbIcon, ChartBarIcon, SparklesIcon } from '@heroicons/react/24/solid';

export default function ActionButtons() {
  const { runAgent, loading, setLoading } = useChatStore();
  const handleClick = async (endpoint) => {
    setLoading(true);
    try {
      await runAgent(endpoint);
    } finally {
      setLoading(false);
    }
  };

  const buttons = [
    {
      label: LABELS.generateProductIdea,
      endpoint: AGENT_ENDPOINTS.productAgent,
      icon: LightBulbIcon,
      bgColor: 'bg-blue-600',
      hoverColor: 'hover:bg-blue-700',
    },
    {
      label: LABELS.getResearchReport,
      endpoint: AGENT_ENDPOINTS.researchAgent,
      icon: ChartBarIcon,
      bgColor: 'bg-indigo-600',
      hoverColor: 'hover:bg-indigo-700',
    },
    {
      label: LABELS.generateMarketingPlan,
      endpoint: AGENT_ENDPOINTS.marketingAgent,
      icon: SparklesIcon,
      bgColor: 'bg-purple-600',
      hoverColor: 'hover:bg-purple-700',
    },
    {
      label: LABELS.runFullPipeline,
      endpoint: AGENT_ENDPOINTS.runPipeline,
      icon: RocketLaunchIcon,
      bgColor: 'bg-green-600',
      hoverColor: 'hover:bg-green-700',
    },
  ];

  return (
    <div className="flex flex-wrap gap-4 justify-center">
      {buttons.map(({ label, endpoint, icon: Icon, bgColor, hoverColor }) => (
        <button
          key={label}
          onClick={() => handleClick(endpoint)}
          disabled={loading}
          className={`inline-flex items-center px-4 py-2 rounded-md text-white font-medium transition-colors duration-200 ${bgColor} ${hoverColor} disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <Icon className="h-5 w-5 mr-2" />
          {label}
        </button>
      ))}
    </div>
  );
}
