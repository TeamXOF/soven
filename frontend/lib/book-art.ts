export const BOOK_ART: Record<string, {
    image: string;
    description: string;
    ur: string;
    es: string;
}> = {
    story_forest_01: { image: "/illustrations/forest.webp", description: "A little courage. A very big adventure.", ur: "ایک ننھا لومڑ اور ایک بڑی مہم۔", es: "Un poco de valentía. Una gran aventura." },
    story_space_02: { image: "/illustrations/space.webp", description: "Count down to a sky full of possibilities.", ur: "ستاروں کی دنیا کی طرف سفر۔", es: "Cuenta regresiva hacia un cielo lleno de posibilidades." },
    story_ocean_03: { image: "/illustrations/ocean.webp", description: "Find your voice beneath the waves.", ur: "سمندر کی لہروں میں ایک نئی کہانی۔", es: "Encuentra tu voz bajo las olas." },
};
export function bookArt(id: string) { return BOOK_ART[id] ?? BOOK_ART.story_forest_01; }
