'use client';

import Image from 'next/image';
import type { TeamMember } from '@/types/coaching';

interface TeamLeaderboardProps {
  members: TeamMember[];
  className?: string;
}

function getTrendIcon(trend: 'up' | 'down' | 'stable'): { icon: string; color: string } {
  switch (trend) {
    case 'up':
      return { icon: '↑', color: 'text-emerald-500' };
    case 'down':
      return { icon: '↓', color: 'text-red-500' };
    default:
      return { icon: '→', color: 'text-gray-400' };
  }
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600';
  if (score >= 60) return 'text-amber-600';
  return 'text-red-600';
}

function getRankBadge(rank: number): { bg: string; text: string } {
  switch (rank) {
    case 1:
      return { bg: 'bg-amber-100', text: 'text-amber-700' };
    case 2:
      return { bg: 'bg-gray-100', text: 'text-gray-600' };
    case 3:
      return { bg: 'bg-orange-100', text: 'text-orange-700' };
    default:
      return { bg: 'bg-gray-50', text: 'text-gray-500' };
  }
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export function TeamLeaderboard({ members, className = '' }: TeamLeaderboardProps) {
  const sortedMembers = [...members].sort((a, b) => b.averageScore - a.averageScore);

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Team Leaderboard</h2>
        <span className="text-sm text-gray-500">{members.length} members</span>
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                Rank
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                Team Member
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                Calls
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                Avg Score
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                Trend
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                SPICED Breakdown
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedMembers.map((member, index) => {
              const rank = index + 1;
              const rankBadge = getRankBadge(rank);
              const trend = getTrendIcon(member.trend);

              return (
                <tr key={member.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${rankBadge.bg} ${rankBadge.text} font-bold text-sm`}>
                      {rank}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      {member.avatar ? (
                        <Image
                          src={member.avatar}
                          alt={member.name}
                          width={40}
                          height={40}
                          className="rounded-full"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {getInitials(member.name)}
                          </span>
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-gray-900">{member.name}</p>
                        <p className="text-sm text-gray-500">{member.role}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="text-gray-900 font-medium">{member.totalCalls}</span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className={`text-lg font-bold ${getScoreColor(member.averageScore)}`}>
                      {member.averageScore}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className={`text-lg ${trend.color}`}>{trend.icon}</span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex justify-end gap-1">
                      {(['situation', 'pain', 'impact', 'criticalEvent', 'decision'] as const).map((key) => (
                        <div key={key} className="text-center w-10">
                          <p className="text-xs text-gray-400 uppercase">{key[0]}</p>
                          <p className={`text-sm font-medium ${getScoreColor(member.recentScores[key])}`}>
                            {member.recentScores[key]}
                          </p>
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-3">
        {sortedMembers.map((member, index) => {
          const rank = index + 1;
          const rankBadge = getRankBadge(rank);
          const trend = getTrendIcon(member.trend);

          return (
            <div key={member.id} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-start gap-3">
                <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${rankBadge.bg} ${rankBadge.text} font-bold text-sm flex-shrink-0`}>
                  {rank}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {member.avatar ? (
                      <Image
                        src={member.avatar}
                        alt={member.name}
                        width={32}
                        height={32}
                        className="rounded-full"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-xs font-medium text-blue-600">
                          {getInitials(member.name)}
                        </span>
                      </div>
                    )}
                    <div>
                      <p className="font-medium text-gray-900">{member.name}</p>
                      <p className="text-xs text-gray-500">{member.role}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-gray-500">Avg Score</span>
                      <span className={`ml-2 text-lg font-bold ${getScoreColor(member.averageScore)}`}>
                        {member.averageScore}
                      </span>
                      <span className={`ml-1 ${trend.color}`}>{trend.icon}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-gray-500">Calls</span>
                      <span className="ml-2 font-medium text-gray-900">{member.totalCalls}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TeamLeaderboard;
