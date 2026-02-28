// components/LoadingBar.js
import React from 'react'

export default function LoadingBar(){
  return (
    <div style={{width: '100%', maxWidth: 640}}>
      <div className="loading-bar">
        <div className="inner"></div>
      </div>
      <div className="mt-3 text-xs text-sky-200 text-center">Processing file — constructing molecular spectrum</div>
    </div>
  )
}
