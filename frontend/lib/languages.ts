import registry from "../../shared/languages.json";
import { READING_LANGUAGES } from "./language-types";
import type { LanguageCode, ReadingLanguage } from "./language-types";

export type { LanguageCode, ReadingLanguage } from "./language-types";
export type LanguageDefinition = (typeof registry.languages)[number];
export const LANGUAGE_CATALOG: readonly LanguageDefinition[] = registry.languages;

export function isReadingLanguage(value: unknown): value is ReadingLanguage {
  return typeof value === "string" && (READING_LANGUAGES as readonly string[]).includes(value);
}

export function isLanguageCode(value: unknown): value is LanguageCode {
  return typeof value === "string" && LANGUAGE_CATALOG.some((language) => language.code === value);
}

// Language roles stay separate even while the old screens use storyLanguage.
export type ReaderLanguagePreferences = {
  readingLanguage: ReadingLanguage;
  interfaceLanguage: LanguageCode;
  nativeLanguage: LanguageCode | null;
  translationLanguage: LanguageCode | null;
};

export type ProviderCapability = {
  id: string;
  task: string;
  implementation: "existing" | "planned";
  availability: string;
  word_timing?: string;
  confidence?: string;
  adapter_implemented?: boolean;
  offline_guaranteed?: boolean;
};

export type PlatformCapabilities = {
  schema_version: number;
  language_catalog: typeof registry;
  providers: ProviderCapability[];
  language_speech?: {schema_version:number; languages:Record<string,{locale:string;recognition:string[];playback:string}>; notice:string};
  notice: string;
};
