import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'NAVIQ — Maritime Freight & Chartering Intelligence',
  description: 'AI-driven bulk cargo procurement, freight forecasting, vessel matching and port congestion prediction platform for SIH26006.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <Providers>
          <AuthProvider>{children}</AuthProvider>
        </Providers>
      </body>
    </html>
  );
}
