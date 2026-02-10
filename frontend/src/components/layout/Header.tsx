import { Link, useLocation } from "react-router";

const NAV_ITEMS = [
  { to: "/", label: "Upload" },
  { to: "/batch", label: "Batch" },
  { to: "/history", label: "History" },
];

export default function Header() {
  const location = useLocation();

  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link to="/" className="text-xl font-bold text-gray-900">
          LabelCheck
        </Link>
        <nav className="flex gap-4">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.to;
            const cls = `text-sm font-medium ${
              isActive ? "text-blue-600" : "text-gray-600 hover:text-gray-900"
            }`;
            // Plain <a> when already on "/" so the page fully reloads and resets state
            if (item.to === "/" && isActive) {
              return <a key={item.to} href="/" className={cls}>{item.label}</a>;
            }
            return (
              <Link key={item.to} to={item.to} className={cls}>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
