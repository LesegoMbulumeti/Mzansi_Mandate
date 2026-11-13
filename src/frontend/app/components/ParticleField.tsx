"use client";

import { useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

export function ParticleField() {
  const [ready, setReady] = useState(false);
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let mounted = true;
    const screenQuery = window.matchMedia("(max-width: 680px)");
    setCompact(screenQuery.matches);
    const updateScreen = (event: MediaQueryListEvent) => setCompact(event.matches);
    screenQuery.addEventListener("change", updateScreen);
    void initParticlesEngine(async (engine) => loadSlim(engine)).then(() => {
      if (mounted) setReady(true);
    });
    return () => {
      mounted = false;
      screenQuery.removeEventListener("change", updateScreen);
    };
  }, []);

  if (!ready) return null;
  return (
    <Particles
      id="mandate-particles"
      className="particle-field"
      options={{
        fullScreen: { enable: false },
        detectRetina: true,
        fpsLimit: 45,
        particles: {
          color: { value: ["#70b6ff", "#a6cfff", "#ffffff"] },
          links: { enable: true, color: "#6ca9f5", distance: compact ? 108 : 142, opacity: 0.2, width: 1 },
          move: { enable: true, speed: 0.42, outModes: { default: "out" } },
          number: { value: compact ? 20 : 38, density: { enable: true } },
          opacity: { value: { min: 0.12, max: 0.48 } },
          shape: { type: "circle" },
          size: { value: { min: 1, max: 2.7 } },
        },
        interactivity: {
          events: { onHover: { enable: !compact, mode: "grab" }, resize: { enable: true } },
          modes: { grab: { distance: 145, links: { opacity: 0.32 } } },
        },
        pauseOnBlur: true,
        pauseOnOutsideViewport: true,
      }}
    />
  );
}
