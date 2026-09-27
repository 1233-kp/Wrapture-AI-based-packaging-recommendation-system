import { Canvas, useFrame } from '@react-three/fiber'
import { Html, RoundedBox } from '@react-three/drei'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { DoubleSide } from 'three'

// Deliberately cheap scene for mobile safety: no shadows, no postprocessing,
// no transmission material (real glass transmission needs an extra render
// pass and is one of the more expensive three.js materials) — the
// "transparent container" look here is a couple of low-opacity RoundedBox
// shells (suggesting a laminated film), and the "mango" is a few low-segment
// primitives, not an imported model.

const TONE_CLASSES = {
  teal: 'border-teal-200 bg-teal-50/90 text-teal-700',
  brand: 'border-brand-200 bg-brand-50/90 text-brand-700',
  amber: 'border-amber-200 bg-amber-50/90 text-amber-700',
}

function Label({ position, title, value, tone }) {
  return (
    <Html position={position} center transform={false} occlude={false} className="pointer-events-none">
      <div
        className={`whitespace-nowrap rounded-pill border px-2.5 py-1 text-[10px] font-bold shadow-soft-sm backdrop-blur-sm ${TONE_CLASSES[tone]}`}
      >
        <span className="opacity-70">{title}</span> {value}
      </div>
    </Html>
  )
}

function Mango() {
  return (
    <group>
      <mesh scale={[0.85, 1.05, 0.85]}>
        <icosahedronGeometry args={[1, 1]} />
        <meshStandardMaterial color="#f5a623" roughness={0.55} />
      </mesh>
      <mesh position={[0, 1.05, 0]}>
        <cylinderGeometry args={[0.05, 0.07, 0.18, 6]} />
        <meshStandardMaterial color="#6b4a2f" roughness={0.8} />
      </mesh>
    </group>
  )
}

// Two nested shells rather than one solid wall — reads as a thin packaging
// film with a barrier layer, without adding real geometry cost (still just
// two cheap transparent boxes).
function Container() {
  return (
    <>
      <RoundedBox args={[2.5, 2.5, 2.5]} radius={0.2} smoothness={2}>
        <meshPhysicalMaterial color="#bfe8e0" transparent opacity={0.14} roughness={0.15} side={DoubleSide} />
      </RoundedBox>
      <RoundedBox args={[2.38, 2.38, 2.38]} radius={0.18} smoothness={2}>
        <meshPhysicalMaterial color="#8fd6c9" transparent opacity={0.08} roughness={0.2} side={DoubleSide} />
      </RoundedBox>
    </>
  )
}

const GAS_COLORS = { o2: '#0891b2', moisture: '#059669', co2: '#d97706' }

function GasParticles() {
  const particles = useMemo(
    () =>
      [...Array(6)].map((_, i) => ({
        id: i,
        gas: ['o2', 'moisture', 'co2'][i % 3],
        angle: (i / 6) * Math.PI * 2,
        radiusStart: 1.75,
        speed: 0.4 + (i % 3) * 0.08,
        yOffset: ((i % 3) - 1) * 0.5,
      })),
    []
  )
  const groupRef = useRef(null)

  useFrame((state) => {
    if (!groupRef.current) return
    groupRef.current.children.forEach((mesh, i) => {
      const p = particles[i]
      const t = (state.clock.elapsedTime * p.speed + i) % 1
      const radius = p.radiusStart - t * 0.85
      mesh.position.set(Math.cos(p.angle) * radius, p.yOffset + Math.sin(t * Math.PI) * 0.15, Math.sin(p.angle) * radius)
      mesh.material.opacity = 0.9 * (1 - t)
    })
  })

  return (
    <group ref={groupRef}>
      {particles.map((p) => (
        <mesh key={p.id}>
          <sphereGeometry args={[0.035, 6, 6]} />
          <meshBasicMaterial color={GAS_COLORS[p.gas]} transparent opacity={0.9} />
        </mesh>
      ))}
    </group>
  )
}

function Scene({ reducedMotion, simplified, shelfLifeLabel, sustainabilityLabel, materialLabel }) {
  const productRef = useRef(null)

  useFrame((_, delta) => {
    if (reducedMotion || !productRef.current) return
    productRef.current.rotation.y += delta * (simplified ? 0.18 : 0.3)
  })

  return (
    <>
      <ambientLight intensity={0.9} />
      <directionalLight position={[3, 4, 5]} intensity={1.1} />

      <group ref={productRef}>
        <Mango />
        <Container />
        {!simplified && !reducedMotion && <GasParticles />}
      </group>

      <Label position={[1.15, 1.1, 0.2]} title="OTR" value="19,000" tone="teal" />
      <Label position={[-1.15, 0.5, 0.5]} title="WVTR" value="42.5" tone="brand" />
      <Label position={[1.05, -1.0, -0.2]} title={shelfLifeLabel} value="4.4d" tone="amber" />
      <Label position={[-1.05, -0.85, 0.6]} title={sustainabilityLabel} value="100" tone="brand" />
      <Html position={[0, -1.3, 0]} center transform={false} occlude={false} className="pointer-events-none">
        <div className="whitespace-nowrap rounded-pill border border-ink-200 bg-white/95 px-3 py-1 text-[11px] font-bold text-ink-700 shadow-soft-sm backdrop-blur-sm">
          {materialLabel}
        </div>
      </Html>
    </>
  )
}

export default function HeroScene({ simplified = false }) {
  const { t } = useTranslation()
  const [reducedMotion, setReducedMotion] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = (e) => setReducedMotion(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  return (
    <div className="relative mx-auto aspect-square w-full max-w-80">
      <Canvas
        dpr={simplified ? 1 : [1, 1.5]}
        gl={{ antialias: !simplified, alpha: true, powerPreference: 'low-power' }}
        camera={{ position: [0, 0, 6], fov: 38 }}
      >
        <Scene
          reducedMotion={reducedMotion}
          simplified={simplified}
          shelfLifeLabel={t('results.shelfLife')}
          sustainabilityLabel={t('results.sustainability')}
          materialLabel="Vented PET"
        />
      </Canvas>
    </div>
  )
}
