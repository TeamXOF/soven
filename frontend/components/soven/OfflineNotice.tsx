"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { useState } from "react";
import { WifiOff } from "lucide-react";
export default function OfflineNotice() { const [offline, setOffline] = useState(false); useDeferredEffect(() => { const update = () => setOffline(!navigator.onLine); update(); window.addEventListener("online", update); window.addEventListener("offline", update); return () => { window.removeEventListener("online", update); window.removeEventListener("offline", update); }; }, []); return offline ? <div role="status" className="soven-offline"><WifiOff size={18}/><span>Your browser is offline. Reading analysis still needs a reachable SOVEN server with cached models. A disconnected browser cannot submit readings.</span></div> : null; }
