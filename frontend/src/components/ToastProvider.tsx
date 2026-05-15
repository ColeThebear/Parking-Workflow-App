import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  ReactNode,
} from "react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextType {
  showToast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

const TOAST_DURATION_MS = 3500;
const MAX_VISIBLE_TOASTS = 4;

const STYLES: Record<ToastType, string> = {
  success: "bg-green-50 border border-green-200 text-green-800",
  error:   "bg-red-50   border border-red-200   text-red-800",
  info:    "bg-blue-50  border border-blue-200  text-blue-800",
};

const ICONS: Record<ToastType, string> = {
  success: "✓",
  error:   "!",
  info:    "i",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counter = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (type: ToastType, message: string) => {
      const id = ++counter.current; // always unique — never collides

      setToasts((prev) => {
        const next = [...prev, { id, type, message }];
        return next.length > MAX_VISIBLE_TOASTS
          ? next.slice(next.length - MAX_VISIBLE_TOASTS)
          : next;
      });

      setTimeout(() => dismiss(id), TOAST_DURATION_MS);
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      <div
        role="region"
        aria-label="Notifications"
        aria-live="polite"
        className="fixed top-4 right-4 left-4 sm:left-auto sm:w-80 flex flex-col gap-2 z-50"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-start gap-3 px-4 py-3 rounded-lg shadow-md text-sm font-medium ${STYLES[t.type]}`}
          >
            <span className="shrink-0 font-bold w-4 text-center">
              {ICONS[t.type]}
            </span>
            <span className="flex-1">{t.message}</span>
            <button
              onClick={() => dismiss(t.id)}
              aria-label="Dismiss notification"
              className="shrink-0 opacity-40 hover:opacity-80 leading-none ml-1"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}
