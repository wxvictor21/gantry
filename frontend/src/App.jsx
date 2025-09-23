import React from 'react'
import MotorControl from './components/MotorControl'
import CameraControl from './components/CameraControl'

export default function App(){
  return (
    <div style={{padding:20}}>
      <h1>Gantry Control</h1>
      <MotorControl />
      <hr />
      <CameraControl />
    </div>
  )
}
