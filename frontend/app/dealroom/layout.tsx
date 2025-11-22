/**
 * Deal Room Layout
 *
 * Shared layout for deal room management pages.
 */

import { ReactNode } from 'react';

export default function DealRoomLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

export const metadata = {
  title: 'Deal Rooms - Sales OS',
  description: 'Manage your digital deal rooms for prospect engagement',
};
