"use client";

import { TutorSession } from "@/components/TutorSession";

export default function Home() {
  return (
    <main className="app-container">
      <header className="app-header">
        <h1>Socratic AI Tutor</h1>
        <p className="subtitle">Learn through questions, not answers</p>
      </header>
      <TutorSession />
    </main>
  );
}
