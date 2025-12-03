import { useMemo } from "react";

interface LineChartData {
  label: string;
  value: number;
}

interface SimpleLineChartProps {
  data: LineChartData[];
  title?: string;
  height?: number;
  maxValue?: number;
  color?: string;
}

export const SimpleLineChart = ({
  data,
  title,
  height = 200,
  maxValue,
  color = "#e90118",
}: SimpleLineChartProps) => {
  const max = useMemo(() => {
    if (maxValue !== undefined) return maxValue;
    return Math.max(...data.map((d) => d.value), 0) || 1;
  }, [data, maxValue]);

  const points = useMemo(() => {
    const width = 100;
    const step = width / (data.length - 1 || 1);
    return data.map((item, index) => {
      const x = index * step;
      const y = height - (item.value / max) * height;
      return { x, y, value: item.value, label: item.label };
    });
  }, [data, max, height]);

  const path = useMemo(() => {
    if (points.length === 0) return "";
    const pathParts = points.map((point, index) => {
      if (index === 0) {
        return `M ${point.x}% ${point.y}`;
      }
      return `L ${point.x}% ${point.y}`;
    });
    return pathParts.join(" ");
  }, [points]);

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
          
          {/* Line */}
          <path
            d={path}
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Points */}
          {points.map((point, index) => (
            <g key={index}>
              <circle
                cx={`${point.x}%`}
                cy={point.y}
                r="4"
                fill={color}
                className="hover:r-6 transition-all"
              />
              <text
                x={`${point.x}%`}
                y={point.y - 10}
                textAnchor="middle"
                className="text-xs fill-gray-700"
                fontSize="10"
              >
                {point.value.toFixed(1)}
              </text>
            </g>
          ))}
        </svg>
        
        {/* Labels */}
        <div className="flex justify-between mt-2">
          {data.map((item, index) => (
            <div
              key={index}
              className="text-xs text-gray-600 text-center"
              style={{ width: `${100 / data.length}%` }}
            >
              {item.label.length > 8
                ? `${item.label.substring(0, 8)}...`
                : item.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

