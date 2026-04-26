// Mirror of finbot/apps/appwsrv/agent/schema.py rich-block discriminated union — keep in sync.

export interface ChartSeries {
  name: string;
  data: (number | null)[];
}

export interface ClarificationOption {
  label: string;
  send_text: string;
}

export type RichBlock =
  | {
      kind: "kv";
      title: string;
      rows: { label: string; value: string; tone?: "up" | "down" | "neutral" }[];
    }
  | {
      kind: "table";
      title: string;
      headers: string[];
      rows: string[][];
      footer?: string;
    }
  | {
      kind: "callout";
      tone: "success" | "warning";
      title: string;
      body: string;
    }
  | {
      kind: "chart";
      chart_type: "line" | "area" | "bar";
      title: string;
      x_axis_labels: string[];
      series: ChartSeries[];
      y_unit?: string | null;
      footer?: string | null;
    }
  | {
      kind: "clarification";
      title: string;
      options: ClarificationOption[];
    };
