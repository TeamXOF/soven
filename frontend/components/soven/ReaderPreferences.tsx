"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { useRef } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { loadPrefs, savePrefs } from "@/lib/prefs";
/** Hydrate once per identity/profile revision; a legacy default must not erase browser choices. */
export default function ReaderPreferences() {
    const { user } = useAuth();
    const { setLanguage } = useSpeakFlow();
    const applied = useRef("");
    useDeferredEffect(() => {
        const key = user ? `${user.id}:${user.profile?.version ?? 0}` : "";
        if (key && key !== applied.current) {
            const profile = user?.profile;
            const hasSavedProfile = profile && (profile.version > 1 || profile.native_language !== null);
            const prefs = hasSavedProfile ? savePrefs({ storyLanguage: profile.reading_language,
                biggerText: profile.accessibility.larger_text, wordTips: profile.accessibility.word_tips }) : loadPrefs();
            setLanguage(prefs.storyLanguage);
        }
        applied.current = key;
        document.documentElement.dataset.sovenContrast = user?.profile?.accessibility.high_contrast ? "high" : "normal";
        return () => { document.documentElement.dataset.sovenContrast = "normal"; };
    }, [user, setLanguage]);
    return null;
}
