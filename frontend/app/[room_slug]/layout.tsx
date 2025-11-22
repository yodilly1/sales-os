/**
 * Public Deal Room Layout
 *
 * Layout for public deal room viewing experience.
 */

import { ReactNode } from 'react';

export default function PublicRoomLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

export const metadata = {
  title: 'Deal Room',
  description: 'View shared deal room content',
};
