"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  Zap,
  BarChart3,
  Calendar,
  MessageCircle,
  Wand2,
  ArrowRight,
  Crown,
  LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getAccessToken } from "@/store/auth";

// Floating particle component
function Particle({ delay, duration, size, left, top }: {
  delay: number;
  duration: number;
  size: number;
  left: string;
  top: string;
}) {
  return (
    <div
      className="absolute rounded-full bg-gradient-to-br from-amber-400/20 to-yellow-200/10 blur-sm animate-float"
      style={{
        width: size,
        height: size,
        left,
        top,
        animationDelay: `${delay}s`,
        animationDuration: `${duration}s`,
      }}
    />
  );
}

// Feature card component
function FeatureCard({ icon: Icon, title, description, delay }: {
  icon: LucideIcon;
  title: string;
  description: string;
  delay: number;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={cn(
        "group relative p-6 rounded-2xl bg-white/[0.03] backdrop-blur-sm border border-amber-500/10 transition-all duration-700 hover:bg-white/[0.06] hover:border-amber-500/30 hover:scale-105",
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
      )}
    >
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-amber-500/5 to-yellow-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="relative">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center mb-4 shadow-lg shadow-amber-500/20 group-hover:scale-110 transition-transform">
          <Icon className="w-6 h-6 text-black" />
        </div>
        <h3 className="text-lg font-semibold text-amber-50 mb-2">{title}</h3>
        <p className="text-sm text-stone-400 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

// Platform icon component
function PlatformIcon({ children, delay }: { children: React.ReactNode; delay: number }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={cn(
        "w-11 h-11 sm:w-14 sm:h-14 rounded-xl sm:rounded-2xl bg-white/[0.03] backdrop-blur-sm border border-amber-500/20 flex items-center justify-center transition-all duration-500 hover:scale-110 hover:bg-amber-500/10 hover:border-amber-500/40",
        visible ? "opacity-100 scale-100" : "opacity-0 scale-50"
      )}
    >
      {children}
    </div>
  );
}

export default function HomePage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [entering, setEntering] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleEnter = () => {
    setEntering(true);
    const target = getAccessToken() ? "/dashboard" : "/login";
    setTimeout(() => {
      router.push(target);
    }, 800);
  };

  const features = [
    {
      icon: Calendar,
      title: "Smart Scheduling",
      description: "Plan and schedule your content across all platforms with our intuitive calendar.",
    },
    {
      icon: Wand2,
      title: "AI-Powered Captions",
      description: "Generate engaging captions and hashtags with advanced AI assistance.",
    },
    {
      icon: BarChart3,
      title: "Deep Analytics",
      description: "Track performance, growth, and engagement with beautiful visualizations.",
    },
    {
      icon: MessageCircle,
      title: "Unified Inbox",
      description: "Manage comments and mentions from all platforms in one place.",
    },
  ];

  // Generate particles with seeded random values (only on client to avoid hydration mismatch)
  const [particles, setParticles] = useState<Array<{
    id: number;
    delay: number;
    duration: number;
    size: number;
    left: string;
    top: string;
  }>>([]);

  useEffect(() => {
    // Generate particles only on client side to avoid hydration mismatch
    const generated = Array.from({ length: 15 }, (_, i) => ({
      id: i,
      delay: Math.random() * 5,
      duration: 12 + Math.random() * 10,
      size: 30 + Math.random() * 80,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
    }));
    setParticles(generated);
  }, []);

  return (
    <div
      className={cn(
        "min-h-screen relative overflow-hidden transition-all duration-1000",
        entering ? "opacity-0 scale-110" : "opacity-100 scale-100"
      )}
    >
      {/* Animated background - deep luxury black */}
      <div className="absolute inset-0 bg-[#0a0a0a]" />

      {/* Subtle texture overlay */}
      <div
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />

      {/* Gradient orbs - gold/champagne tones */}
      <div className="absolute top-1/4 -left-32 w-[500px] h-[500px] bg-amber-500/[0.07] rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 -right-32 w-[400px] h-[400px] bg-yellow-500/[0.05] rounded-full blur-[100px]" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-400/[0.03] rounded-full blur-[150px]" />

      {/* Accent line */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-32 bg-gradient-to-b from-transparent via-amber-500/50 to-transparent" />

      {/* Floating particles */}
      {particles.map((p) => (
        <Particle key={p.id} {...p} />
      ))}

      {/* Elegant grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(212,175,55,0.3) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(212,175,55,0.3) 1px, transparent 1px)`,
          backgroundSize: '80px 80px',
        }}
      />

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="p-4 sm:p-6 lg:p-8">
          <div
            className={cn(
              "flex items-center gap-3 transition-all duration-1000",
              mounted ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-8"
            )}
          >
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-amber-400 via-yellow-500 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/30">
              <Crown className="w-5 h-5 sm:w-6 sm:h-6 text-black" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold text-amber-50 tracking-tight font-display">
                Apulu Studio
              </h1>
              <p className="text-[10px] sm:text-xs text-stone-500">Premium Social Media Suite</p>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16">
          {/* Hero section */}
          <div className="text-center max-w-4xl mx-auto mb-16">
            <div
              className={cn(
                "inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-amber-500/10 to-yellow-500/10 border border-amber-500/20 mb-8 transition-all duration-1000",
                mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
              )}
              style={{ transitionDelay: "200ms" }}
            >
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span className="text-sm text-amber-200/80 font-medium">Powered by AI</span>
            </div>

            <h2
              className={cn(
                "text-3xl sm:text-5xl md:text-7xl font-bold mb-4 sm:mb-6 transition-all duration-1000 tracking-tight font-display",
                mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
              )}
              style={{ transitionDelay: "400ms" }}
            >
              <span className="text-stone-200">Your Social Media,</span>
              <br />
              <span className="bg-gradient-to-r from-amber-300 via-yellow-400 to-amber-500 bg-clip-text text-transparent">
                Elevated
              </span>
            </h2>

            <p
              className={cn(
                "text-sm sm:text-lg md:text-xl text-stone-400 max-w-2xl mx-auto mb-8 sm:mb-12 transition-all duration-1000 leading-relaxed",
                mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
              )}
              style={{ transitionDelay: "600ms" }}
            >
              Experience the art of social media management. Create stunning content,
              grow your audience, and elevate your brand presence.
            </p>

            {/* Platform icons */}
            <div
              className={cn(
                "flex items-center justify-center gap-2.5 sm:gap-4 mb-8 sm:mb-12 flex-wrap transition-all duration-1000",
                mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
              )}
              style={{ transitionDelay: "700ms" }}
            >
              <PlatformIcon delay={800}>
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-amber-200/70">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
              </PlatformIcon>
              <PlatformIcon delay={900}>
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-amber-200/70">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
              </PlatformIcon>
              <PlatformIcon delay={1000}>
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-amber-200/70">
                  <path d="M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565.139 1.908 0 3.08 0 3.768c0 .69.378 5.65.624 6.479.815 2.736 3.713 3.66 6.383 3.364.136-.02.275-.039.415-.056-.138.022-.276.04-.415.056-3.912.58-7.387 2.005-2.83 7.078 5.013 5.19 6.87-1.113 7.823-4.308.953 3.195 2.05 9.271 7.733 4.308 4.267-4.308 1.172-6.498-2.74-7.078a8.741 8.741 0 01-.415-.056c.14.017.279.036.415.056 2.67.297 5.568-.628 6.383-3.364.246-.828.624-5.79.624-6.478 0-.69-.139-1.861-.902-2.206-.659-.298-1.664-.62-4.3 1.24C16.046 4.748 13.087 8.687 12 10.8z"/>
                </svg>
              </PlatformIcon>
              <PlatformIcon delay={1100}>
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-amber-200/70">
                  <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
                </svg>
              </PlatformIcon>
              <PlatformIcon delay={1200}>
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-amber-200/70">
                  <path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.5 12.068V12c.015-3.58 1.205-6.333 3.509-8.183C6.96 2.172 9.814 1.322 13.332 1.322h.035c2.535.015 4.75.59 6.585 1.71a10.052 10.052 0 013.6 4.184l-2.227 1.07a7.764 7.764 0 00-2.764-3.185c-1.396-.859-3.09-1.302-5.031-1.318h-.025c-2.705 0-4.891.742-6.5 2.207-1.688 1.537-2.589 3.847-2.673 6.868v.061c.084 3.02.985 5.331 2.673 6.868 1.609 1.465 3.795 2.207 6.5 2.207h.056c2.21-.015 4.076-.555 5.545-1.606 1.378-.984 2.297-2.37 2.73-4.122h-8.36V12.69h10.943v.254c0 3.187-1.096 5.869-3.167 7.748-1.897 1.72-4.476 2.633-7.457 2.642l-.076-.001z"/>
                </svg>
              </PlatformIcon>
            </div>

            {/* Enter button - luxury gold */}
            <button
              onClick={handleEnter}
              className={cn(
                "group relative inline-flex items-center gap-2.5 sm:gap-3 px-8 sm:px-12 py-4 sm:py-5 rounded-full text-base sm:text-lg font-semibold transition-all duration-1000 hover:scale-105 active:scale-95",
                mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
              )}
              style={{ transitionDelay: "800ms" }}
            >
              {/* Button glow */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-amber-400 via-yellow-400 to-amber-500 opacity-0 group-hover:opacity-100 blur-2xl transition-opacity duration-500" />

              {/* Button background */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-amber-400 via-yellow-500 to-amber-500 shadow-2xl shadow-amber-500/30" />

              {/* Inner border effect */}
              <div className="absolute inset-[1px] rounded-full bg-gradient-to-b from-yellow-300/20 to-transparent" />

              {/* Button content */}
              <span className="relative flex items-center gap-3 text-black font-bold tracking-wide">
                <Crown className="w-5 h-5" />
                Enter Studio
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </button>

            {/* Decorative line below button */}
            <div
              className={cn(
                "mt-12 flex items-center justify-center gap-3 transition-all duration-1000",
                mounted ? "opacity-100" : "opacity-0"
              )}
              style={{ transitionDelay: "1000ms" }}
            >
              <div className="w-12 h-[1px] bg-gradient-to-r from-transparent to-amber-500/50" />
              <span className="text-xs text-stone-600 uppercase tracking-[0.2em]">Premium Experience</span>
              <div className="w-12 h-[1px] bg-gradient-to-l from-transparent to-amber-500/50" />
            </div>
          </div>

          {/* Features grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 max-w-6xl mx-auto w-full">
            {features.map((feature, index) => (
              <FeatureCard
                key={feature.title}
                {...feature}
                delay={1000 + index * 150}
              />
            ))}
          </div>
        </main>

        {/* Footer */}
        <footer className="p-4 sm:p-8 text-center">
          <p
            className={cn(
              "text-sm text-stone-600 transition-all duration-1000",
              mounted ? "opacity-100" : "opacity-0"
            )}
            style={{ transitionDelay: "1500ms" }}
          >
            v0.1.0 Beta &middot; Crafted with precision
          </p>
        </footer>
      </div>

      {/* Custom styles for animations */}
      <style jsx>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0) rotate(0deg);
            opacity: 0.2;
          }
          50% {
            transform: translateY(-30px) rotate(180deg);
            opacity: 0.4;
          }
        }
        .animate-float {
          animation: float 12s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
