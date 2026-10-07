import {
  Activity,
  AlarmClock,
  Bell,
  BookOpen,
  Boxes,
  Braces,
  ChartLine,
  CircuitBoard,
  Clock,
  Code,
  Cpu,
  Database,
  Download,
  Fan,
  FileText,
  Filter,
  Flame,
  Gauge,
  Globe,
  Heart,
  KeyRound,
  Layers,
  LayoutDashboard,
  Lock,
  Mail,
  MonitorSmartphone,
  Network,
  Package,
  Play,
  Plug,
  Printer,
  RefreshCw,
  Rocket,
  ScrollText,
  Search,
  Send,
  Server,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Tags,
  Terminal,
  Thermometer,
  Timer,
  Usb,
  Users,
  Webhook,
  Workflow,
  Wrench,
  Zap,
} from 'lucide-react';
import type { ComponentType } from 'react';

export function GitHubIcon({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="currentColor" aria-hidden="true" className={className}>
      <path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.93.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2z" />
    </svg>
  );
}

export function LinkedInIcon({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="currentColor" aria-hidden="true" className={className}>
      <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.34V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z" />
    </svg>
  );
}

export function WhatsAppIcon({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="currentColor" aria-hidden="true" className={className}>
      <path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.65.07-.3-.15-1.26-.46-2.4-1.48-.89-.79-1.49-1.77-1.66-2.07-.17-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.03-.52-.07-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48 0 1.46 1.07 2.88 1.21 3.07.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.69.62.71.23 1.36.2 1.87.12.57-.08 1.76-.72 2.01-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35zM12.05 21.5h-.01a9.43 9.43 0 0 1-4.8-1.31l-.35-.21-3.57.94.95-3.48-.23-.36a9.4 9.4 0 0 1-1.44-5.02c0-5.2 4.24-9.44 9.46-9.44a9.4 9.4 0 0 1 6.68 2.77 9.38 9.38 0 0 1 2.77 6.68c0 5.21-4.24 9.44-9.46 9.44zm8.05-17.5A11.3 11.3 0 0 0 12.05.67C5.78.67.67 5.77.67 12.05c0 2 .52 3.96 1.52 5.69L.57 23.67l6.06-1.59a11.36 11.36 0 0 0 5.42 1.38h.01c6.27 0 11.38-5.1 11.38-11.38 0-3.04-1.18-5.9-3.34-8.05z" />
    </svg>
  );
}

/** Iconos disponibles para el contenido (campo "icon" en landing.json). */
const icons: Record<string, ComponentType<{ size?: number; className?: string }>> = {
  activity: Activity,
  alarm: AlarmClock,
  bell: Bell,
  book: BookOpen,
  boxes: Boxes,
  braces: Braces,
  chart: ChartLine,
  circuit: CircuitBoard,
  clock: Clock,
  code: Code,
  cpu: Cpu,
  database: Database,
  download: Download,
  fan: Fan,
  file: FileText,
  filter: Filter,
  flame: Flame,
  gauge: Gauge,
  github: GitHubIcon,
  globe: Globe,
  heart: Heart,
  key: KeyRound,
  layers: Layers,
  linkedin: LinkedInIcon,
  dashboard: LayoutDashboard,
  lock: Lock,
  mail: Mail,
  devices: MonitorSmartphone,
  network: Network,
  package: Package,
  play: Play,
  plug: Plug,
  printer: Printer,
  refresh: RefreshCw,
  rocket: Rocket,
  logs: ScrollText,
  search: Search,
  send: Send,
  server: Server,
  settings: Settings,
  shield: ShieldCheck,
  sliders: SlidersHorizontal,
  sparkles: Sparkles,
  tags: Tags,
  terminal: Terminal,
  thermometer: Thermometer,
  timer: Timer,
  usb: Usb,
  users: Users,
  webhook: Webhook,
  whatsapp: WhatsAppIcon,
  workflow: Workflow,
  wrench: Wrench,
  zap: Zap,
};

export function Icon({ name, size = 20, className }: { name?: string; size?: number; className?: string }) {
  const Component = (name && icons[name]) || Sparkles;
  return <Component size={size} className={className} aria-hidden="true" />;
}
