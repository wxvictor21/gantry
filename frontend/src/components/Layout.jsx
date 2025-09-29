import React from 'react';
import { Link } from 'react-router-dom';
import './Layout.css';

export default function Layout({ children }) {
  return (
    <div>
      <head>
        <title>ABENICS CHAMBER</title>
      </head>
      <nav style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--header-bg-color)', color: 'var(--header-text-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <img src="/logoATRIA.png" alt="Atria logo" style={{ height: '50px', marginRight: '1rem' }} />
        </div>
        <h1 style={{ margin: '0', flexGrow: 1, textAlign: 'center' }}>ABENICS CHAMBER</h1>
      </nav>
      <div style={{padding:20}}>
        {children}
      </div>
    </div>
  );
}
