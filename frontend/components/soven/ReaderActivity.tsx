"use client";
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
const Activity = createContext<{ busy: boolean; setBusy: (value: boolean) => void }>({ busy: false, setBusy: () => {} });
export function ReaderActivityProvider({ children }: { children: ReactNode }) {
  const [busy, setBusy] = useState(false);
  const value = useMemo(() => ({ busy, setBusy }), [busy]);
  return <Activity.Provider value={value}>{children}</Activity.Provider>;
}
export function useReaderActivity() { return useContext(Activity); }
