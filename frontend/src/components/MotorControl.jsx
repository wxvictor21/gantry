
import React, {useState} from 'react'
import { moveCamera } from '../services/api'

export default function MotorControl(){
  const [x,setX]=useState(0)
  const [y,setY]=useState(0)
  const [status,setStatus]=useState('')

  async function onMove(){
    const res = await moveCamera(Number(x), Number(y), 1500)
    setStatus(JSON.stringify(res))
  }

  return (
    <div>
      <h2>Motor Control</h2>
      <input value={x} onChange={e=>setX(e.target.value)} placeholder='X' />
      <input value={y} onChange={e=>setY(e.target.value)} placeholder='Y' />
      <button onClick={onMove}>Move</button>
      <pre>{status}</pre>
    </div>
  )
}
