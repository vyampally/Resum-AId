import { useEffect } from 'react';  // Import only what is needed

const StreamlitRedirect = () => {
    useEffect(() => {
        // Redirect to the Streamlit app's URL (replace localhost:8501 with the actual port)
        window.location.href = "http://localhost:8501/";  // URL where Streamlit is running
    }, []);  // This runs the redirect only once when the component mounts

    return null;  // No need to render anything
};

export default StreamlitRedirect;