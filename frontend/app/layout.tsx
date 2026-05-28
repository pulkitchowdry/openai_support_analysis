import "./globals.css";

export const metadata = {
  title: "OpenAI Support Intelligence",
  description: "Developer issue analytics for the OpenAI API ecosystem"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
