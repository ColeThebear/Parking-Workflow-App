import { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import TopNav from "./TopNav";
import Sidebar from "./Sidebar";

const MOBILE_BP = 768; // px — matches Tailwind's `md:`

export default function Layout() {
  const isMobileInit = typeof window !== "undefined" && window.innerWidth < MOBILE_BP;

  // Desktop: collapsed = icon-only. Mobile: collapsed = hidden.
  const [collapsed, setCollapsed] = useState(isMobileInit);
  const [isMobile,  setIsMobile]  = useState(isMobileInit);

  useEffect(() => {
    function onResize() {
      const mobile = window.innerWidth < MOBILE_BP;
      setIsMobile(mobile);
      if (!mobile) setCollapsed(false);   // always show on desktop after resize
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <TopNav onMenuClick={() => setCollapsed((c) => !c)} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((c) => !c)}
          mobile={isMobile}
          onClose={() => setCollapsed(true)}
        />

        <main className="flex-1 overflow-auto bg-gray-50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
