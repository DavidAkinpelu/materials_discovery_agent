import React from 'react';

interface MaterialsTableProps {
  materials: any[];
}

export const MaterialsTable: React.FC<MaterialsTableProps> = ({ materials }) => {
  if (!materials || materials.length === 0) return null;
  
  // Filter out error objects
  const validMaterials = materials.filter(m => !m.error);
  if (validMaterials.length === 0) return null;

  const keys = Object.keys(validMaterials[0]).filter(key => key !== 'error');
  
  // Helper to format key names (e.g., "material_id" -> "Material ID")
  const formatKey = (key: string) => {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  // Helper to format values
  const formatValue = (value: any) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'object') return JSON.stringify(value);
    if (typeof value === 'number') return value.toFixed(3);
    return value;
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-100">
          <tr>
            {keys.map((key) => (
              <th key={key} className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                {formatKey(key)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-100">
          {validMaterials.map((material, idx) => (
            <tr key={material.material_id || idx} className="hover:bg-slate-50 transition-colors">
              {keys.map((key) => (
                <td key={key} className="px-5 py-3 text-sm text-slate-700">
                  {formatValue(material[key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

