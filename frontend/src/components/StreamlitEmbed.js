import React from 'react';

const StreamlitEmbed = () => {
    return (
        <div style={{ width: '100vw', height: '100vh', margin: 0, padding: 0 }}>
            <iframe
                src="http://localhost:8501"  // URL where Streamlit is running
                width="100%"
                height="100%"
                frameBorder="0"
                title="Streamlit App"
                style={{ display: 'block', border: 'none' }}
            ></iframe>
        </div>
    );
};

export default StreamlitEmbed;
