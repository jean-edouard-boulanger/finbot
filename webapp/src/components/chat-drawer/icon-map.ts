// Maps server-emitted icon hint strings (from agent tool specs) to lucide-react components.

import {
  BarChart3,
  Calendar,
  CreditCard,
  HelpCircle,
  LayoutGrid,
  type LucideIcon,
  MessageSquare,
  PiggyBank,
  RefreshCw,
  Search,
  Sparkles,
  Table2,
  TrendingUp,
  Wallet,
  Wrench,
} from "lucide-react";

const ICON_MAP: Record<string, LucideIcon> = {
  wallet: Wallet,
  trending: TrendingUp,
  "credit-card": CreditCard,
  search: Search,
  refresh: RefreshCw,
  piggy: PiggyBank,
  calendar: Calendar,
  sparkles: Sparkles,
  kv: LayoutGrid,
  table: Table2,
  chart: BarChart3,
  callout: MessageSquare,
  clarification: HelpCircle,
};

export function iconFromName(name: string): LucideIcon {
  return ICON_MAP[name] ?? Wrench;
}
