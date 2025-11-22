"use client";

type FilterPeriod = "today" | "week" | "month" | "all";

interface PrepFiltersProps {
  currentPeriod: FilterPeriod;
  onPeriodChange: (period: FilterPeriod) => void;
}

export function PrepFilters({ currentPeriod, onPeriodChange }: PrepFiltersProps) {
  const periods: { value: FilterPeriod; label: string }[] = [
    { value: "today", label: "Today" },
    { value: "week", label: "This Week" },
    { value: "month", label: "This Month" },
    { value: "all", label: "All Upcoming" },
  ];

  return (
    <div className="mb-6">
      <div className="flex items-center space-x-2 bg-gray-100 p-1 rounded-lg w-fit">
        {periods.map((period) => (
          <button
            key={period.value}
            onClick={() => onPeriodChange(period.value)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              currentPeriod === period.value
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {period.label}
          </button>
        ))}
      </div>
    </div>
  );
}
