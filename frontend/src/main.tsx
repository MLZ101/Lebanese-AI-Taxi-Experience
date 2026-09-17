import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Self-hosted so the cabinet still looks right offline - a CDN miss here
// would drop us back to system sans and break the whole era.
import "@fontsource/press-start-2p";
import "@fontsource/vt323";

import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
