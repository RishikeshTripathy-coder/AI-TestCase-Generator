import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import theme from "./theme";
import "./App.css";
import Header from "./components/header/Header";
import Footer from "./components/footer/Footer";
import Home from "./components/home/Home";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import UserStory from "./components/user-story/UserStory";
import ContextTemplate from "./context-template/ContextTemplate";

function App() {
  console.count("App");
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <main className="main_container">
        <BrowserRouter>
          <Header />
          <div style={{ flex: 1 }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/context-template" element={<ContextTemplate />} />
              {/* <Route path="/create" element={<UserStory />} /> */}
            </Routes>
          </div>
          <Footer />
        </BrowserRouter>
      </main>
    </ThemeProvider>
  );
}

export default App;
