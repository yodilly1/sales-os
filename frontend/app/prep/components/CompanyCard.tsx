"use client";

interface CompanyResearch {
  name: string;
  website?: string;
  industry?: string;
  size?: string;
  headquarters?: string;
  description?: string;
  recent_news?: string[];
  key_initiatives?: string[];
  tech_stack?: string[];
  funding_stage?: string;
  annual_revenue?: string;
  existing_customer?: boolean;
  current_products?: string[];
}

interface CompanyCardProps {
  company: CompanyResearch;
}

export function CompanyCard({ company }: CompanyCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center text-white font-bold text-xl">
              {company.name.charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {company.name}
              </h2>
              {company.industry && (
                <p className="text-sm text-gray-500">{company.industry}</p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {company.existing_customer && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                Existing Customer
              </span>
            )}
            {company.website && (
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <svg
                  className="w-4 h-4 mr-1.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
                Website
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-5 space-y-6">
        {/* Overview */}
        {company.description && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Overview</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              {company.description}
            </p>
          </div>
        )}

        {/* Quick Facts */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {company.size && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Company Size
              </p>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {company.size}
              </p>
            </div>
          )}
          {company.headquarters && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Headquarters
              </p>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {company.headquarters}
              </p>
            </div>
          )}
          {company.funding_stage && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Funding Stage
              </p>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {company.funding_stage}
              </p>
            </div>
          )}
          {company.annual_revenue && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Annual Revenue
              </p>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {company.annual_revenue}
              </p>
            </div>
          )}
        </div>

        {/* Recent News */}
        {company.recent_news && company.recent_news.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Recent News
            </h3>
            <ul className="space-y-2">
              {company.recent_news.map((news, index) => (
                <li
                  key={index}
                  className="flex items-start text-sm text-gray-600"
                >
                  <svg
                    className="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  {news}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Key Initiatives */}
        {company.key_initiatives && company.key_initiatives.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Key Initiatives
            </h3>
            <div className="flex flex-wrap gap-2">
              {company.key_initiatives.map((initiative, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700"
                >
                  {initiative}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Tech Stack */}
        {company.tech_stack && company.tech_stack.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Tech Stack
            </h3>
            <div className="flex flex-wrap gap-2">
              {company.tech_stack.map((tech, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Current Products (if existing customer) */}
        {company.existing_customer &&
          company.current_products &&
          company.current_products.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Current Products
              </h3>
              <div className="flex flex-wrap gap-2">
                {company.current_products.map((product, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700"
                  >
                    {product}
                  </span>
                ))}
              </div>
            </div>
          )}
      </div>
    </div>
  );
}
