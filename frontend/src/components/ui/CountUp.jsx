import { useInView, useMotionValue, useReducedMotion, useSpring } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'

/**
 * Animated numeric counter that counts up when it scrolls into view.
 * Pattern informed by 21st.dev's "Count Animation" (bundui) — Tailwind + Framer
 * Motion viewport-triggered counters — built here directly against our design
 * tokens rather than pulled verbatim (that component's code wasn't retrievable
 * this session; daily 21st fetch quota was exhausted after 2 pulls).
 */
export function CountUp({ value, duration = 1.4, className, suffix = '', prefix = '', decimals = 0 }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-10% 0px' })
  const reduceMotion = useReducedMotion()
  const motionValue = useMotionValue(0)
  const spring = useSpring(motionValue, { duration: reduceMotion ? 0 : duration * 1000, bounce: 0 })
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    if (inView) motionValue.set(value)
  }, [inView, value, motionValue])

  useEffect(() => {
    const unsub = spring.on('change', (v) => setDisplay(v))
    return unsub
  }, [spring])

  return (
    <span ref={ref} className={className}>
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  )
}
