import { Component } from 'react'

// The 3D hero is a progressive enhancement — anything that goes wrong while
// mounting or rendering it (WebGL context creation, a driver quirk, etc.)
// should silently fall back to the static hero card rather than break the
// page. This must be a class component: React has no hook-based equivalent
// for componentDidCatch/getDerivedStateFromError.
export class Hero3DErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error) {
    console.error('Hero 3D scene failed, falling back to static hero card.', error)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}
