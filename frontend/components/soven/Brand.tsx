import Link from "next/link";
import BrandMark from "@/components/brand/BrandMark";
export default function Brand({ light = false }: {
    light?: boolean;
}) {
    return <Link href="/" aria-label="SOVEN home" className={`soven-brand ${light ? "soven-brand-light" : ""}`}>
    <span className="soven-brand-icon"><BrandMark /></span><span>SOVEN</span>
  </Link>;
}
