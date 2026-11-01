export const BOOK_ART: Record<string, {
    image: string;
    description: string;
    ur: string;
}> = {
    story_forest_01: { image: "/illustrations/forest.webp", description: "A little courage. A very big adventure.", ur: "ایک ننھا لومڑ اور ایک بڑی مہم۔" },
    story_space_02: { image: "/illustrations/space.webp", description: "Count down to a sky full of possibilities.", ur: "ستاروں کی دنیا کی طرف سفر۔" },
    story_ocean_03: { image: "/illustrations/ocean.webp", description: "Find your voice beneath the waves.", ur: "سمندر کی لہروں میں ایک نئی کہانی۔" },
};
export function bookArt(id: string) { return BOOK_ART[id] ?? BOOK_ART.story_forest_01; }
