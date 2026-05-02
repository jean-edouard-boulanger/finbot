import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  TrendingUp,
  PieChart,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

import { FinbotMark } from "components";
import { Button } from "components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "components/ui/card";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "components/ui/sheet";
import { LinkAccount } from "routes/settings/link-account";

export interface WelcomeProps {}

interface ValuePropProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}

const ValueProp: React.FC<ValuePropProps> = ({
  icon: Icon,
  title,
  description,
}) => (
  <Card>
    <CardHeader className="pb-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </div>
      <CardTitle className="text-base mt-3">{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
  </Card>
);

export const Welcome: React.FC<WelcomeProps> = () => {
  const navigate = useNavigate();
  const [sheetOpen, setSheetOpen] = useState(false);

  const handleLinked = () => {
    setSheetOpen(false);
    navigate("/dashboard");
  };

  return (
    <div className="container mx-auto max-w-3xl px-6 pb-24 pt-10">
      <div className="flex flex-col items-center text-center">
        <div className="flex items-center gap-3 text-primary">
          <FinbotMark className="h-14 w-14" />
          <span className="text-4xl font-semibold tracking-tight text-foreground">
            finbot
          </span>
        </div>
        <h1 className="mt-8 text-3xl font-semibold tracking-tight">
          Welcome — let&apos;s set up your dashboard.
        </h1>
        <p className="mt-3 max-w-xl text-muted-foreground">
          Link your first account and finbot will start tracking your net worth,
          spending, and subscriptions automatically.
        </p>
        <Button size="lg" className="mt-8" onClick={() => setSheetOpen(true)}>
          Link your first account
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
        <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" />
          Read-only access. Credentials are encrypted. First sync usually takes
          a minute or two.
        </p>
      </div>

      <div className="mt-12 grid gap-4 sm:grid-cols-3">
        <ValueProp
          icon={TrendingUp}
          title="Net worth & history"
          description="See your total wealth across every linked account, tracked over time."
        />
        <ValueProp
          icon={PieChart}
          title="Spending & subscriptions"
          description="Automatic categorisation surfaces where money is going and what's recurring."
        />
        <ValueProp
          icon={Sparkles}
          title="Ask Finbot anything"
          description="Chat with your data — net worth, holdings, savings rate, all in plain English."
        />
      </div>

      <div className="mt-10 text-center text-sm text-muted-foreground">
        Prefer the full settings view?{" "}
        <Link
          to="/settings/linked"
          className="text-primary underline underline-offset-4 hover:text-primary/80"
        >
          Manage all linked accounts
        </Link>
        .
      </div>

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="right" className="sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Link your first account</SheetTitle>
            <SheetDescription>
              Connect a financial data provider to start tracking your
              portfolio.
            </SheetDescription>
          </SheetHeader>
          <div className="mt-6">
            <LinkAccount onSuccess={handleLinked} />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
};
