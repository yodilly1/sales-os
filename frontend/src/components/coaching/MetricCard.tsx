'use client';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  changeLabel?: string;
  icon?: string;
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  icon,
  className = ''
}: MetricCardProps) {
  const isPositiveChange = change !== undefined && change > 0;
  const isNegativeChange = change !== undefined && change < 0;

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          {change !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              <span className={`text-sm font-medium ${
                isPositiveChange ? 'text-emerald-600' :
                isNegativeChange ? 'text-red-600' :
                'text-gray-500'
              }`}>
                {isPositiveChange && '+'}
                {change}%
              </span>
              {changeLabel && (
                <span className="text-sm text-gray-400">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <span className="text-3xl">{icon}</span>
        )}
      </div>
    </div>
  );
}

export default MetricCard;
