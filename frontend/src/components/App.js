import React from "react";
import Signup from "./Signup";
import { Container } from "react-bootstrap";
import { AuthProvider } from "../contexts/AuthContext";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
import Login from "./Login";
import PrivateRoute from "./PrivateRoute";
import StreamlitEmbed from './StreamlitEmbed';  // Import your StreamlitEmbed component

function App() {
  return (
    <Router>
      <AuthProvider>
        <Switch>
          {/* StreamlitEmbed will take the full screen without the container */}
          <PrivateRoute exact path="/" component={StreamlitEmbed} />

          {/* Wrapped signup and login inside a container */}
          <Route path={["/signup", "/login"]}>
            <Container
              className="d-flex align-items-center justify-content-center"
              style={{ minHeight: "100vh" }}
            >
              <div className="w-100" style={{ maxWidth: "400px" }}>
                <Switch>
                  <Route path="/signup" component={Signup} />
                  <Route path="/login" component={Login} />
                </Switch>
              </div>
            </Container>
          </Route>
        </Switch>
      </AuthProvider>
    </Router>
  );
}

export default App;
