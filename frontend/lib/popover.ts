/**
 * Position a fixed-position popover relative to an anchor element's on-screen
 * rectangle — immune to any ancestor overflow-hidden/scroll clipping.
 * Horizontally clamped to the viewport; flips above the anchor when there
 * isn't room below.
 */
export function popoverPosition(
  anchor: DOMRect,
  width = 256,
  estimatedHeight = 280,
  margin = 8
): { left: number; top: number; openUp: boolean } {
  let left = anchor.left + anchor.width / 2 - width / 2;
  left = Math.max(margin, Math.min(left, window.innerWidth - width - margin));
  const below = anchor.bottom + margin;
  const openUp =
    below + estimatedHeight > window.innerHeight - margin &&
    anchor.top - estimatedHeight - margin > margin;
  const top = openUp ? anchor.top - margin : below;
  return { left, top, openUp };
}
