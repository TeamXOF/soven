"use client";
import { useAuth } from "@/components/auth/AuthProvider";
import Brand from "@/components/soven/Brand";
import { Activity, BookOpen, FileText, GraduationCap, History, Home, Languages, LineChart, LogOut, Mic, Settings, ShieldCheck, Target, Users, Wifi, WifiOff } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";

const teacherNav = [
  { name: "Teacher Hub", ur: "استاد", href: "/teacher", icon: GraduationCap },
  { name: "Students", ur: "طلبہ", href: "/students", icon: Users },
  { name: "Reading Sessions", ur: "ریکارڈنگ", href: "/sessions", icon: History },
  { name: "Pipeline Monitor", ur: "نگرانی", href: "/pipeline", icon: Activity },
  { name: "Reports", ur: "رپورٹ", href: "/reports", icon: FileText },
  { name: "Settings", ur: "ترتیبات", href: "/settings", icon: Settings }
];

const readerNav = [
  { name: "2D AI Book", ur: "2D کتاب", href: "/books", icon: BookOpen },
  { name: "Voice Stats", ur: "وائس ڈیٹا", href: "/my-progress", icon: LineChart },
  { name: "Mode & Language", ur: "موڈ اور زبان", href: "/profile", icon: Languages }
];

export function MobileReaderNav() {
  const { isTeacher, user } = useAuth();
  const path = usePathname();
  const ur = user?.profile?.interface_language === "ur";
  return (
    <nav aria-label="Mobile navigation" className="soven-mobile-links">
      {(isTeacher ? teacherNav.slice(0, 3) : readerNav).map(({ name, ur: label, href, icon: Icon }) => (
        <Link key={href} href={href} aria-current={path === href ? "page" : undefined}>
          <Icon size={14}/>{ur ? label : name}
        </Link>
      ))}
      <Link href="/settings">{ur ? "ترتیبات" : "Settings"}</Link>
    </nav>
  );
}

export default function Sidebar() {
  const { user, logout, isTeacher } = useAuth();
  const path = usePathname();
  const router = useRouter();
  const [online, setOnline] = useState(true);

  useEffect(() => {
    setOnline(typeof navigator !== "undefined" ? navigator.onLine : true);
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  const ur = user?.profile?.interface_language === "ur";
  const initials = (user?.name ?? "Reader").split(" ").slice(0, 2).map(p => p[0]).join("");

  return (
    <aside className="soven-sidebar">
      <Brand light/>

      {/* Online / Offline Synced Status Badge */}
      <div className="flex items-center gap-2 px-3 py-2 my-2 rounded-lg bg-white/10 text-xs text-white/90">
        <span className={`w-2 h-2 rounded-full ${online ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`}/>
        <span className="font-medium">{online ? "Online · Synced" : "Offline · Synced Locally"}</span>
      </div>

      <nav aria-label="Primary">
        {(isTeacher ? teacherNav : readerNav).map(({ name, ur: label, href, icon: Icon }) => (
          <Link key={href} href={href} aria-current={path === href || path.startsWith(href + "/") ? "page" : undefined}>
            <Icon size={18}/>{ur ? label : name}
          </Link>
        ))}
      </nav>

      <div className="soven-sidebar-bottom">
        <Link href="/privacy" className="soven-privacy-note">
          <ShieldCheck size={21}/>
          <span>
            <strong>{ur ? "آپ کی رازداری" : "Your reading, your privacy"}</strong>
            {ur ? "جانیں کہ آپ کی آواز کہاں جاتی ہے۔" : "Zero voice retention. Meta AI open weights."}
          </span>
        </Link>
        <div className="soven-sidebar-user">
          <span className="soven-avatar">{initials}</span>
          <div>
            <p>{user?.name}</p>
            <small>{isTeacher ? "Teacher" : user?.reader_mode === "dyslexia" ? "Dyslexia Reader" : user?.reader_mode === "adult" ? "Adult Reader" : "Child Reader"}</small>
          </div>
          <button aria-label="Log out" onClick={async () => { await logout(); router.replace("/login"); }}>
            <LogOut size={16}/>
          </button>
        </div>
      </div>
    </aside>
  );
}
