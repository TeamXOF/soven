"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import Link from "next/link";
import { useRef, useState } from "react";
import { Mic, Square, RotateCcw, ArrowRight, ShieldCheck } from "lucide-react";
import Brand from "@/components/soven/Brand";
import { useRecorder } from "@/hooks/useRecorder";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TryPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/onboarding/test");
  }, [router]);

  return (
    <div className="soven-auth-page flex items-center justify-center min-h-screen">
      <p className="text-sm text-text-muted">Redirecting to 20-Second Pre-Signup Voice Test...</p>
    </div>
  );
}
