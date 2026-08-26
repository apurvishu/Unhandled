import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'SIH26006 Maritime Freight & Chartering Intelligence',
  description: 'AI-driven bulk cargo procurement, freight forecasting, vessel matching and port congestion prediction platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080e1a] text-slate-100 min-h-screen">
        <Providers>
          <AuthProvider>{children}</AuthProvider>
        </Providers>
      </body>
    </html>
  );
}
