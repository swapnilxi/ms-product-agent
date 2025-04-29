"use client";

import { useState } from 'react';
import { useChatStore } from '@/services/chatApi';

const companies = [
  "OpenAI",
  "Google",
  "Amazon",
  "Microsoft",
  "Custom Entry",
];

export default function CompanySelector() {
  const { company1, setCompany1, company2, setCompany2 } = useChatStore();
  const [custom1, setCustom1] = useState(false);
  const [custom2, setCustom2] = useState(false);

  return (
    <div className="flex flex-col md:flex-row gap-4 px-2">
      
      {/* Company 1 */}
      <div className="flex flex-col w-full">
        {!custom1 ? (
          <select
            value={company1}
            onChange={(e) => {
              if (e.target.value === "Custom Entry") {
                setCustom1(true);
                setCompany1("");
              } else {
                setCompany1(e.target.value);
              }
            }}
            className="border border-gray-500 p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-white placeholder-white"
          >
            <option value="">Select Company 1</option>
            {companies.map((company) => (
              <option key={company} value={company}>
                {company}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={company1}
            onChange={(e) => setCompany1(e.target.value)}
            placeholder="Enter Company 1"
            className="border border-gray-500 p-2 rounded-lg w-full bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-white placeholder-gray-400"
          />
        )}
      </div>

      {/* Company 2 */}
      <div className="flex flex-col w-full">
        {!custom2 ? (
          <select
            value={company2}
            onChange={(e) => {
              if (e.target.value === "Custom Entry") {
                setCustom2(true);
                setCompany2("");
              } else {
                setCompany2(e.target.value);
              }
            }}
            className="border border-gray-500 p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-white placeholder-white"
          >
            <option value="">Select Company 2</option>
            {companies.map((company) => (
              <option key={company} value={company}>
                {company}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={company2}
            onChange={(e) => setCompany2(e.target.value)}
            placeholder="Enter Company 2"
            className="border border-gray-500 p-2 rounded-lg w-full bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-white placeholder-gray-400"
          />
        )}
      </div>

    </div>
  );
}
