"use client";

import { useState } from "react";
import Targets from "./components/Targets";
import Tweets from "./components/Tweets";
import Analysis from "./components/Analysis";
import Schedules from "./components/Schedules";
import Settings from "./components/Settings";

type View = "targets" | "tweets" | "analysis" | "schedules" | "settings";

const NAV_ITEMS: { key: View; label: string }[] = [
  { key: "targets", label: "Targets" },
  { key: "tweets", label: "Tweets" },
  { key: "analysis", label: "Analysis" },
  { key: "schedules", label: "Schedules" },
  { key: "settings", label: "Settings" },
];

export default function Home() {
  const [view, setView] = useState<View>("targets");

  return (
    <div className="shell">
      <nav className="sidebar">
        <h1>SocialScope</h1>
        {NAV_ITEMS.map(({ key, label }) => (
          <a
            key={key}
            href="#"
            className={view === key ? "active" : ""}
            onClick={(e) => {
              e.preventDefault();
              setView(key);
            }}
          >
            {label}
          </a>
        ))}
      </nav>
      <main className="main">
        {view === "targets" && <Targets />}
        {view === "tweets" && <Tweets />}
        {view === "analysis" && <Analysis />}
        {view === "schedules" && <Schedules />}
        {view === "settings" && <Settings />}
      </main>
    </div>
  );
}
