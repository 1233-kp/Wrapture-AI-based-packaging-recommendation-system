import logoSrc from '../../assets/wrapture-mark-sm.png'
import { cn } from '../../lib/utils'

/**
 * The Wrapture logo mark — a real image, always paired with the brand name
 * as actual text (never baked into the image) so the wordmark stays crisp
 * and uses the site's own font. `size` takes a Tailwind size-N token so
 * callers can drop it into the same slot the old colored-badge+icon
 * treatment used, at the same footprint.
 */
export function BrandMark({ size = 'size-9', className }) {
  return <img src={logoSrc} alt="" className={cn(size, 'shrink-0 object-contain', className)} />
}
