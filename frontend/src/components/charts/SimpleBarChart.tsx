import { useMemo } from "react";

interface BarChartData {
  label: string;
  value: number;
  color?: string;
}

interface SimpleBarChartProps {
  data: BarChartData[];
  title?: string;
  height?: number;
  maxValue?: number;
}

export const SimpleBarChart = ({
  data,
  title,
  height = 200,
  maxValue,
}: SimpleBarChartProps) => {
  const max = useMemo(() => {
    if (maxValue !== undefined) return maxValue;
    return Math.max(...data.map((d) => d.value), 0) || 1;
  }, [data, maxValue]);

  const barWidth = 100 / data.length;

  return (
    <div className="w-full">
      {title && (
        <h3 className="text-sm font-semibold text-brand-gray mb-4">{title}</h3>
      )}
      <div className="relative" style={{ height: `${height}px` }}>
        <svg width="100%" height={height} className="overflow-visible">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = height - ratio * height;
            return (
              <line
                key={ratio}
                x1="0"
                y1={y}
                x2="100%"
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
            );
          })}
          
          {/* Bars */}
          {data.map((item, index) => {
            const barHeight = (item.value / max) * height;
            const x = (index * barWidth) + "%";
            const width = `${barWidth * 0.8}%`;
            const y = height - barHeight;
            
            return (
              <g key={index}>
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={barHeight}
                  fill={item.color || "#e90118"}
                  rx="4"
                  className="hover:opacity-80 transition-opacity"
                />
                <text
                  x={`${parseFloat(x) + parseFloat(width) / 2}%`}
                  y={y - 5}
                  textAnchor="middle"
                  className="text-xs fill-gray-700"
                  fontSize="12"
                >
                  {item.value.toFixed(1)}
                </text>
              </g>
            );
          })}
        </svg>
        
        {/* Labels */}
        <div className="flex justify-between mt-2">
          {data.map((item, index) => (
            <div
              key={index}
              className="text-xs text-gray-600 text-center"
              style={{ width: `${barWidth}%` }}
            >
              {item.label.length > 10
                ? `${item.label.substring(0, 10)}...`
                : item.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

