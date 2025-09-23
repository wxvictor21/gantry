
import React, {useState} from 'react'
import { captureImage, gallery } from '../services/api'

export default function CameraControl(){
  const [status,setStatus]=useState('')
  const [img,setImg]=useState(null)

  async function onCapture(){
    const res = await captureImage()
    setStatus(JSON.stringify(res))
    if(res.file){
      setImg(res.file.startsWith('http') ? res.file : (window.location.origin + res.file))
    }
  }

  async function loadGallery(){
    const res = await gallery()
    if(res.photos && res.photos.length) setImg(res.photos[res.photos.length-1])
  }

  return (
    <div>
      <h2>Camera</h2>
      <button onClick={onCapture}>Capture</button>
      <button onClick={loadGallery}>Load last photo</button>
      <p>{status}</p>
      {img && <div><img src={img} style={{maxWidth:400}}/></div>}
    </div>
  )
}
