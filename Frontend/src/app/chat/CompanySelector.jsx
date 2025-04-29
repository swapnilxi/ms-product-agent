"use client";
import { useChatStore } from '@/services/chatApi';

export default function CompanySelector() {
  const { company1, setCompany1, company2, setCompany2 } = useChatStore();

  return (
    <div className="flex gap-4">
      <input
        type="text"
        value={company1}
        onChange={(e) => setCompany1(e.target.value)}
        placeholder="Enter Company 1"
        className="border p-2 rounded w-full"
      />
      <input
        type="text"
        value={company2}
        onChange={(e) => setCompany2(e.target.value)}
        placeholder="Enter Company 2"
        className="border p-2 rounded w-full"
      />
    </div>
  );
}
