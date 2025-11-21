import React from 'react';

interface ExampleQueriesProps {
  onSelect: (query: string) => void;
}

const QUERIES = [
  "Find novel adhesive materials with high temperature resistance for automotive applications?",
  "What are the hardest ceramic materials for industrial abrasives and grinding wheels?",
  "Find biocompatible polymers for medical tape and wound dressings?",
  "Identify materials with high filtration efficiency and low pressure drop for respirator masks?"
];

export const ExampleQueries: React.FC<ExampleQueriesProps> = ({ onSelect }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
      {QUERIES.map((q, i) => (
        <button
          key={i}
          onClick={() => onSelect(q)}
          className="text-left p-4 rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50 transition-colors bg-white shadow-sm group"
        >
          <p className="text-sm font-medium text-slate-700 group-hover:text-blue-700">{q}</p>
        </button>
      ))}
    </div>
  );
};

