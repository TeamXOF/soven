"use client";

import { useEffect,type DependencyList,type EffectCallback } from "react";

/** Schedule external initialization after commit; cancel safely in Strict Mode. */
export function useDeferredEffect(effect: EffectCallback, dependencies: DependencyList) {
  useEffect(() => {
    let cleanup: ReturnType<EffectCallback>;
    const timer = setTimeout(() => { cleanup = effect(); }, 0);
    return () => {
      clearTimeout(timer);
      if (typeof cleanup === "function") cleanup();
    };
    // The caller supplies an effect dependency list, checked by ESLint there.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
}
